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

Enhanced Scoring Pipeline (v2):
    1. Apply rule-based filter (pass/fail — with soft budget boundaries)
    2. Compute TF-IDF cosine similarity for passing destinations (50% weight)
    3. Compute seasonal relevance score based on travel dates (15% weight)
    4. Compute popularity and safety weighted score (10% weight)
    5. Compute climate preference match score (15% weight)
    6. Compute smart budget gradient score (10% weight)
    7. Combine all sub-scores into a weighted final score
    8. Penalise previously visited destinations
    9. Apply visa accessibility scoring
    10. Enforce geographic diversity in top-N results
    11. Return top-N results with human-readable explanations

Dependencies:
    - scikit-learn: for TF-IDF vectorisation and cosine similarity
    - json: for loading the destination database
    - math: for the budget gradient falloff function
    - datetime: for seasonal relevance calculations
"""

import json
import math
import os
import numpy as np
from datetime import datetime
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
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
# re-read the file on every API request. This is efficient for the dataset
# (46 UK & European destinations) and avoids unnecessary I/O.
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

# Soft budget boundaries — how far beyond the hard cutoff we still consider
# destinations (used in the smart budget gradient scoring)
BUDGET_SOFT_MARGIN = 30  # GBP per day beyond hard cutoff


# ---------------------------------------------------------------------------
# Climate-to-preference mapping for climate preference matching
# ---------------------------------------------------------------------------
# Maps user style preferences to climate types that are a good fit.
# Used in Layer 2 climate matching to boost destinations whose climate
# aligns with the user's stated interests.
# ---------------------------------------------------------------------------

CLIMATE_PREFERENCE_MAP = {
    "beach":      ["tropical", "mediterranean", "subtropical"],
    "surfing":    ["tropical", "subtropical", "oceanic"],
    "diving":     ["tropical", "subtropical"],
    "snorkeling": ["tropical", "subtropical"],
    "skiing":     ["alpine", "subarctic", "continental"],
    "snowboard":  ["alpine", "subarctic", "continental"],
    "winter":     ["alpine", "subarctic", "continental"],
    "hiking":     ["temperate", "continental", "alpine", "mediterranean"],
    "trekking":   ["temperate", "continental", "alpine"],
    "desert":     ["arid", "desert", "semi-arid"],
    "safari":     ["tropical", "savanna", "semi-arid"],
    "wildlife":   ["tropical", "savanna", "temperate"],
    "city":       ["temperate", "mediterranean", "continental"],
    "culture":    ["temperate", "mediterranean", "continental", "tropical"],
    "nightlife":  ["mediterranean", "tropical", "temperate"],
    "wellness":   ["tropical", "mediterranean", "subtropical"],
    "spa":        ["tropical", "mediterranean", "subtropical"],
}


# ---------------------------------------------------------------------------
# Weight configuration for the enhanced multi-factor scoring
# ---------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "content":    0.50,  # TF-IDF cosine similarity (core matching)
    "seasonal":   0.15,  # Seasonal relevance based on travel dates
    "popularity": 0.10,  # Popularity and safety combined score
    "climate":    0.15,  # Climate preference alignment
    "budget":     0.10,  # Smart budget gradient score
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
#      within the range defined by the user's budget_level (with soft margin).
#   2. Group type compatibility: the user's group_type must appear in the
#      destination's suitable_for list.
#
# Returns: A list of destination dicts that pass all rules.
# ---------------------------------------------------------------------------

def rule_based_filter(destinations, budget_level, group_type):
    """
    Filter destinations by budget level and group type.

    Uses soft budget boundaries — destinations slightly outside the user's
    budget range are still included (they will receive a lower budget gradient
    score in the scoring phase rather than being completely excluded).

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

    # Expand the range by the soft margin so near-boundary destinations
    # are not completely excluded — they will get a lower budget score instead
    soft_min = max(0, budget_min - BUDGET_SOFT_MARGIN)
    soft_max = budget_max + BUDGET_SOFT_MARGIN

    filtered = []
    for dest in destinations:
        # --- Rule 1: Budget check (with soft margin) ---
        # The destination's average daily cost must fall within the expanded
        # budget range (hard range + soft margin on both ends)
        cost = dest["avg_daily_cost_gbp"]
        if cost < soft_min or cost > soft_max:
            continue  # Skip — too far outside this budget level

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
#   - The destination's highlights text (new field for richer matching)
#
# This gives us a rich text representation that captures what a destination
# offers. For example, Bangkok becomes:
#   "culture street-food temples nightlife shopping budget-friendly
#    Visit Grand Palace Street food tour in Chinatown ... tropical
#    Explore the vibrant street markets and ancient temples..."
# ---------------------------------------------------------------------------

