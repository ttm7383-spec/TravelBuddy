"""
TravelBuddy Recommendation Engine
==================================
This module implements a two-layer recommendation system for travel destinations:

Layer 1 - Rule-Based Filtering:
    Filters the destination pool based on hard constraints like budget level
    and group type. This ensures we only recommend destinations that are
    practically feasible for the user.

Layer 2 - Content-Based Scoring (TF-IDF + Cosine Similarity):
    Uses Natural Language Processing (NLP) techniques to match the user's
    style preferences (e.g., "beach", "adventure") against each destination's
    characteristics. This produces a relevance score for ranking.

Scoring Pipeline:
    1. Apply rule-based filter (pass/fail)
    2. Compute TF-IDF cosine similarity for passing destinations
    3. Penalise previously visited destinations
    4. Return top-N results with human-readable explanations

Dependencies:
    - scikit-learn: for TF-IDF vectorisation and cosine similarity
    - json: for loading the destination database
"""

import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# STEP 0: Load the visa requirements database
# ---------------------------------------------------------------------------
# This is used in Layer 3 (visa accessibility scoring) to adjust scores
# based on how easy it is for the user's passport to enter each destination.
# ---------------------------------------------------------------------------

_VISA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "visa_requirements.json")

try:
    with open(_VISA_PATH, "r", encoding="utf-8") as f:
        VISA_DATA = json.load(f)
except FileNotFoundError:
    VISA_DATA = {}


# ---------------------------------------------------------------------------
# STEP 1: Load the destination database from the JSON file
# ---------------------------------------------------------------------------
# We load the destinations once when the module is imported, so we don't
# re-read the file on every API request. This is efficient for a small
# dataset (30 destinations) and avoids unnecessary I/O.
# ---------------------------------------------------------------------------

# Build the path to destinations.json relative to this file's location
_DESTINATIONS_PATH = os.path.join(os.path.dirname(__file__), "destinations.json")

with open(_DESTINATIONS_PATH, "r", encoding="utf-8") as f:
    DESTINATIONS = json.load(f)


# ---------------------------------------------------------------------------
# STEP 2: Define budget level boundaries
# ---------------------------------------------------------------------------
# These thresholds map the user's budget preference (low / medium / high)
# to actual GBP-per-day ranges. They are used in the rule-based filter
# to eliminate destinations that fall outside the user's budget.
#
#   low    → under £80 per day   (budget travellers, hostels, street food)
#   medium → £80 to £200 per day (mid-range hotels, restaurants)
#   high   → over £200 per day   (luxury resorts, fine dining)
# ---------------------------------------------------------------------------

BUDGET_RANGES = {
    "low":    (0, 80),      # Budget-friendly destinations
    "medium": (80, 200),    # Mid-range destinations
    "high":   (200, 10000), # Luxury destinations (upper bound is effectively unlimited)
}


# ---------------------------------------------------------------------------
# STEP 3: Rule-Based Filter (Layer 1)
# ---------------------------------------------------------------------------
# Purpose: Narrow down the destination pool to only those that match the
#          user's hard constraints. A destination must pass ALL rules to
#          be considered for content-based scoring.
#
# Rules applied:
#   1. Budget compatibility: destination's avg_daily_cost_gbp must fall
#      within the range defined by the user's budget_level.
#   2. Group type compatibility: the user's group_type must appear in the
#      destination's suitable_for list.
#
# Returns: A list of destination dicts that pass all rules.
# ---------------------------------------------------------------------------