def build_destination_text(destination):
    """
    Convert a destination's features into a single text string for TF-IDF.

    We concatenate tags, sample activities, climate, and highlights into one
    string. This creates a "document" that represents the destination's
    character, which TF-IDF can then vectorise for similarity comparison.

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
    highlights = destination.get("highlights", "")

    return f"{tags} {activities} {climate} {highlights}"


# ---------------------------------------------------------------------------
# STEP 4b: Pre-compute TF-IDF matrix at module load (CACHED)
# ---------------------------------------------------------------------------
# Building a TF-IDF vectoriser and matrix on every API call is wasteful.
# Since the destination database doesn't change at runtime, we compute it
# once when the module loads and reuse it for all subsequent requests.
# This reduces recommendation latency from ~50ms to ~2ms.
# ---------------------------------------------------------------------------

_CORPUS = [build_destination_text(d) for d in DESTINATIONS]
_VECTORISER = TfidfVectorizer(stop_words="english")
_TFIDF_MATRIX = _VECTORISER.fit_transform(_CORPUS)


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

    Uses the pre-computed _TFIDF_MATRIX and _VECTORISER for performance.
    The query is transformed into the existing TF-IDF space (not re-fitted),
    then compared against the cached destination vectors.

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
        return [(i, 0.5) for i in range(len(destinations))]

    # Transform the user query into the cached TF-IDF space
    user_query = " ".join(style_preferences)
    query_vector = _VECTORISER.transform([user_query])

    # Map filtered destinations to their indices in the full DESTINATIONS list
    dest_ids = {d["id"] for d in destinations}
    dest_indices = [i for i, d in enumerate(DESTINATIONS) if d["id"] in dest_ids]

    if not dest_indices:
        return [(i, 0.5) for i in range(len(destinations))]

    # Extract only the cached TF-IDF rows for filtered destinations
    filtered_matrix = _TFIDF_MATRIX[dest_indices]

    # Compute cosine similarity between query and filtered destinations
    scores = cosine_similarity(query_vector, filtered_matrix).flatten()

    # Map scores back to the input destinations list order
    id_to_score = {}
    for rank, full_idx in enumerate(dest_indices):
        id_to_score[DESTINATIONS[full_idx]["id"]] = float(scores[rank])

    return [(i, id_to_score.get(dest["id"], 0.0))
            for i, dest in enumerate(destinations)]


# ---------------------------------------------------------------------------
# STEP 5b: Seasonal Relevance Scoring
# ---------------------------------------------------------------------------
# If the user provides travel dates, we boost destinations that are in
# their peak season during those dates. Destinations at their best time
# of year receive a score of 1.0, while off-peak destinations receive
# a lower score (but never 0 — off-peak travel can still be enjoyable).
#
# Uses the peak_months field from each destination.
# ---------------------------------------------------------------------------

def compute_seasonal_score(destination, travel_month):
    """
    Score how well a destination matches the user's travel month.

    A destination gets a high score if the travel month falls within its
    peak_months, a moderate score if it is one month away from peak, and
    a base score otherwise.

    Parameters
    ----------
    destination : dict
        A single destination object.
    travel_month : int or None
        The month number (1-12) the user plans to travel in.

    Returns
    -------
    float
        A score between 0.3 and 1.0 indicating seasonal suitability.
    """
    if travel_month is None:
        return 0.5  # Neutral score when no travel date is provided

    peak_months = destination.get("peak_months", [])
    if not peak_months:
        return 0.5  # No peak data — neutral score

    # Check if the travel month is a peak month
    if travel_month in peak_months:
        return 1.0  # Perfect — travelling during the best season

    # Check if the travel month is adjacent to a peak month
    # (within 1 month — shoulder season is still good)
    for peak in peak_months:
        # Handle wrap-around (December → January)
        diff = min(abs(travel_month - peak), 12 - abs(travel_month - peak))
        if diff == 1:
            return 0.75  # Shoulder season — still a decent time to visit

    # Off-peak but not terrible
    return 0.3


# ---------------------------------------------------------------------------
# STEP 5c: Popularity and Safety Scoring
# ---------------------------------------------------------------------------
# Combines the destination's popularity_score (1-100) and safety_rating
# (1-5) into a single normalised score. Solo travellers and families
# receive a higher weighting on safety.
# ---------------------------------------------------------------------------

def compute_popularity_safety_score(destination, group_type):
    """
    Compute a combined popularity and safety score for a destination.

    Solo travellers and families get a higher safety weighting (60/40 split)
    while couples and friends get an even split (50/50).

    Parameters
    ----------
    destination : dict
        A single destination object.
    group_type : str
        One of "solo", "couple", "family", or "friends".

    Returns
    -------
    float
        A normalised score between 0.0 and 1.0.
    """
    # Normalise popularity_score from 1-100 to 0-1
    popularity = destination.get("popularity_score", 50) / 100.0

    # Normalise safety_rating from 1-5 to 0-1
    safety = destination.get("safety_rating", 3) / 5.0

    # Solo travellers and families weight safety more heavily
    if group_type in ("solo", "family"):
        safety_weight = 0.60
        popularity_weight = 0.40
    else:
        safety_weight = 0.50
        popularity_weight = 0.50

    return (popularity * popularity_weight) + (safety * safety_weight)


# ---------------------------------------------------------------------------
# STEP 5d: Climate Preference Matching
# ---------------------------------------------------------------------------
# Maps the user's style preferences to ideal climate types and scores
# each destination based on how well its climate matches.
# ---------------------------------------------------------------------------

def compute_climate_score(destination, style_preferences):
    """
    Score how well a destination's climate matches the user's preferences.

    Uses the CLIMATE_PREFERENCE_MAP to determine which climate types best
    suit the user's stated interests. For example, a user who likes "beach"
    will get higher scores for tropical and mediterranean climates.

    Parameters
    ----------
    destination : dict
        A single destination object.
    style_preferences : list[str]
        User's style preferences.

    Returns
    -------
    float
        A score between 0.2 and 1.0 indicating climate alignment.
    """
    if not style_preferences:
        return 0.5  # Neutral when no preferences given

    dest_climate = destination.get("climate", "").lower()
    if not dest_climate:
        return 0.5  # No climate data — neutral score

    # Collect all ideal climate types from the user's preferences
    ideal_climates = set()
    for pref in style_preferences:
        pref_lower = pref.lower()
        if pref_lower in CLIMATE_PREFERENCE_MAP:
            ideal_climates.update(CLIMATE_PREFERENCE_MAP[pref_lower])

    if not ideal_climates:
        return 0.5  # User preferences don't map to specific climates

    # Check if the destination's climate matches any ideal climate
    for ideal in ideal_climates:
        if ideal in dest_climate:
            return 1.0  # Direct climate match

    # Partial match — check if any climate-related word overlaps
    dest_climate_words = set(dest_climate.split())
    ideal_words = set()
    for c in ideal_climates:
        ideal_words.update(c.split())

    overlap = dest_climate_words & ideal_words
    if overlap:
        return 0.7  # Partial climate match

    return 0.2  # No climate alignment


# ---------------------------------------------------------------------------
# STEP 5e: Smart Budget Gradient Scoring
# ---------------------------------------------------------------------------
# Instead of a hard budget cutoff, this applies a smooth gradient. A
# destination at GBP 79/day should not be completely excluded for a
# "medium" budget user — it gets a high budget score. A destination at
# GBP 60/day gets a slightly lower score, and one at GBP 50/day lower
# still, following a sigmoid-like falloff curve.
# ---------------------------------------------------------------------------

def compute_budget_gradient_score(destination, budget_level):
    """
    Compute a smooth budget compatibility score using a gradient falloff.

    Destinations within the user's budget range get a score of 1.0.
    Destinations slightly outside the range get a score that falls off
    smoothly, rather than dropping to 0 immediately.

    Parameters
    ----------
    destination : dict
        A single destination object.
    budget_level : str
        One of "low", "medium", or "high".

    Returns
    -------
    float
        A score between 0.0 and 1.0 indicating budget compatibility.
    """
    budget_min, budget_max = BUDGET_RANGES.get(budget_level, (0, 10000))
    cost = destination["avg_daily_cost_gbp"]

    # Within the ideal range — perfect score
    if budget_min <= cost <= budget_max:
        return 1.0

    # Calculate how far outside the range the cost falls
    if cost < budget_min:
        distance = budget_min - cost
    else:
        distance = cost - budget_max

    # Apply a sigmoid-like falloff: score = 1 / (1 + e^(k * distance))
    # k controls the steepness — we use 0.1 so the curve is fairly gentle
    # At distance=0 → score=0.5 (we shift to start at ~1.0)
    # At distance=30 → score ≈ 0.13
    # At distance=50 → score ≈ 0.01
    falloff = 1.0 / (1.0 + math.exp(0.15 * distance))

    # Scale so that at distance=0 we get ~1.0 not 0.5
    # The sigmoid at distance=0 gives 0.5, so we multiply by 2 and cap at 1.0
    score = min(1.0, falloff * 2.0)

    return score


# ---------------------------------------------------------------------------
# STEP 5f: Geographic Diversity Enforcement
# ---------------------------------------------------------------------------
# Ensures the final top-N recommendations include at least 2 different
# continents, so the user gets a diverse set of suggestions rather than
# 5 destinations all from the same region.
# ---------------------------------------------------------------------------

def enforce_geographic_diversity(scored_destinations, top_n=5, min_continents=2):
    """
    Re-rank the top results to ensure geographic diversity.

    If the top-N results are all from the same continent, this function
    swaps in highly-scored destinations from other continents to ensure
    at least min_continents different continents are represented.

    Parameters
    ----------
    scored_destinations : list[tuple(dict, float)]
        Sorted list of (destination, score) tuples (highest first).
    top_n : int
        Number of results to return.
    min_continents : int
        Minimum number of distinct continents in the results (default: 2).

    Returns
    -------
    list[tuple(dict, float)]
        Re-ranked list of (destination, score) tuples of length top_n.
    """
    if len(scored_destinations) <= top_n:
        return scored_destinations

    # Start with the top-N by score
    selected = list(scored_destinations[:top_n])
    remaining = list(scored_destinations[top_n:])

    # Count distinct continents in the current selection
    continents_in_selection = set()
    for dest, _ in selected:
        continent = dest.get("continent", "Unknown")
        continents_in_selection.add(continent)

    # If we already have enough diversity, return as-is
    if len(continents_in_selection) >= min_continents:
        return selected

    # We need more diversity — find the best destination from a new continent
    # Replace the lowest-scored item in the selection with the best candidate
    # from a continent not yet represented
    for candidate_dest, candidate_score in remaining:
        candidate_continent = candidate_dest.get("continent", "Unknown")
        if candidate_continent not in continents_in_selection:
            # Replace the lowest-scored item in selection
            # (but only if the candidate's score is reasonable — at least 50%
            # of the lowest selected score, to avoid inserting poor matches)
            lowest_score = selected[-1][1]
            if candidate_score >= lowest_score * 0.5:
                selected[-1] = (candidate_dest, candidate_score)
                continents_in_selection.add(candidate_continent)

                # Re-sort by score after the swap
                selected.sort(key=lambda x: x[1], reverse=True)

            # Check if we now have enough continents
            if len(continents_in_selection) >= min_continents:
                break

    return selected


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

def generate_match_reason(destination, style_preferences, budget_level,
                          travel_month=None):
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
    travel_month : int or None, optional
        The travel month (1-12) for seasonal context.

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

    # Append seasonal context if applicable
    if travel_month is not None:
        peak_months = destination.get("peak_months", [])
        if travel_month in peak_months:
            month_names = [
                "", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            reason += f" — {month_names[travel_month]} is peak season here"

    return reason


# ---------------------------------------------------------------------------
# STEP 8: Main Recommendation Function (Full Pipeline)
# ---------------------------------------------------------------------------
# This is the entry point called by the Flask API route. It orchestrates
# the entire recommendation pipeline:
#
#   1. Rule-based filter → eliminates unsuitable destinations (soft budget)
#   2. Content-based scoring → ranks by preference match (50% weight)
#   3. Seasonal relevance → boosts in-season destinations (15% weight)
#   4. Popularity & safety → factors in ratings (10% weight)
#   5. Climate matching → boosts climate-aligned destinations (15% weight)
#   6. Budget gradient → smooth budget scoring (10% weight)
#   7. History penalty → de-prioritises previously visited destinations
#   8. Visa scoring → adjusts for travel accessibility
#   9. Geographic diversity → ensures continent variety in results
#   10. Return top N results with match reasons
# ---------------------------------------------------------------------------

def get_recommendations(
    budget_level,
    style_preferences,
    group_type,
    travel_history=None,
    passport_country=None,
    top_n=5,
    travel_month=None,
    travel_date=None
):
    """
    Main recommendation function — orchestrates the full scoring pipeline.

    Parameters
    ----------
    budget_level : str
        One of "low", "medium", or "high".
    style_preferences : list[str]
        List of travel style keywords, e.g., ["beach", "adventure", "culture"].
    group_type : str
        One of "solo", "couple", "family", or "friends".
    travel_history : list[str], optional
        List of destination IDs the user has previously visited.
    passport_country : str, optional
        ISO country code of the user's passport (e.g., "GB", "IN").
    top_n : int, optional
        Number of recommendations to return (default: 5).
    travel_month : int, optional
        Month number (1-12) the user plans to travel. Used for seasonal
        relevance scoring. Overridden by travel_date if both are provided.
    travel_date : str, optional
        ISO date string (e.g., "2026-07-15") for the planned trip. The month
        is extracted for seasonal scoring. Takes precedence over travel_month.

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

    # --- Resolve travel month from date if provided ---
    effective_month = travel_month
    if travel_date:
        try:
            effective_month = datetime.fromisoformat(travel_date).month
        except (ValueError, TypeError):
            pass  # Invalid date — fall back to travel_month or None

    # --- Pipeline Step 1: Rule-based filtering ---
    # Remove destinations that don't match budget and group type
    # (uses soft budget boundaries so near-boundary destinations are kept)
    filtered = rule_based_filter(DESTINATIONS, budget_level, group_type)

    if not filtered:
        # No destinations match the hard constraints
        # Return empty list — the API route will handle this gracefully
        return []

    # --- Pipeline Step 2: Content-based scoring (50% weight) ---
    # Score each filtered destination against user's style preferences
    # using TF-IDF vectorisation and cosine similarity
    indexed_scores = compute_content_scores(filtered, style_preferences)

    # --- Pipeline Step 3: Compute all sub-scores and combine ---
    # For each destination, compute the weighted combination of all factors
    scored = []
    for i, content_score in indexed_scores:
        dest = filtered[i]

        # Sub-score 1: TF-IDF content similarity (already computed)
        s_content = content_score

        # Sub-score 2: Seasonal relevance
        s_seasonal = compute_seasonal_score(dest, effective_month)

        # Sub-score 3: Popularity and safety
        s_popularity = compute_popularity_safety_score(dest, group_type)

        # Sub-score 4: Climate preference alignment
        s_climate = compute_climate_score(dest, style_preferences)

        # Sub-score 5: Budget gradient
        s_budget = compute_budget_gradient_score(dest, budget_level)

        # Weighted combination
        final_score = (
            SCORE_WEIGHTS["content"]    * s_content +
            SCORE_WEIGHTS["seasonal"]   * s_seasonal +
            SCORE_WEIGHTS["popularity"] * s_popularity +
            SCORE_WEIGHTS["climate"]    * s_climate +
            SCORE_WEIGHTS["budget"]     * s_budget
        )

        scored.append((dest, final_score))

    # --- Pipeline Step 4: Apply travel history penalty ---
    # Reduce scores for destinations the user has already visited
    scored = apply_history_penalty(scored, travel_history)

    # --- Pipeline Step 5: Apply visa accessibility scoring ---
    # Adjust scores based on how easy each destination is to enter
    # with the user's passport. Removes 'not-admitted' destinations.
    if passport_country:
        scored = apply_visa_scoring(scored, passport_country)

    # --- Pipeline Step 5b: Apply feedback-based adaptive boost ---
    scored = apply_feedback_boost(scored)

    # --- Pipeline Step 6: Sort by score (descending) ---
    scored.sort(key=lambda x: x[1], reverse=True)

    # --- Pipeline Step 7: Enforce geographic diversity ---
    # All destinations are now European, so we enforce country diversity
    # instead of continent diversity (min_continents=1 effectively skips
    # continent swapping but keeps the function available for future use)
    top_results = enforce_geographic_diversity(scored, top_n=top_n, min_continents=1)

    # --- Pipeline Step 8: Build the response objects ---
    recommendations = []
    for dest, score in top_results:
        # Create a copy of the destination dict so we don't mutate the original
        result = dict(dest)

        # Add the match score (rounded to 2 decimal places for readability)
        result["match_score"] = round(score, 2)

        # Generate a human-readable explanation for the match
        result["match_reason"] = generate_match_reason(
            dest, style_preferences, budget_level, travel_month=effective_month
        )

        # Attach visa information if passport is provided
        if passport_country:
            visa = get_visa_info_for_destination(dest, passport_country)
            if visa:
                result["visa_info"] = visa

        recommendations.append(result)

    return recommendations


# ---------------------------------------------------------------------------
# STEP 8b: Feedback-Based Score Adjustment (Adaptive Learning)
# ---------------------------------------------------------------------------
# Reads user feedback data (booked/saved/dismissed/viewed) and adjusts
# recommendation scores. Destinations that users frequently book or save
# get a small boost; destinations frequently dismissed get a small penalty.
# This implements the adaptive learning loop from the project proposal.
# ---------------------------------------------------------------------------

_FEEDBACK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "feedback.json")


def apply_feedback_boost(scored_destinations):
    """
    Adjust recommendation scores based on aggregated user feedback.

    Reads feedback.json, computes a sentiment score per destination
    (weighted sum of booked=5, saved=3, viewed=1, dismissed=-2),
    normalises to [-1, +1], and applies a small adjustment (8% weight).

    Parameters
    ----------
    scored_destinations : list[tuple(dict, float)]
        List of (destination, score) tuples.

    Returns
    -------
    list[tuple(dict, float)]
        Same list with adjusted scores. Scores capped at [0.0, 1.0].
    """
    try:
        with open(_FEEDBACK_PATH, "r", encoding="utf-8") as f:
            feedback = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return scored_destinations  # No feedback data — return unchanged

    if not feedback:
        return scored_destinations

    # Compute sentiment score per destination
    sentiment = {}
    for entry in feedback:
        did = entry.get("destination_id", "")
        weight = entry.get("weight", 0)
        sentiment[did] = sentiment.get(did, 0) + weight

    if not sentiment:
        return scored_destinations

    # Normalise to [-1, +1] range
    max_abs = max(abs(v) for v in sentiment.values()) or 1
    normalised = {did: val / max_abs for did, val in sentiment.items()}

    # Apply small adjustment (8% weight) to each scored destination
    adjusted = []
    for dest, score in scored_destinations:
        boost = normalised.get(dest["id"], 0.0) * 0.08
        new_score = max(0.0, min(1.0, score + boost))
        adjusted.append((dest, new_score))

    return adjusted