def rule_based_filter(destinations, budget_level, group_type):
    """
    Filter destinations by budget level and group type.

    Parameters
    ----------
    destinations : list[dict]
        The full list of destination objects from destinations.json.
    budget_level : str
        One of "low", "medium", or "high".
    group_type : str
        One of "solo", "couple", "family", or "friends".

    Returns
    -------
    list[dict]
        Destinations that satisfy both the budget and group type constraints.
    """
    # Look up the min and max daily cost for the given budget level
    # Default to the full range (0, 10000) if an unrecognised level is provided
    budget_min, budget_max = BUDGET_RANGES.get(budget_level, (0, 10000))

    filtered = []
    for dest in destinations:
        # --- Rule 1: Budget check ---
        # The destination's average daily cost must fall within the user's
        # budget range (inclusive on both ends)
        cost = dest["avg_daily_cost_gbp"]
        if cost < budget_min or cost > budget_max:
            continue  # Skip — too cheap or too expensive for this budget level

        # --- Rule 2: Group type check ---
        # The destination must explicitly list this group type as suitable
        if group_type and group_type not in dest.get("suitable_for", []):
            continue  # Skip — not suitable for this travel group

        # Destination passed all rules — include it
        filtered.append(dest)

    return filtered


# ---------------------------------------------------------------------------
# STEP 4: Build text representation for each destination
# ---------------------------------------------------------------------------
# For content-based filtering, we need to represent each destination as a
# text string so we can apply TF-IDF vectorisation. We combine:
#   - The destination's tags (e.g., "beach", "culture", "nightlife")
#   - The destination's sample_activities (e.g., "Visit Grand Palace")
#   - The destination's climate (e.g., "tropical")
#
# This gives us a rich text representation that captures what a destination
# offers. For example, Bangkok becomes:
#   "culture street-food temples nightlife shopping budget-friendly
#    Visit Grand Palace Street food tour in Chinatown ... tropical"
# ---------------------------------------------------------------------------

def build_destination_text(destination):
    """
    Convert a destination's features into a single text string for TF-IDF.

    We concatenate tags, sample activities, and climate into one string.
    This creates a "document" that represents the destination's character,
    which TF-IDF can then vectorise for similarity comparison.

    Parameters
    ----------
    destination : dict
        A single destination object from the database.

    Returns
    -------
    str
        A space-separated string of the destination's features.
    """
    # Combine all feature lists into one text blob
    tags = " ".join(destination.get("tags", []))
    activities = " ".join(destination.get("sample_activities", []))
    climate = destination.get("climate", "")

    return f"{tags} {activities} {climate}"


# ---------------------------------------------------------------------------
# STEP 5: Content-Based Scoring using TF-IDF + Cosine Similarity (Layer 2)
# ---------------------------------------------------------------------------
# How this works:
#
# 1. TF-IDF Vectorisation:
#    TF-IDF (Term Frequency - Inverse Document Frequency) converts text into
#    numerical vectors. Each word gets a weight based on:
#      - TF: How often the word appears in this document (destination)
#      - IDF: How rare the word is across ALL documents (destinations)
#    Words that are unique to a destination get higher weights, making them
#    more distinctive. For example, "skiing" would be highly weighted for
#    Interlaken because few other destinations mention it.
#
# 2. Query Vector:
#    The user's style preferences (e.g., ["beach", "adventure"]) are treated
#    as a "query document". We transform this into the same TF-IDF space
#    so we can compare it directly against destination vectors.
#
# 3. Cosine Similarity:
#    Measures the angle between the user's preference vector and each
#    destination vector. A score of 1.0 means perfect alignment; 0.0 means
#    no overlap at all. This is ideal for text comparison because it
#    normalises for document length — a destination with more activities
#    won't automatically score higher.
#
# Returns: A list of (destination_index, similarity_score) tuples.
# ---------------------------------------------------------------------------