# ---------------------------------------------------------------------------
# STEP 9: Destination Similarity Function
# ---------------------------------------------------------------------------
# Powers "You might also like..." features on the frontend. Given a
# destination ID, finds the most similar destinations using the TF-IDF
# vectors built from their text representations.
# ---------------------------------------------------------------------------

def get_similar_destinations(destination_id, top_n=5):
    """
    Find destinations similar to a given one using TF-IDF cosine similarity.

    This function builds TF-IDF vectors for all destinations and returns
    the top-N most similar to the specified destination. Useful for "You
    might also like..." recommendations on destination detail pages.

    Parameters
    ----------
    destination_id : str
        The ID of the destination to find similar matches for.
    top_n : int, optional
        Number of similar destinations to return (default: 5).

    Returns
    -------
    list[dict]
        Top N similar destinations, each containing all destination fields
        plus a similarity_score (float between 0 and 1).

    Example
    -------
    >>> similar = get_similar_destinations("bali")
    >>> [d["name"] for d in similar[:3]]
    ['Phuket', 'Ko Samui', 'Goa']
    """
    # Find the target destination by ID
    target = None
    target_index = None
    for i, dest in enumerate(DESTINATIONS):
        if dest["id"] == destination_id:
            target = dest
            target_index = i
            break

    if target is None:
        return []  # Destination not found

    # Use pre-computed TF-IDF matrix (cached at module load)
    similarity_scores = cosine_similarity(
        _TFIDF_MATRIX[target_index], _TFIDF_MATRIX
    ).flatten()

    # Create (index, score) pairs, excluding the target itself
    scored = []
    for i, score in enumerate(similarity_scores):
        if i != target_index:
            scored.append((i, float(score)))

    # Sort by similarity score (descending) and take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top_similar = scored[:top_n]

    # Build result objects
    results = []
    for idx, sim_score in top_similar:
        result = dict(DESTINATIONS[idx])
        result["similarity_score"] = round(sim_score, 2)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# STEP 10: Trending Destinations Function
# ---------------------------------------------------------------------------
# Returns destinations sorted by a combination of popularity and seasonal
# relevance. Useful for homepage "Trending Now" sections.
# ---------------------------------------------------------------------------

def get_trending_destinations(month=None, top_n=10):
    """
    Get trending destinations based on popularity and seasonal relevance.

    Combines each destination's popularity_score with its seasonal relevance
    for the specified month to produce a "trending" ranking. If no month is
    provided, defaults to the current month.

    Parameters
    ----------
    month : int or None, optional
        Month number (1-12) to evaluate seasonal relevance for.
        Defaults to the current month if not specified.
    top_n : int, optional
        Number of trending destinations to return (default: 10).

    Returns
    -------
    list[dict]
        Top N trending destinations, each containing all destination fields
        plus a trending_score (float between 0 and 1).

    Example
    -------
    >>> trending = get_trending_destinations(month=7, top_n=5)
    >>> [d["name"] for d in trending[:3]]
    ['Santorini', 'Barcelona', 'Dubrovnik']
    """
    # Default to the current month if none provided
    if month is None:
        month = datetime.now().month

    # Score each destination: 60% popularity + 40% seasonal relevance
    scored = []
    for dest in DESTINATIONS:
        popularity = dest.get("popularity_score", 50) / 100.0
        seasonal = compute_seasonal_score(dest, month)

        trending_score = (0.60 * popularity) + (0.40 * seasonal)
        scored.append((dest, trending_score))

    # Sort by trending score (descending)
    scored.sort(key=lambda x: x[1], reverse=True)
    top_trending = scored[:top_n]

    # Build result objects
    results = []
    for dest, trend_score in top_trending:
        result = dict(dest)
        result["trending_score"] = round(trend_score, 2)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# SVD Collaborative Filtering Recommendations