def compute_content_scores(destinations, style_preferences):
    """
    Score destinations against user preferences using TF-IDF + cosine similarity.

    Parameters
    ----------
    destinations : list[dict]
        The filtered list of destinations (output from rule_based_filter).
    style_preferences : list[str]
        User's preferred travel styles, e.g., ["beach", "adventure", "culture"].

    Returns
    -------
    list[tuple(int, float)]
        List of (index, similarity_score) for each destination, where index
        corresponds to the position in the input destinations list.
    """
    if not destinations:
        return []

    if not style_preferences:
        # If the user has no preferences, give all destinations an equal score
        # This avoids division-by-zero issues in TF-IDF
        return [(i, 0.5) for i in range(len(destinations))]

    # --- Step 5a: Build the corpus ---
    # Each destination becomes one "document" in our corpus
    corpus = [build_destination_text(dest) for dest in destinations]

    # The user's preferences become the query document
    # We join them into a single string, e.g., "beach adventure culture"
    user_query = " ".join(style_preferences)

    # Append the user query as the last document in the corpus
    # so it gets vectorised in the same TF-IDF space
    corpus.append(user_query)

    # --- Step 5b: TF-IDF Vectorisation ---
    # Create the TF-IDF vectoriser. Key parameters:
    #   - stop_words='english': removes common English words like "the", "and"
    #     which don't carry meaningful information for similarity
    #   - lowercase=True (default): normalises case so "Beach" == "beach"
    vectoriser = TfidfVectorizer(stop_words="english")

    # Fit the vectoriser on the entire corpus (destinations + query) and
    # transform all documents into TF-IDF vectors
    # Result shape: (num_destinations + 1, num_unique_terms)
    tfidf_matrix = vectoriser.fit_transform(corpus)

    # --- Step 5c: Cosine Similarity ---
    # Compare the user query vector (last row) against all destination vectors
    # tfidf_matrix[-1] is the user query; tfidf_matrix[:-1] are destinations
    # Result shape: (1, num_destinations)
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    # Convert to a flat array for easier processing
    scores = similarity_scores.flatten()

    # Return (index, score) pairs
    return [(i, float(scores[i])) for i in range(len(destinations))]


# ---------------------------------------------------------------------------
# STEP 6: Travel History Penalty
# ---------------------------------------------------------------------------
# If the user has visited a destination before, we don't want to recommend
# it as strongly — they likely want to explore somewhere new. We apply a
# penalty factor (0.3 = 30% reduction) to the score of visited destinations.
#
# We don't remove them entirely because some users might enjoy revisiting
# favourite spots, and a heavily penalised destination could still rank
# if it's an exceptionally good match.
# ---------------------------------------------------------------------------

HISTORY_PENALTY = 0.3  # 30% penalty for previously visited destinations


def apply_history_penalty(scored_destinations, travel_history):
    """
    Reduce scores for destinations the user has already visited.

    Parameters
    ----------
    scored_destinations : list[tuple(dict, float)]
        List of (destination, score) tuples.
    travel_history : list[str]
        List of destination IDs the user has previously visited.

    Returns
    -------
    list[tuple(dict, float)]
        Same list with adjusted scores.
    """
    if not travel_history:
        return scored_destinations  # No history — no penalties to apply

    adjusted = []
    for dest, score in scored_destinations:
        if dest["id"] in travel_history:
            # Apply penalty: multiply score by (1 - HISTORY_PENALTY)
            # e.g., score 0.8 becomes 0.8 * 0.7 = 0.56
            adjusted_score = score * (1 - HISTORY_PENALTY)
            adjusted.append((dest, adjusted_score))
        else:
            adjusted.append((dest, score))

    return adjusted


# ---------------------------------------------------------------------------
# STEP 6b: Visa Accessibility Scoring (Layer 3)
# ---------------------------------------------------------------------------
# Different passport holders have vastly different travel freedom. A UK
# passport holder can visit most countries visa-free, while an Indian or
# Pakistani passport holder needs visas for many destinations.
#
# We adjust recommendation scores based on visa ease:
#   - visa-free:          score × 1.0   (no penalty — easiest to visit)
#   - visa-on-arrival:    score × 0.95  (minor friction, pay at airport)
#   - e-visa:             score × 0.95  (easy online application)
#   - visa-required <£50: score × 0.85  (needs embassy visit, affordable)
#   - visa-required >£50: score × 0.70  (expensive + bureaucratic)
#   - not-admitted:        removed entirely from results
#
# This ensures recommendations are practical — we don't recommend Paris
# to someone who'd need a £65 Schengen visa and 15 days processing unless
# it's truly a great match.
# ---------------------------------------------------------------------------

VISA_SCORE_MULTIPLIERS = {
    "visa-free":       1.0,   # No penalty
    "visa-on-arrival": 0.95,  # Tiny penalty for minor friction
    "e-visa":          0.95,  # Easy online process
    "visa-required":   0.85,  # Default for paid visas
    "not-admitted":    0.0,   # Remove from results
}


def apply_visa_scoring(scored_destinations, passport_country):
    """
    Adjust scores based on visa accessibility for the user's passport.

    Parameters
    ----------
    scored_destinations : list[tuple(dict, float)]
        List of (destination, score) tuples.
    passport_country : str
        ISO country code of the user's passport (e.g., "GB", "IN", "PK").

    Returns
    -------
    list[tuple(dict, float)]
        Adjusted list with visa penalties applied. Destinations marked
        'not-admitted' are removed entirely.
    """
    if not passport_country or passport_country not in VISA_DATA:
        # No passport data available — return unchanged
        return scored_destinations

    passport_data = VISA_DATA[passport_country]
    adjusted = []

    for dest, score in scored_destinations:
        country = dest.get("country", "")
        visa_info = passport_data.get(country, {})
        requirement = visa_info.get("requirement", "visa-required")
        cost = visa_info.get("cost_gbp", 0)

        # Skip destinations where entry is not permitted
        if requirement == "not-admitted":
            continue

        # Get base multiplier for the requirement type
        multiplier = VISA_SCORE_MULTIPLIERS.get(requirement, 0.85)

        # For expensive visas (>£50), apply a stronger penalty
        if requirement == "visa-required" and cost > 50:
            multiplier = 0.70

        adjusted_score = score * multiplier
        adjusted.append((dest, adjusted_score))

    return adjusted


def get_visa_info_for_destination(destination, passport_country):
    """
    Get visa info for a single destination, used to attach to recommendation results.

    Returns a dict with requirement, cost, processing_days, notes.
    """
    if not passport_country or passport_country not in VISA_DATA:
        return None

    country = destination.get("country", "")
    return VISA_DATA[passport_country].get(country)


# ---------------------------------------------------------------------------
# STEP 7: Generate Human-Readable Match Reasons
# ---------------------------------------------------------------------------
# For the frontend UI, we need to explain WHY a destination was recommended.
# This function builds a friendly sentence based on which of the user's
# preferences matched the destination's tags.
# ---------------------------------------------------------------------------

def generate_match_reason(destination, style_preferences, budget_level):
    """
    Create a human-readable explanation for why this destination was recommended.

    Parameters
    ----------
    destination : dict
        The recommended destination object.
    style_preferences : list[str]
        User's style preferences.
    budget_level : str
        User's budget level.

    Returns
    -------
    str
        A sentence explaining the match, e.g.,
        "Matches your beach and culture interests within your budget"
    """
    # Find which user preferences overlap with destination tags
    dest_tags = set(destination.get("tags", []))
    dest_activities_text = " ".join(destination.get("sample_activities", [])).lower()

    matching_interests = []
    for pref in style_preferences:
        pref_lower = pref.lower()
        # Check if the preference matches a tag or appears in activities text
        if pref_lower in dest_tags or pref_lower in dest_activities_text:
            matching_interests.append(pref_lower)

    # Build the reason string
    budget_labels = {"low": "budget-friendly", "medium": "mid-range", "high": "luxury"}
    budget_label = budget_labels.get(budget_level, "")

    if matching_interests:
        # Join matched interests with "and" for the last one
        if len(matching_interests) == 1:
            interests_text = matching_interests[0]
        else:
            interests_text = ", ".join(matching_interests[:-1]) + " and " + matching_interests[-1]

        reason = f"Matches your {interests_text} interests"
    else:
        reason = "Great match based on overall destination character"

    # Append budget context
    if budget_label:
        reason += f" within your {budget_label} budget"

    return reason