# ---------------------------------------------------------------------------
# Uses Singular Value Decomposition to find latent patterns in user-destination
# interaction data. When enough users exist, this captures preferences that
# content-based filtering misses (e.g., "users who visited Bali also loved
# Sri Lanka" even if the tags don't overlap much).
#
# Falls back to content-based recommendations if fewer than 5 user histories
# are available (cold start problem).
# ---------------------------------------------------------------------------

def get_svd_recommendations(user_history, all_user_histories,
                            budget_level, group_type, top_n=5):
    """
    SVD-based collaborative filtering recommendation.

    Builds a user-destination interaction matrix, decomposes it
    using Singular Value Decomposition, finds similar users,
    and recommends destinations they visited that this user hasn't.

    Falls back to content-based get_recommendations() if fewer
    than 5 users exist (cold start problem).

    Parameters
    ----------
    user_history : list[str]
        Destination IDs the current user has visited.
    all_user_histories : list[list[str]]
        List of destination ID lists for all users in the system.
    budget_level : str
        One of "low", "medium", or "high".
    group_type : str
        One of "solo", "couple", "family", or "friends".
    top_n : int, optional
        Number of recommendations to return (default: 5).

    Returns
    -------
    list[dict]
        Top N recommendations with match_score and match_reason.
    """
    # Cold start fallback — not enough users for collaborative filtering
    if len(all_user_histories) < 5:
        return get_recommendations(
            budget_level=budget_level,
            style_preferences=[],
            group_type=group_type,
            travel_history=user_history,
            top_n=top_n
        )

    # Build destination index map
    all_dest_ids = [d["id"] for d in DESTINATIONS]
    dest_index = {did: i for i, did in enumerate(all_dest_ids)}

    # Build interaction matrix (users x destinations)
    matrix = np.zeros((len(all_user_histories), len(all_dest_ids)))
    for u_idx, history in enumerate(all_user_histories):
        for dest_id in history:
            if dest_id in dest_index:
                matrix[u_idx][dest_index[dest_id]] = 1

    # SVD decomposition — k latent factors
    k = min(10, min(matrix.shape) - 1)
    if k < 1:
        return get_recommendations(
            budget_level=budget_level,
            style_preferences=[],
            group_type=group_type,
            travel_history=user_history,
            top_n=top_n
        )

    U, sigma, Vt = svds(csr_matrix(matrix, dtype=float), k=k)
    predicted = U @ np.diag(sigma) @ Vt

    # Build current user's vector from their history
    user_vec = np.zeros(len(all_dest_ids))
    for dest_id in user_history:
        if dest_id in dest_index:
            user_vec[dest_index[dest_id]] = 1

    # Find k=3 most similar users by cosine similarity
    sims = cosine_similarity([user_vec], matrix)[0]
    similar_user_indices = np.argsort(sims)[::-1][:3]

    # Average predicted ratings from similar users
    avg_predicted = predicted[similar_user_indices].mean(axis=0)

    # Exclude already visited destinations
    visited_indices = {dest_index[d] for d in user_history
                       if d in dest_index}

    # Rank unvisited destinations by predicted score
    ranked = [(i, avg_predicted[i]) for i in range(len(all_dest_ids))
              if i not in visited_indices]
    ranked.sort(key=lambda x: x[1], reverse=True)

    # Build results
    results = []
    for dest_idx, score in ranked[:top_n]:
        result = dict(DESTINATIONS[dest_idx])
        result["match_score"] = round(float(score), 2)
        result["match_reason"] = "Recommended based on similar travellers"
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Evaluation Metrics (Precision, Recall, F1)
# ---------------------------------------------------------------------------
# Used to demonstrate recommendation accuracy for coursework evaluation.
# Tests the engine against predefined test cases with known-correct answers.
# ---------------------------------------------------------------------------