# ---------------------------------------------------------------------------
# STEP 8: Main Recommendation Function (Full Pipeline)
# ---------------------------------------------------------------------------
# This is the entry point called by the Flask API route. It orchestrates
# the entire recommendation pipeline:
#
#   1. Rule-based filter → eliminates unsuitable destinations
#   2. Content-based scoring → ranks remaining destinations by preference match
#   3. History penalty → de-prioritises previously visited destinations
#   4. Sort and return top N results with match reasons
# ---------------------------------------------------------------------------

def get_recommendations(
    budget_level,
    style_preferences,
    group_type,
    travel_history=None,
    passport_country=None,
    top_n=5
):
    """
    Main recommendation function — orchestrates the full scoring pipeline.

    Parameters
    ----------
    budget_level : str
        One of "low", "medium", or "high".
    style_preferences : list[str]
        List of travel style keywords, e.g., ["beach", "culture", "nightlife"].
    group_type : str
        One of "solo", "couple", "family", or "friends".
    travel_history : list[str], optional
        List of destination IDs the user has previously visited.
    top_n : int, optional
        Number of recommendations to return (default: 5).

    Returns
    -------
    list[dict]
        Top N recommendations, each containing:
        - All destination fields (id, name, country, etc.)
        - match_score: float between 0 and 1
        - match_reason: human-readable explanation string

    Example
    -------
    >>> results = get_recommendations(
    ...     budget_level="low",
    ...     style_preferences=["beach", "culture"],
    ...     group_type="solo"
    ... )
    >>> results[0]["name"]
    'Bali'
    >>> results[0]["match_score"]
    0.72
    """
    if travel_history is None:
        travel_history = []

    # --- Pipeline Step 1: Rule-based filtering ---
    # Remove destinations that don't match budget and group type
    filtered = rule_based_filter(DESTINATIONS, budget_level, group_type)

    if not filtered:
        # No destinations match the hard constraints
        # Return empty list — the API route will handle this gracefully
        return []

    # --- Pipeline Step 2: Content-based scoring ---
    # Score each filtered destination against user's style preferences
    # using TF-IDF vectorisation and cosine similarity
    indexed_scores = compute_content_scores(filtered, style_preferences)

    # Pair each destination with its similarity score
    scored = [(filtered[i], score) for i, score in indexed_scores]

    # --- Pipeline Step 3: Apply travel history penalty ---
    # Reduce scores for destinations the user has already visited
    scored = apply_history_penalty(scored, travel_history)

    # --- Pipeline Step 3b: Apply visa accessibility scoring ---
    # Adjust scores based on how easy each destination is to enter
    # with the user's passport. Removes 'not-admitted' destinations.
    if passport_country:
        scored = apply_visa_scoring(scored, passport_country)

    # --- Pipeline Step 4: Sort by score (descending) and take top N ---
    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = scored[:top_n]

    # --- Pipeline Step 5: Build the response objects ---
    recommendations = []
    for dest, score in top_results:
        # Create a copy of the destination dict so we don't mutate the original
        result = dict(dest)

        # Add the match score (rounded to 2 decimal places for readability)
        result["match_score"] = round(score, 2)

        # Generate a human-readable explanation for the match
        result["match_reason"] = generate_match_reason(
            dest, style_preferences, budget_level
        )

        # Attach visa information if passport is provided
        if passport_country:
            visa = get_visa_info_for_destination(dest, passport_country)
            if visa:
                result["visa_info"] = visa

        recommendations.append(result)

    return recommendations