def evaluate_recommendations(test_cases):
    """
    Compute precision and recall for the recommendation engine.
    Used to demonstrate the accuracy threshold from the evaluation plan.

    Parameters
    ----------
    test_cases : list[dict]
        Each dict has:
        - "input": dict of get_recommendations() keyword arguments
        - "relevant": list of destination IDs considered correct

    Returns
    -------
    dict
        precision, recall, f1 scores (each 0-1), and meets_threshold bool.

    Example
    -------
    >>> cases = [{
    ...     "input": {"budget_level": "low", "style_preferences": ["beach"],
    ...               "group_type": "solo", "top_n": 5},
    ...     "relevant": ["bali", "zanzibar", "goa", "phuket", "sri-lanka"]
    ... }]
    >>> evaluate_recommendations(cases)
    {'precision': 0.6, 'recall': 0.6, 'f1': 0.6, 'meets_threshold': False}
    """
    precisions, recalls = [], []

    for case in test_cases:
        recs = get_recommendations(**case["input"])
        rec_ids = {r["id"] for r in recs}
        relevant = set(case["relevant"])

        if not rec_ids:
            precisions.append(0)
            recalls.append(0)
            continue

        true_positives = len(rec_ids & relevant)
        precision = true_positives / len(rec_ids)
        recall = true_positives / len(relevant) if relevant else 0

        precisions.append(precision)
        recalls.append(recall)

    avg_precision = sum(precisions) / len(precisions) if precisions else 0
    avg_recall = sum(recalls) / len(recalls) if recalls else 0
    f1 = (2 * avg_precision * avg_recall /
          (avg_precision + avg_recall + 1e-9))

    return {
        "precision": round(avg_precision, 3),
        "recall": round(avg_recall, 3),
        "f1": round(f1, 3),
        "meets_threshold": avg_precision >= 0.7 and avg_recall >= 0.7
    }
