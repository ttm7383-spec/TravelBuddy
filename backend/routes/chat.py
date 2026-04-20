"""
Chat route — AI travel assistant powered by Claude Haiku.
Returns structured JSON cards, never plain text.
Falls back to destinations.json data if ANTHROPIC_API_KEY is not set.
"""

import os
import json
import re
import time
import uuid
import logging
from flask import Blueprint, request, jsonify

try:
    from services.wikipedia_service import (
        get_city_knowledge,
        get_country_knowledge,
        get_attraction_detail,
    )
    _WIKIPEDIA_AVAILABLE = True
except Exception as _wiki_err:  # pragma: no cover - graceful degradation
    print(f"[Chat] Wikipedia service unavailable: {_wiki_err}")
    _WIKIPEDIA_AVAILABLE = False

    def get_city_knowledge(city, country):
        return {}

    def get_country_knowledge(country):
        return {}

    def get_attraction_detail(attraction, city):
        return ""

try:
    from services.places_service import get_places as _osm_get_places
    _PLACES_AVAILABLE = True
except Exception as _places_err:  # pragma: no cover - graceful degradation
    print(f"[Chat] Places service unavailable: {_places_err}")
    _PLACES_AVAILABLE = False

    def _osm_get_places(city, category, limit=6, timeout=12):
        return []


# ── Debug logger for the AI Concierge ────────────────────────────
_chat_logger = logging.getLogger("travelbuddy.chat")
_chat_logger.setLevel(logging.INFO)
if not _chat_logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[Chat] %(message)s"))
    _chat_logger.addHandler(_h)


# ── In-memory session store (resets on server restart) ───────────
# Keyed by session_id sent by the client. When the browser refreshes
# and drops its id, the server simply issues a new one — effectively
# resetting memory per the spec.
_SESSION_STORE = {}
_SESSION_TTL_SECONDS = 3600

chat_bp = Blueprint("chat", __name__)

# Load destinations for fallback
_dest_path = os.path.join(os.path.dirname(__file__), "..", "recommender", "destinations.json")
try:
    with open(_dest_path, "r", encoding="utf-8") as f:
        DESTINATIONS = json.load(f)
except Exception:
    DESTINATIONS = []

DEST_MAP = {d["name"].lower(): d for d in DESTINATIONS}
DEST_MAP.update({d["id"].lower(): d for d in DESTINATIONS})

# Country → top cities (for "trip to USA", "trip to Japan" etc.)
COUNTRY_CITIES = {}
for _d in DESTINATIONS:
    _c = _d.get("country", "").lower()
    if _c:
        COUNTRY_CITIES.setdefault(_c, []).append(_d)
# Sort each country's cities by popularity_score descending
for _c in COUNTRY_CITIES:
    COUNTRY_CITIES[_c].sort(key=lambda x: x.get("popularity_score", 0), reverse=True)

# Country name aliases → canonical lowercase country name
COUNTRY_ALIASES = {
    "usa": "usa", "us": "usa", "united states": "usa", "america": "usa",
    "uk": "united kingdom", "britain": "united kingdom", "england": "united kingdom",
    "uae": "uae", "emirates": "uae",
    "japan": "japan", "spain": "spain", "france": "france", "italy": "italy",
    "thailand": "thailand", "indonesia": "indonesia", "mexico": "mexico",
    "greece": "greece", "turkey": "turkey", "germany": "germany",
    "portugal": "portugal", "australia": "australia", "india": "india",
    "brazil": "brazil", "colombia": "colombia", "peru": "peru",
    "south korea": "south korea", "korea": "south korea",
    "new zealand": "new zealand", "south africa": "south africa",
    "morocco": "morocco", "egypt": "egypt", "croatia": "croatia",
    "vietnam": "vietnam", "cambodia": "cambodia", "nepal": "nepal",
    "argentina": "argentina", "cuba": "cuba", "canada": "canada",
}


# Explicit ordering requested for the flagship country queries. When a DB
# entry isn't present, we still emit a synthetic destination with the right
# name so the frontend never shows something like "Spain In Under".
_PREFERRED_CITIES_BY_COUNTRY = {
    "spain":         ["barcelona", "madrid", "seville"],
    "italy":         ["rome", "florence", "venice"],
    "france":        ["paris", "lyon", "nice"],
    "greece":        ["athens", "santorini", "mykonos"],
    "united kingdom": ["london", "edinburgh", "manchester"],
}


def _resolve_country_cities(canonical_country):
    """Return the preferred 3 destination dicts for a country, falling back
    to popularity-ordered DB entries when preferred city isn't present."""
    preferred = _PREFERRED_CITIES_BY_COUNTRY.get(canonical_country, [])
    out = []
    used = set()
    for city in preferred:
        d = DEST_MAP.get(city)
        if d and d["id"] not in used:
            out.append(d)
            used.add(d["id"])
        elif city not in used:
            synthetic = dict(_SYNTHETIC_DEFAULT)
            synthetic["id"] = city.replace(" ", "-")
            synthetic["name"] = city.title()
            synthetic["country"] = canonical_country.title()
            out.append(synthetic)
            used.add(city)
    # Top up from DB popularity if we still have fewer than 3.
    for d in COUNTRY_CITIES.get(canonical_country, []):
        if len(out) >= 3:
            break
        if d["id"] not in used:
            out.append(d)
            used.add(d["id"])
    return out[:3]


def _parse_origin_destination(msg):
    """
    Parse origin and destination(s) from user message.
    'from London' = origin only (strip it).
    'to [city/country]' = destination.
    Returns (origin, destinations_list).
    """
    origin = "London"  # default

    # Extract origin: "from London", "from Manchester", etc.
    origin_match = re.search(r'\bfrom\s+([a-z][a-z\s]{1,25}?)(?:\s+to\b|\s*$|\s*,|\s+on\b|\s+for\b|\s+in\b)', msg)
    if origin_match:
        origin = origin_match.group(1).strip().title()

    # Remove "from [origin]" from message so it doesn't match as destination
    cleaned = re.sub(r'\bfrom\s+[a-z][a-z\s]{1,25}?(?=\s+to\b|\s*$|\s*,|\s+on\b|\s+for\b|\s+in\b)', '', msg).strip()

    # Check for country names first (they resolve to multiple cities).
    # Uses word-boundary matching so aliases like "uk" don't match inside
    # arbitrary words ("luck", "buck", "stuck"). For flagship countries we
    # hand back the explicit preferred 3-city shortlist.
    destinations = []
    for alias, canonical in COUNTRY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", cleaned):
            country_dests = _resolve_country_cities(canonical)
            if country_dests:
                return origin, country_dests[:3], canonical

    # Check for specific city names — use word boundaries so "York" doesn't
    # match inside "New York", and "Bath" doesn't match inside "Bathroom".
    for name, dest in DEST_MAP.items():
        if re.search(rf"\b{re.escape(name)}\b", cleaned):
            destinations.append(dest)
            if len(destinations) >= 3:
                break

    return origin, destinations, None


def _detect_budget_tier(msg):
    """
    Detect budget tier from message.
    Returns (multiplier, tier_name, accommodation_note, food_note).
    """
    if any(kw in msg for kw in ["budget", "cheap", "backpack", "hostel", "low cost", "on a budget"]):
        return 0.65, "budget", "Hostels & budget guesthouses", "Street food & markets"
    if any(kw in msg for kw in ["luxury", "luxurious", "premium", "high end", "5 star", "five star", "splurge"]):
        return 1.8, "luxury", "4-5 star hotels", "Fine dining & upscale restaurants"
    return 1.0, "medium", "Mid-range hotel", "Mix of local & restaurants"


def _extract_user_budget(msg):
    """
    Parse an explicit budget amount from the user's message.
    Returns (gbp_amount, currency_label) or (None, None).
    Non-GBP amounts are converted to rough GBP equivalents.
    """
    # Digit-led patterns — require at least one digit, optional thousand separators.
    num = r"(\d[\d,]*)"
    # $500 — USD symbol
    m = re.search(rf"\$\s*{num}", msg)
    if m:
        return round(int(m.group(1).replace(",", "")) * 0.79), "USD"
    # £500 — GBP symbol
    m = re.search(rf"£\s*{num}", msg)
    if m:
        return int(m.group(1).replace(",", "")), "GBP"
    # €500 — EUR symbol
    m = re.search(rf"€\s*{num}", msg)
    if m:
        return round(int(m.group(1).replace(",", "")) * 0.85), "EUR"
    # "500 usd" / "500 dollars"
    m = re.search(rf"\b{num}\s*(usd|dollars?)\b", msg)
    if m:
        return round(int(m.group(1).replace(",", "")) * 0.79), "USD"
    # "500 gbp" / "500 pounds" / "500 quid"
    m = re.search(rf"\b{num}\s*(gbp|pounds?|quid)\b", msg)
    if m:
        return int(m.group(1).replace(",", "")), "GBP"
    # "500 eur" / "500 euros"
    m = re.search(rf"\b{num}\s*(eur|euros?)\b", msg)
    if m:
        return round(int(m.group(1).replace(",", "")) * 0.85), "EUR"
    # "budget of 500" / "budget 500" — must be followed by an actual digit
    m = re.search(rf"budget\s*(?:of|is|=|:)?\s*{num}", msg)
    if m:
        return int(m.group(1).replace(",", "")), "GBP"
    # "under 500" / "up to 500" / "below 500" / "less than 500" / "within 500" /
    # "max 500" — budget cap expressed without an explicit currency.
    m = re.search(rf"(?:under|up\s*to|below|less\s*than|within|max(?:imum)?(?:\s*of)?)\s+{num}", msg)
    if m:
        return int(m.group(1).replace(",", "")), "GBP"
    return None, None


# Multi-word world cities that would otherwise be mis-captured by the
# single-word lowercase regex (e.g. "bars in new york" picks up "new" and
# then "york" clobbers to the DB "York" entry). Pre-checked against the
# message before regex extraction so the full name wins.
_MULTIWORD_CITIES = {
    "new york":         "United States",
    "new delhi":        "India",
    "new orleans":      "United States",
    "san francisco":    "United States",
    "san diego":        "United States",
    "los angeles":      "United States",
    "las vegas":        "United States",
    "hong kong":        "Hong Kong",
    "cape town":        "South Africa",
    "abu dhabi":        "United Arab Emirates",
    "saint petersburg": "Russia",
    "st petersburg":    "Russia",
    "rio de janeiro":   "Brazil",
    "sao paulo":        "Brazil",
    "quebec city":      "Canada",
    "mexico city":      "Mexico",
    "buenos aires":     "Argentina",
    "tel aviv":         "Israel",
    "kuala lumpur":     "Malaysia",
    "ho chi minh city": "Vietnam",
    "phnom penh":       "Cambodia",
    "siem reap":        "Cambodia",
    "luang prabang":    "Laos",
    "da nang":          "Vietnam",
    "chiang mai":       "Thailand",
    "addis ababa":      "Ethiopia",
    "port louis":       "Mauritius",
    "dar es salaam":    "Tanzania",
    "san juan":         "Puerto Rico",
    "panama city":      "Panama",
    "port moresby":     "Papua New Guinea",
    "new zealand":      "New Zealand",
    "south africa":     "South Africa",
    "south korea":      "South Korea",
    "saudi arabia":     "Saudi Arabia",
    "united arab emirates": "United Arab Emirates",
    "united kingdom":   "United Kingdom",
    "united states":    "United States",
    "czech republic":   "Czech Republic",
    "sri lanka":        "Sri Lanka",
    "costa rica":       "Costa Rica",
    "north macedonia":  "North Macedonia",
}


# Synthetic cost estimate for destinations not in the local DB — used only so
# the locked city is never silently replaced. Values are deliberately neutral
# and flagged (_synthetic=True) so the zero-hallucination path can detect them.
_SYNTHETIC_DEFAULT = {
    "id": None,  # filled per-instance
    "name": None,
    "country": "",
    "avg_daily_cost_gbp": 100,
    "budget_level": "medium",
    "tags": [],
    "sample_activities": [],
    "climate": "temperate",
    "best_season": "",
    "avg_rating": 4.5,
    "visa_requirements": {"GB": "Check embassy website"},
    "iata_code": "???",
    "_synthetic": True,
}


def _resolve_locked_destination(user_message, msg, parsed_dests):
    """
    Return the destination the user explicitly specified — locked so it is
    never removed or replaced by later logic. Resolution order:

    1. A Title-Case proper-noun from the original message (covers any world
       city/country including multi-word names like "Rio de Janeiro" and
       ensures "New York" isn't reduced to the DB entry "York").
    2. A lowercase proper-noun via context words (e.g., "hotels in tokyo").
    3. parsed_dests from _parse_origin_destination (DB substring).
    4. A word-boundary DEST_MAP match on the origin-stripped message.

    Returns a destination dict, or None if no destination was provided.
    """
    # Strip the "from <origin>" clause so later fallbacks don't latch on to
    # the origin city when the real destination is elsewhere.
    msg_no_origin = re.sub(
        r"\bfrom\s+[a-z][a-z\s]{1,25}?(?=\s+to\b|\s*$|\s*,|\s+on\b|\s+for\b|\s+in\b)",
        "",
        msg,
    )

    # Pre-regex multi-word city check. Ensures "new york", "cape town",
    # "rio de janeiro", etc. resolve as a single place rather than being
    # split and clobbered by single-word regex or DB substring matches.
    for phrase, country in _MULTIWORD_CITIES.items():
        if re.search(rf"\b{re.escape(phrase)}\b", msg_no_origin):
            db_match = DEST_MAP.get(phrase)
            if db_match:
                return db_match
            alias = phrase.lower()
            if alias in COUNTRY_ALIASES:
                country_cities = COUNTRY_CITIES.get(COUNTRY_ALIASES[alias], [])
                if country_cities:
                    return country_cities[0]
            synthetic = dict(_SYNTHETIC_DEFAULT)
            synthetic["id"] = phrase.replace(" ", "-")
            synthetic["name"] = phrase.title()
            synthetic["country"] = country
            return synthetic

    # Raw extraction from the original-cased message — catches non-DB cities.
    stop_words = {
        "I", "Me", "My", "The", "A", "An", "Some", "Any", "What", "Where",
        "Why", "How", "Who", "Plan", "Trip", "Travel", "Budget", "Days",
        "Day", "Holiday", "Vacation", "Hi", "Hello", "Hey",
        "Hotels", "Hotel", "Food", "Restaurant", "Restaurants", "Flights",
        "Flight", "Tips", "Tip", "Weather", "Visa", "Climate", "Itinerary",
        "Recommend", "Suggest", "Tell",
        # Possessive / interrogative openers that aren't places
        "What's", "How's", "That's", "Here's", "There's", "Let's", "Who's",
        # Common adjectives/nouns that aren't places
        "Solo", "Couple", "Family", "Friends", "Kids", "Children",
        "Safe", "Safety", "Cheap", "Luxury", "Expensive", "Free",
        "Best", "Top", "Good", "Great", "Nice", "Worst",
        # Listing/venue category openers
        "Cafe", "Cafes", "Bar", "Bars", "Pub", "Pubs", "Streetfood",
        "Street", "Attractions", "Things", "Places", "Sights", "Museums",
        "Bakery", "Bakeries", "Market", "Markets", "Breakfast", "Lunch",
        "Dinner", "Brunch",
    }
    # Multi-word place name token: a Title-Case head word, optionally followed
    # by up to 3 more Title-Case words OR short lowercase connectors
    # (de, la, of, the, etc. — "Rio de Janeiro", "Isle of Man", "New York").
    _conn = r"(?:de|la|le|del|della|di|da|do|dos|das|du|of|the|von|van|al|el|en|y)"
    _place = rf"[A-Z][a-zA-Z'\-]+(?:\s+(?:[A-Z][a-zA-Z'\-]+|{_conn})){{0,3}}"
    # Proper-name patterns (Title Case) — catch any capitalised place name.
    # `\b` anchors the preposition list so we don't match "at" inside "what"
    # or "in" inside "location".
    patterns_proper = [
        rf"\b(?:to|in|at|for|about|visit|visiting|trip to|travel to|going to|plan(?:ning)?\s+(?:a\s+trip\s+to)?)\s+({_place})",
        rf"^({_place})\s*(?:,|\.|\bfor\b|\bwith\b|\btrip\b|\bon\b|\bin\b|\d)",
        rf"^({_place})\s*$",
    ]
    # Case-insensitive patterns — catch lowercased input like "hotels in tokyo"
    # and bare-destination starts like "tokyo up to 500". Allow at most 1
    # extra word so we don't over-capture phrases; trailing connectors are
    # then trimmed below.
    # Pattern 1 captures a single word after the preposition so finditer can
    # pick up every "in <place>" / "to <place>" independently, and an over-
    # eager first capture (e.g. "travel to" in "to travel to dubai") can't
    # swallow the real destination. Pattern 2 handles bare-start phrasing
    # where a 2-word destination may appear (e.g. "new york for 7 days").
    patterns_ci = [
        r"\b(?:to|in|at|for|about|visit|visiting|trip to|travel to|going to|plan(?:ning)?\s+(?:a\s+trip\s+to)?)\s+([a-z][a-z'\-]+)",
        r"^([a-z][a-z'\-]+(?:\s+[a-z][a-z'\-]+){0,1})\s*(?:,|\.|\bfor\b|\bwith\b|\btrip\b|\bon\b|\bin\b|\bup\b|\bunder\b|\bbelow\b|\bless\b|\bmax\b|\d)",
    ]
    # Words that should never end a place name — stripped from the tail of a
    # lowercase match. Kept separate from `stop_words` so they don't affect
    # the Title-Case path.
    trail_trim = {
        "in", "on", "at", "for", "with", "by", "about", "to", "from", "than",
        "and", "or", "of", "the", "a", "an", "up", "down", "under", "over",
        "below", "above", "through", "into", "onto", "per", "near",
        "max", "maximum", "min", "minimum", "budget", "cheap", "luxury",
        "mid", "midrange", "within", "less", "plus", "or",
    }
    for p in patterns_proper:
        m = re.search(p, user_message)
        if m:
            name = m.group(1).strip()
            if name and name not in stop_words:
                db_match = DEST_MAP.get(name.lower())
                if db_match:
                    return db_match
                # Country-level match: if the extracted name is a country that
                # has cities in our DB, prefer the top DB city so downstream
                # logic shows real data (and the offline-estimate notice does
                # not fire for country queries we actually have data for).
                alias = name.lower()
                if alias in COUNTRY_ALIASES:
                    country_cities = COUNTRY_CITIES.get(COUNTRY_ALIASES[alias], [])
                    if country_cities:
                        return country_cities[0]
                synthetic = dict(_SYNTHETIC_DEFAULT)
                synthetic["id"] = name.lower().replace(" ", "-")
                synthetic["name"] = name
                # Best-effort country guess from the known-cities map so
                # downstream OSM lookups can disambiguate.
                guess = _WIKI_CITIES.get(name.lower())
                if guess:
                    synthetic["country"] = guess
                return synthetic
    # Iterate ALL regex matches so we don't stop at a false early capture
    # like "to get street" in "where to get street food in bangkok".
    # Preference: DB / country alias match wins immediately; otherwise we
    # keep the LAST non-junk synthetic candidate (destinations tend to be
    # at the end of natural-language queries).
    best_synthetic_name = None
    for p in patterns_ci:
        for m in re.finditer(p, msg_no_origin):
            raw = m.group(1).strip()
            words = raw.split()
            while words and (words[-1].lower() in trail_trim
                             or words[-1].capitalize() in stop_words):
                words.pop()
            if not words:
                continue
            name = " ".join(w.capitalize() for w in words)
            if name in stop_words:
                continue
            db_match = DEST_MAP.get(name.lower())
            if db_match:
                return db_match
            alias = name.lower()
            if alias in COUNTRY_ALIASES:
                country_cities = COUNTRY_CITIES.get(COUNTRY_ALIASES[alias], [])
                if country_cities:
                    return country_cities[0]
            # Track as preliminary candidate; overwritten by any later match.
            best_synthetic_name = name
    if best_synthetic_name:
        # Before committing to a synthetic name, check if the message
        # word-boundary-matches any real DB destination. A real DB city
        # always beats a non-place synthetic guess (e.g. "bali" beats "Solo"
        # in "is bali safe for solo travellers").
        for name, dest in DEST_MAP.items():
            if name and re.search(rf"\b{re.escape(name)}\b", msg_no_origin):
                return dest
        synthetic = dict(_SYNTHETIC_DEFAULT)
        synthetic["id"] = best_synthetic_name.lower().replace(" ", "-")
        synthetic["name"] = best_synthetic_name
        guess = _WIKI_CITIES.get(best_synthetic_name.lower())
        if guess:
            synthetic["country"] = guess
        return synthetic

    # Fall back to anything _parse_origin_destination already pulled out of
    # DEST_MAP — reached only when no proper-noun / lowercase regex matched.
    if parsed_dests:
        return parsed_dests[0]

    # Last resort: word-boundary match against DEST_MAP on the origin-stripped
    # message. Keeps behaviour for single-word lowercased inputs like
    # "hotels in paris" while avoiding "York" matching inside "New York".
    for name, dest in DEST_MAP.items():
        if re.search(rf"\b{re.escape(name)}\b", msg_no_origin):
            return dest

    return None


def _classify_budget_fit(estimated_cost, user_budget_gbp):
    """Classify how the user's stated budget compares to estimated trip cost.
    Returns 'too_low', 'perfect', 'too_high', or None if no budget was given."""
    if not user_budget_gbp or user_budget_gbp <= 0 or estimated_cost <= 0:
        return None
    ratio = estimated_cost / user_budget_gbp
    if ratio > 1.15:
        return "too_low"
    if ratio < 0.7:
        return "too_high"
    return "perfect"


def _build_budget_conflict_card(city, estimated_cost, user_budget_gbp, num_days, cost_per_day, status):
    """Return a `tips` card explaining how the user's budget fits the locked destination."""
    user_daily = round(user_budget_gbp / num_days) if num_days > 0 else user_budget_gbp

    if status == "too_low":
        gap = estimated_cost - user_budget_gbp
        feasible_days = max(1, user_budget_gbp // max(cost_per_day, 1))
        message = (
            f"Your £{user_budget_gbp} budget covers about £{user_daily}/day in {city}, "
            f"but {num_days} days here typically runs ~£{estimated_cost} "
            f"(~£{cost_per_day}/day). Short by ~£{gap}."
        )
        suggestions = [
            f"Increase budget to at least £{estimated_cost} for {num_days} comfortable days",
            f"Shorten the trip to {feasible_days} days at ~£{cost_per_day}/day",
            "Switch to hostels, public transport and street food to cut daily cost by ~40%",
            "Travel in shoulder season for cheaper flights and stays",
        ]
    elif status == "too_high":
        message = (
            f"Your £{user_budget_gbp} budget gives you ~£{user_daily}/day in {city}, "
            f"well above the typical ~£{cost_per_day}/day. Plenty of room for upgrades."
        )
        suggestions = [
            "Upgrade to a boutique or 4-star hotel",
            "Add a fine-dining meal or private tour",
            "Extend the trip or add a nearby side-trip",
        ]
    else:  # "perfect"
        message = (
            f"Your £{user_budget_gbp} budget is a good fit for {num_days} days in {city} "
            f"(~£{user_daily}/day vs typical ~£{cost_per_day}/day)."
        )
        suggestions = [
            "Book flights 6-8 weeks ahead to lock in the best rates",
            "Mix local eateries with one or two splurge meals",
        ]

    return {
        "type": "tips",
        "data": {
            "city": city,
            "categories": [
                {"name": "budget fit", "tips": [message]},
                {"name": "suggestions", "tips": suggestions},
            ],
        },
    }


# ── Session memory helpers ───────────────────────────────────────

def _cleanup_expired_sessions():
    """Drop sessions that have been idle for longer than the TTL."""
    now = time.time()
    for sid in [sid for sid, s in _SESSION_STORE.items()
                if now - s.get("last_used_at", now) > _SESSION_TTL_SECONDS]:
        _SESSION_STORE.pop(sid, None)


def _get_session(session_id):
    """Return the session dict for a given id, or None if absent/expired."""
    if not session_id:
        return None
    _cleanup_expired_sessions()
    return _SESSION_STORE.get(session_id)


def _save_session(session_id, user_message, response, locked_destination,
                  user_budget_gbp, num_days, budget_mult_tier):
    """Store conversation state for follow-up refinement. Also appends the
    user message and the assistant's reply to `conversation` so the next
    turn can send it back to Claude for memory."""
    if not session_id:
        return
    now = time.time()
    entry = _SESSION_STORE.get(session_id, {
        "created_at": now,
        "query_history": [],
        "conversation": [],
    })
    entry["last_destination"] = locked_destination
    entry["last_response"] = response
    entry["last_budget_gbp"] = user_budget_gbp
    entry["last_num_days"] = num_days
    entry["last_budget_tier"] = budget_mult_tier
    entry["last_used_at"] = now
    entry["query_history"] = (entry.get("query_history", []) +
                              [{"message": user_message, "at": now}])[-10:]

    # Append the turn to `conversation` — used as Claude's messages history.
    # We store the assistant's NATURAL-LANGUAGE reply only (not the cards JSON)
    # so Claude has context for follow-ups without being primed to re-emit the
    # same card types for a different intent. Card summaries are included as
    # short text so Claude knows what was shown.
    conv = entry.get("conversation", [])
    conv.append({"role": "user", "content": user_message})
    cards_list = (response or {}).get("cards", []) or []
    card_summary = ""
    if cards_list:
        counts = {}
        for c in cards_list:
            t = c.get("type", "other")
            counts[t] = counts.get(t, 0) + 1
        card_summary = " (" + ", ".join(f"{n} {t}" for t, n in counts.items()) + ")"
    assistant_text = ((response or {}).get("reply", "") or "") + card_summary
    if not assistant_text.strip():
        assistant_text = "(previous turn returned structured cards)"
    conv.append({"role": "assistant", "content": assistant_text})
    entry["conversation"] = conv[-20:]  # keep last 10 exchanges
    _SESSION_STORE[session_id] = entry


# Keywords we use to recognise a travel-related query in offline mode —
# if a message has none of these AND no detected destination, it's treated
# as off-topic and politely refused.
_TRAVEL_KEYWORDS = (
    "travel", "trip", "visit", "vacation", "holiday", "tour", "tourism",
    "flight", "fly", "plane", "airline", "airport", "layover",
    "hotel", "hostel", "airbnb", "stay", "accommodation", "resort",
    "restaurant", "cafe", "bar", "pub", "eat", "food", "dish", "cuisine",
    "dinner", "lunch", "breakfast", "brunch", "streetfood", "street food",
    "itinerary", "plan", "day trip", "weekend", "backpack", "road trip",
    "visa", "passport", "schengen", "border",
    "budget", "cost", "cheap", "luxury", "money",
    "weather", "climate", "best time", "season", "monsoon",
    "beach", "mountain", "desert", "lake", "river", "island",
    "attraction", "landmark", "museum", "temple", "church", "cathedral",
    "tips", "advice", "scam", "safety", "solo", "couple", "family",
    "pack", "packing", "what to wear", "currency", "language",
    "sim card", "metro", "subway", "transport", "taxi", "uber",
    "recommend", "suggest", "where should", "hidden gem",
)


def _looks_travel_related(msg_lower):
    """Cheap keyword/place check for the offline off-topic guard."""
    if not msg_lower:
        return False
    for kw in _TRAVEL_KEYWORDS:
        if kw in msg_lower:
            return True
    for name in DEST_MAP:
        if name and re.search(rf"\b{re.escape(name)}\b", msg_lower):
            return True
    for alias in COUNTRY_ALIASES:
        if alias and re.search(rf"\b{re.escape(alias)}\b", msg_lower):
            return True
    return False


# Keywords that indicate a follow-up refinement on a previous query.
_FOLLOWUP_KEYWORDS = (
    "cheaper", "more expensive", "pricier", "budget version", "luxury version",
    "shorter", "longer", "more days", "fewer days", "less days",
    "make it", "same but", "same trip", "what about", "instead",
    "reduce", "increase", "lower", "higher", "bump",
)


def _apply_followup_context(message, session):
    """
    If the current message is a follow-up on a prior query, inherit the
    previous destination by rewriting the message. Day-count inheritance is
    ONLY applied to explicit refinement follow-ups ("make it cheaper",
    "shorter", etc.) so a new intent like "cafes in Paris" doesn't get a
    spurious "for 7 days" appended that would re-route it to the itinerary
    branch.
    """
    if not session or not session.get("last_destination"):
        return message

    last_dest = session["last_destination"]
    dest_name = last_dest.get("name", "")
    lower = message.lower()

    # Does the current message already name a destination?
    has_destination = dest_name.lower() in lower if dest_name else False
    if not has_destination:
        for name in DEST_MAP:
            if name and name in lower:
                has_destination = True
                break

    is_followup = any(kw in lower for kw in _FOLLOWUP_KEYWORDS)

    augmented = message
    # Inherit destination when the new message omits it (helps "hotels"
    # without restating the city, and short follow-ups like "make it cheaper").
    if not has_destination and dest_name:
        augmented = f"{message} in {dest_name}"

    # Inherit day count ONLY for explicit refinement follow-ups so new
    # intents ("cafes in X", "hotels in X") don't inherit a stale day count.
    if (is_followup and re.search(r"\d+\s*days?", lower) is None
            and session.get("last_num_days")):
        augmented = f"{augmented} for {session['last_num_days']} days"

    return augmented


# ── Output validation & force-correction ─────────────────────────

# Card types whose data schema doesn't include a top-level `city` field
# (hotel, food, flight, visa, tips). For these we check related fields
# (name, neighbourhood, route, country) and fall back to trusting the
# intent router for the rest.
_CITY_AGNOSTIC_CARD_TYPES = {"tips", "hotel", "food", "flight", "visa"}

# Fields in card.data that commonly carry the destination name.
_DEST_TEXT_FIELDS = (
    "city", "name", "area", "neighbourhood", "address_hint",
    "route", "country", "title",
)


def _card_references_destination(card, requested_name_lower):
    """Return True if the card clearly matches — or at least doesn't clash
    with — the locked destination. Strict for cards that carry an explicit
    `city` field; lenient (fall-back to type whitelist) for the rest."""
    data = card.get("data", {})
    # Prefer an explicit city match when the card has that field.
    city = (data.get("city") or "").lower()
    if city:
        return requested_name_lower in city or city in requested_name_lower
    # Otherwise, accept if any common destination-bearing field matches.
    for key in _DEST_TEXT_FIELDS:
        val = (data.get(key) or "")
        if not isinstance(val, str):
            continue
        val_l = val.lower()
        if val_l and (requested_name_lower in val_l or val_l in requested_name_lower):
            return True
    # Last resort: trust the intent router for schemas that don't carry a
    # destination text field (food, flight, visa, tips, hotel).
    return card.get("type") in _CITY_AGNOSTIC_CARD_TYPES


def _validate_destination_lock(response, locked_destination):
    """
    Verify every card in the response is about the locked destination.
    Returns (is_valid, list_of_issue_strings).
    """
    if not locked_destination:
        return True, []
    requested = (locked_destination.get("name") or "").lower()
    if not requested:
        return True, []

    issues = []
    for card in response.get("cards", []) or []:
        if not _card_references_destination(card, requested):
            data = card.get("data", {})
            city = data.get("city") or "<missing>"
            issues.append(
                f"card '{card.get('type')}' referenced '{city}' instead of '{requested}'"
            )
    return (len(issues) == 0), issues


def _force_correct_response(locked_destination, user_budget_gbp=None,
                            num_days=None, note=None):
    """
    Build a minimal, correct response when validation fails or when no
    detailed data is available for the locked destination (zero-hallucination
    fallback). Always includes an overview, a budget-analysis card, and a
    skip-notice explaining why details are missing.
    """
    name = locked_destination.get("name", "Your destination")
    country = locked_destination.get("country", "")
    is_synthetic = locked_destination.get("_synthetic", False)

    overview_desc = (
        f"Accurate detailed data for {name} is currently unavailable in offline "
        f"mode — I won't invent attractions or prices."
        if is_synthetic
        else f"Here are the details about {name}."
    )
    if note:
        overview_desc = f"{overview_desc} {note}"

    cards = [{
        "type": "overview",
        "data": {
            "city": name,
            "country": country,
            "description": overview_desc,
            "vibes": [],
            "highlights": [],
            "best_time": "",
            "language": "",
            "currency": "",
            "local_tip": "",
        },
    }]

    # Budget analysis (always, when a budget was supplied)
    if user_budget_gbp is not None:
        base_days = num_days or 5
        cost_per_day = round(locked_destination.get("avg_daily_cost_gbp", 100))
        estimated_cost = cost_per_day * base_days
        status = _classify_budget_fit(estimated_cost, user_budget_gbp)
        if status:
            cards.append(_build_budget_conflict_card(
                name, estimated_cost, user_budget_gbp,
                base_days, cost_per_day, status,
            ))

    # Skip notice — be transparent about what we didn't include
    if is_synthetic:
        cards.append(_build_skip_notice_card(
            name, "detailed itinerary & hotels",
            f"Accurate data for {name} is unavailable offline; no attractions, "
            "hotels, or restaurant names are shown to avoid hallucinated details."
        ))

    return {
        "reply": overview_desc,
        "cards": cards,
        "suggestions": [
            f"Budget for {name}",
            f"Visa info for {country or name}",
            f"Weather in {name}",
        ],
    }


# ── Skip-notice & reduced-plan cards ─────────────────────────────

def _build_skip_notice_card(city, what, reason):
    """Return a tips card explaining why a piece of content was skipped."""
    return {
        "type": "tips",
        "data": {
            "city": city,
            "categories": [
                {"name": f"{what} skipped", "tips": [reason]},
            ],
        },
    }


def _build_reduced_plan_cards(destination, user_budget_gbp, num_days_requested,
                              accom_note, food_note, origin):
    """
    Produce a reduced-cost itinerary + budget card that fits within the user's
    budget. Uses the budget-tier multiplier (0.65) and shortens the trip if
    needed. Returns (cards, adjusted_days, adjusted_daily_cost).
    """
    base_daily = destination.get("avg_daily_cost_gbp", 100)
    reduced_mult = 0.65
    reduced_daily = max(1, round(base_daily * reduced_mult))

    if reduced_daily * num_days_requested <= user_budget_gbp:
        adjusted_days = num_days_requested
    else:
        adjusted_days = max(1, int(user_budget_gbp // reduced_daily))

    if destination.get("_synthetic"):
        # Zero-hallucination: for unknown destinations, don't invent a day plan.
        # Return only the budget breakdown at the reduced tier.
        return ([
            _build_budget_card(
                [(destination, adjusted_days)], adjusted_days, reduced_mult,
                "Hostels & budget guesthouses", "Street food & markets", origin,
            )
        ], adjusted_days, reduced_daily)

    cards = [
        _build_itinerary_card(
            destination, adjusted_days, reduced_daily,
            "Hostels & budget guesthouses", "Street food & markets",
        ),
        _build_budget_card(
            [(destination, adjusted_days)], adjusted_days, reduced_mult,
            "Hostels & budget guesthouses", "Street food & markets", origin,
        ),
    ]
    return cards, adjusted_days, reduced_daily


# ── Debug logging for the concierge ──────────────────────────────

def _log_chat_debug(requested_destination, final_destination,
                    budget_conflict, validation_passed, issues=None,
                    session_id=None, source=None):
    """Emit a single debug line summarising this chat turn's outcome."""
    parts = [
        f"source={source or 'unknown'}",
        f"session={session_id or '-'}",
        f"requested_destination={requested_destination or '-'}",
        f"final_destination={final_destination or '-'}",
        f"budget_conflict={bool(budget_conflict)}",
        f"validation_passed={bool(validation_passed)}",
    ]
    if issues:
        parts.append(f"issues={issues}")
    _chat_logger.info(" ".join(parts))


# ── Claude system prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """You are TravelBuddy — a knowledgeable travel companion with deep knowledge of destinations worldwide. You respond like someone who has actually lived in every city, not a tourist who visited once.

CRITICAL RULES — never break these:

1. STAY ON DESTINATION — if the user asks about Spain, ONLY return Spanish cities. Never add other countries. If the user asks about Barcelona, only plan Barcelona. Never mix countries in one response.

2. BUDGET MUST WORK — if the user says £600 for Spain 8 days, the total of ALL cards combined must NOT exceed £600. State clearly: "Your £600 covers X days across Y cities." Never plan a trip that costs more than the stated budget. If the budget is insufficient, shorten the trip or downgrade tier — never silently exceed.

3. ACTIVITIES MUST BE UNIQUE per day — never repeat the same attraction across multiple days. Day 1, Day 2, Day 3 must each have completely different named activities.

4. LUNCH must be a specific named restaurant or market — never write "Lunch — Mix of local & restaurants" or "Lunch at a local restaurant". Always write something like "Lunch at Bar del Pla, Carrer de la Montcada 2 — order the €12 menú del día".

5. DAILY COST must be realistic and add up to the total — if total budget is £600 and the trip is 8 days, daily budget = £600 / 8 = £75/day maximum. Every day card must show costs within that daily limit, and the sum across days must equal the stated total.

SCOPE — STRICTLY TRAVEL:
You only help with travel topics: destinations, itineraries, hotels, food, flights, visas, weather, budgets, packing, local tips, and trip logistics. If the user asks ANYTHING unrelated to travel (coding, math, personal appearance, general chat, compliments, emotional support, any non-travel topic), respond ONLY with:
{ "reply": "I'm TravelBuddy — I can only help with travel. Ask me about destinations, hotels, food, flights, itineraries, or trip planning.", "cards": [], "suggestions": ["Plan 3 days in Tokyo", "Hotels in Paris", "Where should I go?", "Food in Bangkok"] }

DESTINATION LOCK — NEVER SUBSTITUTE:
If the user names a specific destination (city or country), ALWAYS answer about THAT destination. Never redirect to an alternative city. Never refuse because of region. If the user asks for Tokyo, you answer about Tokyo. If they ask for Lagos, you answer about Lagos. Only suggest alternatives when the user explicitly asks for them ("recommend somewhere", "suggest alternatives").

ZERO HALLUCINATION:
Only include facts from your real knowledge. If you are unsure of a specific hotel name, price, opening hour, or address — leave that field blank, write "varies", or omit the detail. NEVER invent restaurant names, hotel chains, prices, phone numbers, or booking URLs. Real places only, or generic descriptors.

MATCH CARD TYPES TO THE QUESTION — return ONLY the card types the user actually asked for:
- "hotels in X" / "where to stay" → 3 hotel cards, no overview/itinerary
- "plan N days in X" / "itinerary for X" → 1 itinerary card + 1 budget card
- "food in X" / "where to eat" / "restaurants" → 3-5 food cards
- "flights to X" / "how to get to X" → 1 flight card
- "budget for X" / "how much does X cost" → 1 budget card
- "visa for X" / "do I need a visa" → 1 visa card
- "weather in X" / "climate" / "best time" → 1 weather card
- "tips for X" / "scams" / "local advice" → 1 tips card (all 6 categories)
- "tell me about X" / "overview" / overview questions → 1 overview card
- "recommend" / "where should I go" (NO destination given) → 3 overview cards
- Do NOT add unrelated cards — if they asked for hotels, don't append an overview or itinerary.

You ALWAYS respond in structured JSON only. Never plain text.
Response format: { "reply": "natural-language answer for the chat bubble (always required, 1-5 sentences, friendly, helpful)", "cards": [optional list of structured cards — use ONLY for listings/data], "suggestions": [4 natural follow-up suggestions] }

USE "reply" FOR:
- Greetings ("hi", "hello", "how are you") — respond as a travel-savvy friend and steer back to travel ("Hey! Ready to plan a trip? Where are you thinking?")
- Quick answers / clarifications / follow-up questions
- General advice ("is Bali safe?", "best time to visit Japan?", "how do I haggle in Marrakech?")
- Short explanations and tips
- Any conversational turn that doesn't need a structured card
- Off-topic refusals (see SCOPE above)

USE "cards" ONLY WHEN:
- User asks for a LIST of hotels, restaurants, cafes, bars, pubs, street-food spots, attractions, etc.
- User asks for an itinerary (day-by-day plan)
- User asks to compare flights
- User asks for a budget breakdown, weather, or visa details
- A destination overview where the structured layout genuinely helps

For pure conversational questions, set cards to [] and put the answer in "reply".
For listing questions, you may leave "reply" short (e.g., "Here are 5 great cafes in Paris — the first three are local favourites:") and put the detail in the cards.

MEMORY:
You will receive prior conversation turns in the messages array. Treat them as context — remember previously discussed destinations, budgets, and preferences so follow-ups work naturally ("make it cheaper" refers to the last plan discussed).

CRITICAL PARSING RULES — read before anything else:
- "from [city]" = DEPARTURE ORIGIN, not destination
- "to [city/country]" = DESTINATION
- "multi city", "multi-city", "few cities", "several cities" = return one itinerary card PER city
- "on a budget" / "cheap" = daily cost under £80, hostels, street food
- "mid range" = £80-200/day
- "luxury" = £200+/day, 5-star hotels, fine dining
- Country names (USA, Japan, Spain) = pick 3 best cities in that country

YOUR KNOWLEDGE — use all of it. For EVERY city you know:
NEIGHBOURHOODS: exact names, what each is known for, where locals live vs tourist zones, gentrifying areas
FOOD: specific restaurant names, exact dish to order, street food stall locations, what time locals eat, dishes tourists order vs what locals order, price in local currency
TRANSPORT: exact metro/bus line names and numbers, which travel card to buy with cost, local taxi apps (Grab, Bolt, etc), airport transfer options with real prices
TIMING: exact opening hours, best time of DAY to visit, which day of week is quietest, local holidays
SCAMS & SAFETY: specific scams by name, areas to avoid at night, common tourist mistakes, dress codes
HIDDEN GEMS: places not in guidebooks, viewpoints locals use, cafes with no English menu, local festivals

CARD SCHEMAS:

"overview" → { "city", "country", "description" (2-3 sentences like a local — mention specific neighbourhoods, not 'great city' but 'Shimokitazawa for vintage shops, Yanaka for old Edo atmosphere, Koenji for counterculture'), "vibes": [{"name","score"}] (vary scores realistically), "highlights": ["specific named things"], "best_time": "months with reason", "language": "language + useful phrases", "currency": "currency + rough GBP rate", "local_tip": "one specific insider tip", "neighbourhoods": [{"name","vibe","best_for"}], "avoid": "what tourists do that annoys locals" }

"itinerary" card activities MUST follow this format:
Each activity must be hyper-specific — never generic.

BAD (never do this):
{"time": "09:00", "activity": "Morning walk"}
{"time": "12:00", "activity": "Lunch at local restaurant"}
{"time": "14:00", "activity": "Visit museum"}

GOOD (always do this):
{
    "time": "08:30",
    "activity": "Walk the Alfama district — start at Portas do Sol viewpoint overlooking the Tagus river, wind down through Rua das Escolas Gerais past the blue azulejo tile facades. The streets are quiet before 10am — locals are heading to work.",
    "type": "morning",
    "duration": "90 mins",
    "cost": "Free",
    "tip": "Wear flat shoes — the cobblestones are brutal in heels or flip flops",
    "getting_there": "Tram 28 from Martim Moniz — €3 ticket, 15 mins"
},
{
    "time": "10:30",
    "activity": "Pastéis de Belém — the original custard tart bakery open since 1837 at Rua de Belém 84-92. Order 2 pastéis (€1.30 each) with a bica coffee (€0.80). Eat at the counter not the tourist tables at the back — fresher and faster.",
    "type": "food",
    "duration": "30 mins",
    "cost": "£3",
    "tip": "Go before 11am — queue gets 45 mins long after midday",
    "getting_there": "Walk 5 mins from Portas do Sol"
},
{
    "time": "11:00",
    "activity": "Mosteiro dos Jerónimos — UNESCO World Heritage monastery, finest example of Manueline architecture in Portugal. Free entry on Sunday mornings before 2pm. Spend time in the cloisters not just the church — the carved stonework is extraordinary.",
    "type": "afternoon",
    "duration": "75 mins",
    "cost": "€10 (free Sunday before 2pm)",
    "tip": "Audio guide is worth the €3 extra",
    "getting_there": "5 min walk from pastry shop"
}

Every itinerary card is: { "city", "country", "total_cost" (GBP), "days": [{ "day", "title" (creative like 'Temples, street food & Chao Phraya at sunset'), "cost", "activities": [ the hyper-specific activity objects above ], "local_food_tip": "specific dish + specific place", "transport_tip": "how to get around today", "avoid_today": "one thing to skip" }] }

ALSO for country queries — when the user asks about a country not a specific city — return this overview structure with suggested_cities:
{
  "type": "overview",
  "data": {
    "city": "Spain",
    "country": "Spain",
    "description": "...",
    "suggested_cities": [
      {
        "name": "Barcelona",
        "why": "Best for architecture, beach, and nightlife",
        "budget_per_day": 110,
        "best_for": ["couples", "friends", "solo"],
        "highlight": "Sagrada Familia, Gothic Quarter, Barceloneta beach"
      },
      {
        "name": "Seville",
        "why": "Most authentic Spanish culture, cheaper than Barcelona",
        "budget_per_day": 75,
        "best_for": ["solo", "culture lovers"],
        "highlight": "Flamenco, tapas, Alcázar palace"
      },
      {
        "name": "Madrid",
        "why": "Best food scene, world class museums, great nightlife",
        "budget_per_day": 95,
        "best_for": ["solo", "couples", "friends"],
        "highlight": "Prado museum, Retiro park, tapas in La Latina"
      },
      {
        "name": "Granada",
        "why": "Budget friendly, stunning Alhambra, free tapas with every drink",
        "budget_per_day": 55,
        "best_for": ["budget travellers", "solo"],
        "highlight": "Alhambra palace, Albaicín quarter, free tapas culture"
      }
    ],
    "budget_recommendation": "For under £500 total for 7 days including flights, Granada or Seville are best. Barcelona needs £700+ to do properly.",
    "vibes": [...],
    "highlights": [...],
    "best_time": "...",
    "local_tip": "..."
  }
}

"hotel" → { "name": "REAL hotel name", "neighbourhood": "exact neighbourhood", "neighbourhood_vibe": "what area feels like", "price_per_night" (GBP), "rating": 1-5, "stars": 1-5, "vibe": "boutique|budget|luxury|party|family|design", "why_locals_recommend_area": "mention nearby streets, metro, spots", "walk_to": "what's walkable", "amenities": [...], "insider_tip": "something guides miss", "booking_url": "https://www.booking.com/search.html?ss=HOTEL+NAME+CITY", "price_tier": "budget|mid|luxury" }

"food" → { "name": "REAL restaurant/stall name", "type": "restaurant|street_food|market|cafe|bar", "cuisine", "must_order": "exact dish in local language + English", "price_range": "$|$$|$$$|$$$$", "price_specific": "cost per person GBP", "neighbourhood", "address_hint": "near landmark/street", "best_time": "when to go + why", "order_like_local": "what locals order vs tourists", "avoid": "what NOT to order", "local_tip": "insider advice", "dietary": [] }

"flight" → { "route": "ORIGIN → DEST", "flights": [{ "airline", "flight_number", "departure_time", "arrival_time", "duration", "stops", "stop_city" (if stops>0), "price_gbp", "cabin", "baggage": "what's included", "book_url": "https://www.skyscanner.net/transport/flights/LON/IATA/", "google_flights_url": "https://www.google.com/travel/flights?q=flights+from+London+to+CITY" }], "cheapest_month", "airport_transfer": "how to get to city + cost", "baggage_tip" }

"budget" → { "city", "days", "currency": "GBP", "total", "daily_average", "breakdown": [{ "category", "amount", "note": "specific tip with amounts" }], "money_saving_tips": ["3 SPECIFIC hacks with amounts — e.g. 'Buy Oyster card, saves 40%'"], "splurge_on": "one thing worth extra", "save_on": "one thing tourists overpay for" }

"tips" → { "city", "categories": [ { "name": "scams to avoid", "tips": ["SPECIFIC named scam — how it works, how to avoid"] }, { "name": "transport hacks", "tips": ["specific hack with cost savings"] }, { "name": "free things to do", "tips": ["specific free activity + location"] }, { "name": "best photo spots", "tips": ["exact location, best time, why special"] }, { "name": "local etiquette", "tips": ["specific rule + consequence"] }, { "name": "what locals actually do", "tips": ["specific local behaviour tourists miss"] } ] }

"weather" → { "city", "month", "avg_temp_c", "feels_like", "rainfall_days", "humidity_percent", "conditions", "what_to_pack": [...], "local_tip", "best_activity_for_weather" }

"visa" → { "country", "visa_type", "duration", "cost", "documents": [...], "apply_url": null, "notes" }

"text" → { "message": "natural-language answer", "followup_question": "one short question to keep the conversation going" } — use for pure conversational turns (greetings, clarifications, short advice). Prefer this over cards when no list/itinerary is needed.

"list" → { "title": "...", "items": [{ "name": "bold head", "description": "short line", "best_for": "who/what", "tip": "one-line insider tip" }] } — use when the user asks for a short named list that isn't hotels/food/flights/tips (e.g., "3 best viewpoints", "top 5 neighbourhoods").

"comparison" → { "title": "...", "columns": ["Option", "Cost", "Vibe", "Best for"], "rows": [{ "Option": "...", "Cost": "\u00a3X", "Vibe": "...", "Best for": "..." }, ...], "verdict": "one-sentence recommendation" } — use for explicit comparison queries ("Prague vs Budapest", "flights vs train").

"itinerary_update" → { "summary": "what changed and why", "activities": [{ "time": "09:00", "activity": "...", "transport": "line + cost", "cost": "\u00a3X", "tip": "..." }] } — use when the user tweaks an existing itinerary ("add a museum after lunch", "make day 2 cheaper").

"place_info" → { "name", "category", "about", "image_keyword" (lowercase city or landmark slug), "quick_facts": [{ "label": "Opening", "value": "09:00-18:00" }, ...], "best_time", "local_tip", "nearby": ["..."], "cost": "\u00a3X", "map_url", "book_url" } — use for place-info queries ("tell me about the Alhambra", "tips for visiting the Colosseum"). Pair with a tips card when the user asks for tips about a place.

INTENT MAPPING:
- "plan X days in [city]" → itinerary + budget + tips (scams+transport) + 3 food cards
- "hotels in [city]" → 3 hotels: budget (<£60), mid (£60-150), special/design. REAL names, different neighbourhoods
- "where to eat" / "food in [city]" → 5 food cards: street food + local gem + splurge + breakfast + late night
- "flights to [city]" → 1 flight card with 3 options + real Skyscanner/Google Flights URLs
- "budget for [city]" → detailed budget with local hacks
- "tell me about [city]" → overview (with neighbourhoods) + 2 food cards + tips
- "hidden gems" / "like a local" → overview of non-tourist areas + 3 local food cards + tips
- "multi city trip to [country]" → 3 best cities, one itinerary per city, combined budget
- "day trip from [city]" → 3 nearby destinations with transport method + duration + cost
- "recommend" / "where should I go" → 3 overviews including 1 unexpected underrated destination
- "tips for [city]" → detailed tips with all 6 categories
- "weather in [city]" → weather + packing + best activities
- "neighbourhood guide" → overview focused on neighbourhood breakdown
- Pure conversational question ("what's the vibe", "is it safe") → 1 text card
- "top/best N X in Y" that isn't hotel/food/flight → 1 list card
- "X vs Y", "compare A and B" → 1 comparison card (+ verdict)
- "add/remove/swap/change" an activity in the current plan → 1 itinerary_update card
- "tell me about X" / "tips for X" / "visiting X" for a specific attraction → 1 place_info card (+ 1 tips card if they asked for tips)

GROUP DETECTION — always infer and reuse across turns:
- "solo", "by myself", "alone" → solo
- "with partner", "with my boyfriend/girlfriend/husband/wife", "with my date" → couple
- "with family", "with kids", "with my children" → family
- "with friends", "mates", "lads", "girls trip" → friends
Never ask the user twice; if they already said it, act on it.

BUDGET EXTRACTION — accept every phrasing the user throws at you:
- "under \u00a3500", "\u00a3500 budget", "500 pounds", "budget of 500", "max 500", "within 500" → 500 GBP
- "$500" → convert to GBP (\u00f70.79).
Do not confuse currency words with place names.

COUNTRY \u2192 CITY FALLBACK:
- spain: barcelona, madrid, seville
- italy: rome, florence, venice
- france: paris, lyon, nice
- greece: athens, santorini, mykonos
- uk: london, edinburgh, manchester
When a country is named (not a city), return an overview card with `suggested_cities` using at least these picks.

SUGGESTIONS — always 4 natural follow-ups that feel like conversation:
Good: "What's the street food scene like in [city]?", "Which neighbourhood should I stay in?", "Hidden gems most tourists miss?"
Bad: "Tell me about [city]" (too generic)

BUDGET TRIP PLANNING RULES:

When user provides a budget for a trip:

1. ANALYSE FIRST — before planning, calculate if budget is realistic:
   - Add up: flights estimate + hotel per night × days + food per day × days + activities
   - If total fits within budget → plan the full trip
   - If budget is too low → do NOT just plan anyway

2. IF BUDGET IS UNREALISTIC — never ignore it, instead offer TWO options:
   Option A: Reduced trip — same destination, fewer days that fit the budget
   Option B: Recommended budget — what the trip actually costs realistically

   Say exactly: "Your budget of £X covers Y days comfortably,
   not Z days. Here is your realistic Z-day plan.
   To do the full Z days you would need £X."

3. EVERY PLAN MUST BE BASED ON REAL LOCAL KNOWLEDGE:
   - Name actual neighbourhoods, not just the city
   - Name specific local restaurants with dish and price
   - Name exact transport (tube line, bus number, cost)
   - Name specific markets, viewpoints, streets
   - Include free activities to stretch the budget
   - Show daily cost breakdown so user sees where money goes

4. DAILY COST BREAKDOWN in every itinerary day:
   - Accommodation: £X (budget hostel / mid hotel / etc)
   - Food: £X (breakfast at X, lunch at X, dinner at X)
   - Transport: £X (day pass / specific line)
   - Activities: £X (free / paid — name them)
   - Day total: £X
   - Running total: £X of £BUDGET used

5. BUDGET TIERS — be realistic per city:
   Use actual daily costs. Example:
   London: budget £80, mid £150, luxury £250+
   Lisbon: budget £50, mid £90, luxury £160+
   Prague: budget £40, mid £75, luxury £140+
   Paris: budget £100, mid £160, luxury £280+
   Always adjust for the actual destination.

6. TIMELINE must be optimised:
   - Group nearby attractions on same day to save transport
   - Free attractions in morning, paid in afternoon
   - Suggest happy hours, early bird discounts, free museum days
   - Never plan more than 4 major spots per day — be realistic

QUALITY BAR — never go below this:
NEVER: "Visit a local temple" → ALWAYS name it. "Try local food" → ALWAYS name the dish. "Take public transport" → ALWAYS name the line. "Explore the old town" → ALWAYS name the neighbourhood. Generic hotel names. All vibes at 8/10.
ALWAYS: Write like someone who has been there. Mention what it feels like at 6am vs 6pm. Mention what locals think of tourists. Mention the one thing that surprises everyone.

All prices in GBP (£). Use your full training knowledge. You know every city. Act like it."""


# ── Wikipedia grounding for the AI Concierge ─────────────────────
# Countries and cities the concierge can ground via Wikipedia. Kept inline so
# the lookup is synchronous and predictable; add more entries as the product
# expands — no other code paths depend on this list.
_WIKI_COUNTRIES = [
    "france", "spain", "italy", "portugal", "greece", "germany", "japan",
    "thailand", "morocco", "turkey", "uk", "united kingdom", "scotland",
    "england", "wales", "ireland", "netherlands", "austria", "czech republic",
    "hungary", "croatia", "norway", "sweden", "denmark", "iceland", "finland",
    "poland", "switzerland", "belgium",
]

_WIKI_CITIES = {
    "london": "United Kingdom", "paris": "France", "rome": "Italy",
    "barcelona": "Spain", "madrid": "Spain", "lisbon": "Portugal",
    "amsterdam": "Netherlands", "berlin": "Germany", "vienna": "Austria",
    "prague": "Czech Republic", "budapest": "Hungary", "athens": "Greece",
    "istanbul": "Turkey", "edinburgh": "United Kingdom", "dublin": "Ireland",
    "copenhagen": "Denmark", "stockholm": "Sweden", "oslo": "Norway",
    "reykjavik": "Iceland", "marrakech": "Morocco", "florence": "Italy",
    "venice": "Italy", "milan": "Italy", "naples": "Italy",
    "seville": "Spain", "porto": "Portugal", "dubrovnik": "Croatia",
    "santorini": "Greece", "munich": "Germany", "warsaw": "Poland",
    "krakow": "Poland", "brussels": "Belgium", "zurich": "Switzerland",
    "geneva": "Switzerland", "nice": "France", "lyon": "France",
    "bordeaux": "France", "tokyo": "Japan", "bangkok": "Thailand",
    "bali": "Indonesia",
}


def _get_wikipedia_context(user_message):
    """
    Detect a city or country in the message and build a context block from
    Wikipedia so Claude can ground its response in real data.
    Returns an empty string if nothing applicable is found or the service
    is unavailable.
    """
    if not _WIKIPEDIA_AVAILABLE:
        return ""

    msg = (user_message or "").lower()
    context = ""

    detected_country = None
    for country in _WIKI_COUNTRIES:
        if re.search(rf"\b{re.escape(country)}\b", msg):
            detected_country = country.title()
            break

    detected_city = None
    detected_city_country = None
    for city, country in _WIKI_CITIES.items():
        if re.search(rf"\b{re.escape(city)}\b", msg):
            detected_city = city.title()
            detected_city_country = country
            break

    if detected_country and not detected_city:
        try:
            data = get_country_knowledge(detected_country)
            context += f"""
WIKIPEDIA KNOWLEDGE ABOUT {detected_country.upper()}:
Summary: {data.get('summary', '')}
Major cities to visit: {', '.join((data.get('major_cities') or [])[:6])}
Culture: {data.get('culture', '')}

Use this to suggest specific cities based on budget:
- Budget traveller: suggest cheaper cities
- Mid range: suggest popular cities
- Luxury: suggest premium destinations
Always recommend 3-4 specific cities with reasons.
"""
        except Exception as e:
            print(f"[Wikipedia country] {e}")

    if detected_city:
        try:
            data = get_city_knowledge(detected_city, detected_city_country or "")
            context += f"""
WIKIPEDIA KNOWLEDGE ABOUT {detected_city.upper()}:
Summary: {data.get('summary', '')}
Neighbourhoods: {', '.join((data.get('neighbourhoods') or [])[:5])}
Top attractions: {', '.join((data.get('attractions') or [])[:6])}
Food culture: {data.get('food_culture', '')}
Transport: {data.get('transport', '')}
History: {data.get('history', '')}

Use this real local knowledge in your itinerary.
Name specific streets, specific restaurants areas,
specific metro lines, specific local dishes.
"""
        except Exception as e:
            print(f"[Wikipedia city] {e}")

    return context


try:
    from services.amadeus_service import search_flights as _amadeus_flights
    from services.amadeus_service import search_hotels as _amadeus_hotels
    _AMADEUS_AVAILABLE = True
except Exception as _amadeus_err:
    print(f"[Chat] Amadeus service unavailable: {_amadeus_err}")
    _AMADEUS_AVAILABLE = False

    def _amadeus_flights(*a, **kw):
        return []

    def _amadeus_hotels(*a, **kw):
        return []


def _extract_origin_city(msg_lower):
    """Pull 'from <city>' out of the message, defaulting to London."""
    m = re.search(r"\bfrom\s+([a-z][a-z\s]{1,25}?)(?:\s+to\b|\s*$|\s*,|\s+on\b|\s+for\b|\s+in\b)", msg_lower)
    return m.group(1).strip().title() if m else "London"


def _extract_departure_date(msg):
    """Heuristic: grab an ISO date from the message, else default to +30 days.
    Amadeus needs a real future date or it returns nothing."""
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", msg)
    if m:
        return m.group(1)
    from datetime import datetime as _dt, timedelta
    return (_dt.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")


def _enrich_with_live_data(user_message):
    """
    Amadeus live enrichment. When the user's message mentions flights or
    hotels AND AMADEUS_API_KEY is set, we fetch 2-3 real offers per type and
    format them as a context block for Claude to ground its response.
    Silent no-op when keys missing or the API returns nothing — never fatal.
    """
    if not _AMADEUS_AVAILABLE:
        return ""
    if not (os.getenv("AMADEUS_API_KEY") and os.getenv("AMADEUS_API_SECRET")):
        return ""

    msg = (user_message or "").lower()
    locked = _resolve_locked_destination(user_message, msg, [])
    if not locked:
        return ""

    dest_city = locked.get("name")
    if not dest_city:
        return ""

    wants_flight = bool(re.search(r"\b(flight|flights|fly|airline|airfare)\b", msg))
    wants_hotel = bool(re.search(r"\b(hotel|hotels|stay|accommodation|hostel)\b", msg))

    # If the user didn't ask for either, don't spend API credits.
    if not (wants_flight or wants_hotel):
        return ""

    origin = _extract_origin_city(msg)
    depart_date = _extract_departure_date(msg)

    out = []
    if wants_flight:
        try:
            flights = _amadeus_flights(origin, dest_city, depart_date, adults=1) or []
            if flights:
                lines = [f"- {f.get('airline', '?')} {f.get('flight_number', '')}: "
                         f"{f.get('departure', {}).get('time', '')} → "
                         f"{f.get('arrival', {}).get('time', '')}, "
                         f"{f.get('duration', '')}, £{f.get('price_gbp', '?')}"
                         for f in flights[:3]]
                out.append(
                    "LIVE FLIGHTS from Amadeus (" + origin + " → " + dest_city +
                    " on " + depart_date + "):\n" + "\n".join(lines)
                )
        except Exception as e:
            print(f"[Amadeus flights] {e}")

    if wants_hotel:
        try:
            from datetime import datetime as _dt, timedelta
            checkin = depart_date
            checkout = (_dt.fromisoformat(depart_date) + timedelta(days=3)).strftime("%Y-%m-%d")
            hotels = _amadeus_hotels(dest_city, checkin, checkout, adults=1) or []
            if hotels:
                lines = [f"- {h.get('name', '?')} ({h.get('stars', '?')}★): "
                         f"£{h.get('price_per_night_gbp', '?')} /night, "
                         f"{h.get('neighbourhood') or h.get('area') or ''}"
                         for h in hotels[:3]]
                out.append(
                    "LIVE HOTELS from Amadeus (" + dest_city +
                    " " + checkin + " to " + checkout + "):\n" + "\n".join(lines)
                )
        except Exception as e:
            print(f"[Amadeus hotels] {e}")

    return "\n\n".join(out)


def _call_claude(user_message, history=None):
    """Call Claude Haiku API with optional prior conversation history and
    return parsed JSON. `history` is a list of {role, content} dicts from
    the current session so the assistant remembers prior turns."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    wiki_context = _get_wikipedia_context(user_message)
    live_context = _enrich_with_live_data(user_message)

    enriched_message = user_message
    if wiki_context or live_context:
        enriched_message = f"""{user_message}

[REAL DATA FROM EXTERNAL SOURCES - use all of this in your response]:
{wiki_context}
{live_context}

IMPORTANT: Use the real Wikipedia data above to give
specific street names, specific neighbourhood names,
specific local knowledge. Do not use generic descriptions.
"""

    # Build the messages array: prior conversation history + current turn.
    # Keep at most the last 10 turns (5 exchanges) to stay within context limits.
    messages = []
    if history:
        for turn in history[-10:]:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": enriched_message})

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    text = response.content[0].text.strip()

    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        text = json_match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting outermost {}
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end > start:
            return json.loads(text[start:end+1])
    except json.JSONDecodeError:
        pass

    # Fallback reply when Claude's JSON couldn't be parsed
    return {
        "reply": "I couldn't quite parse that — could you rephrase? Try asking about one specific city, trip, or topic at a time.",
        "cards": [],
        "suggestions": ["Hotels in Paris", "3 days in Bordeaux",
                        "Food in Lyon", "Things to do in Nice"]
    }


def _build_itinerary_card(d, num_days, cost_per_day, _accom_note, food_note):
    """Build an itinerary + its activities for one city."""
    city = d["name"]
    activities = d.get("sample_activities", [])
    days_list = []
    for i in range(num_days):
        if activities:
            offset = i % len(activities)
            act_slice = activities[offset:] + activities[:offset]
        else:
            act_slice = []
        days_list.append({
            "day": i + 1,
            "title": f"Day {i + 1} — Explore {city}",
            "cost": cost_per_day,
            "activities": [
                {"time": "09:00", "activity": act_slice[0] if act_slice else "Morning exploration"},
                {"time": "12:00", "activity": f"Lunch — {food_note}"},
                {"time": "14:00", "activity": act_slice[1] if len(act_slice) > 1 else "Afternoon sightseeing"},
                {"time": "19:00", "activity": "Dinner and evening leisure"},
            ],
        })
    return {"type": "itinerary", "data": {"city": city, "total_cost": round(cost_per_day * num_days), "days": days_list}}


def _build_budget_card(cities_data, _num_days_each, budget_mult, accom_note, food_note, origin="London"):
    """
    Build a combined budget card for one or more cities.
    cities_data: list of (dest_dict, num_days) tuples.
    """
    total_days = sum(nd for _, nd in cities_data)
    grand_total = 0
    breakdown = []

    # Accommodation
    accom = sum(round(d["avg_daily_cost_gbp"] * budget_mult * nd * 0.35) for d, nd in cities_data)
    breakdown.append({"category": "accommodation", "amount": accom, "note": accom_note})

    # Food
    food = sum(round(d["avg_daily_cost_gbp"] * budget_mult * nd * 0.25) for d, nd in cities_data)
    breakdown.append({"category": "food", "amount": food, "note": food_note})

    # Local transport
    transport = sum(round(d["avg_daily_cost_gbp"] * budget_mult * nd * 0.15) for d, nd in cities_data)
    breakdown.append({"category": "local transport", "amount": transport, "note": "Public transport & taxis"})

    # Activities
    acts = sum(round(d["avg_daily_cost_gbp"] * budget_mult * nd * 0.20) for d, nd in cities_data)
    breakdown.append({"category": "activities", "amount": acts, "note": "Entrance fees & tours"})

    # Flights estimate (origin→first city + inter-city + last city→origin)
    num_flights = len(cities_data) + 1  # outbound + inter-city legs + return
    avg_flight = round(150 * budget_mult)  # rough per-leg estimate
    flight_cost = avg_flight * num_flights
    breakdown.append({"category": "flights", "amount": flight_cost, "note": f"{num_flights} flight legs (est. £{avg_flight}/leg from {origin})"})

    grand_total = accom + food + transport + acts + flight_cost
    city_label = " + ".join(d["name"] for d, _ in cities_data)

    return {"type": "budget", "data": {
        "city": city_label, "days": total_days, "currency": "GBP", "total": grand_total,
        "breakdown": breakdown,
        "money_saving_tips": [
            "Book flights 6-8 weeks in advance for the best deals",
            "Eat where the locals eat — avoid restaurants right next to tourist attractions",
            "Use public transport day passes instead of single tickets",
        ],
    }}


def _build_hotel_cards(city, cost_per_day, base_cost, country=None):
    """
    Build 3 hotel cards — real hotel names from OpenStreetMap when the
    Overpass lookup succeeds, typed placeholders when it doesn't. `country`
    disambiguates cities like London (UK vs Ontario).
    """
    real = _osm_get_places(city, "hotel", limit=6, country=country) if _PLACES_AVAILABLE else []
    # Hostels make for a better "budget" tier than an invented cheap hotel.
    hostels = _osm_get_places(city, "hostel", limit=2, country=country) if _PLACES_AVAILABLE else []

    def _hotel_card(place, vibe, mult, rating, price_tier):
        price = round(cost_per_day * mult)
        name = place["name"]
        hood = place.get("neighbourhood") or place.get("address") or "City Centre"
        return {"type": "hotel", "data": {
            "name": name,
            "area": hood,
            "neighbourhood": hood,
            "price_per_night": price,
            "rating": rating,
            "vibe": vibe,
            "price_tier": price_tier,
            "amenities": ["Free WiFi", "Breakfast included", "Air conditioning"],
            "website": place.get("website") or "",
            "address": place.get("address") or "",
            "booking_url": (
                f"https://www.booking.com/search.html?ss={name.replace(' ', '+')}+{city.replace(' ', '+')}"
            ),
        }}

    cards = []
    tiers = [("Budget-Friendly", 0.5, 3.8, "budget"),
             ("Modern & Central", 0.9, 4.3, "mid"),
             ("Boutique & Luxury", 1.6, 4.7, "luxury")]
    # Prefer a hostel for the budget tier if we got one.
    picks = []
    if hostels:
        picks.append(hostels[0])
    # Then fill from regular hotels, avoiding duplicates with the hostel.
    seen = {(p.get("name") or "").lower() for p in picks}
    for h in real:
        key = (h.get("name") or "").lower()
        if key and key not in seen:
            picks.append(h); seen.add(key)
        if len(picks) >= 3:
            break

    if picks:
        for place, (vibe, mult, rating, tier) in zip(picks, tiers):
            cards.append(_hotel_card(place, vibe, mult, rating, tier))
        # If OSM gave us fewer than 3 results, fall back for the remainder.
        while len(cards) < 3:
            vibe, mult, rating, tier = tiers[len(cards)]
            price = round(cost_per_day * mult)
            cards.append({"type": "hotel", "data": {
                "name": f"{vibe.split(' &')[0]} Hotel {city}",
                "area": "City Centre",
                "price_per_night": price, "rating": rating, "vibe": vibe,
                "price_tier": tier,
                "amenities": ["Free WiFi", "Breakfast included", "Air conditioning"],
                "booking_url": None,
            }})
        return cards

    # No OSM data — original placeholder behaviour.
    for vibe, mult, rating, tier in tiers:
        price = round(cost_per_day * mult)
        cards.append({"type": "hotel", "data": {
            "name": f"{vibe.split(' &')[0]} Hotel {city}",
            "area": "City Centre", "price_per_night": price,
            "rating": rating, "vibe": vibe, "price_tier": tier,
            "amenities": ["Free WiFi", "Breakfast included", "Air conditioning"],
            "booking_url": None,
        }})
    return cards


def _build_food_cards(city, osm_category, food_label, country=None):
    """
    Build up to 5 food cards — real venue names from OpenStreetMap when
    available, typed placeholders otherwise. `osm_category` is passed to the
    places service (restaurant / cafe / pub / bar / street_food).
    """
    real = _osm_get_places(city, osm_category, limit=6, country=country) if _PLACES_AVAILABLE else []

    def _money(cuisine):
        return "$" if osm_category in ("street_food", "cafe") else "$$"

    if real:
        cards = []
        for place in real[:5]:
            cuisine = place.get("cuisine") or food_label
            cuisine = cuisine.replace("_", " ").replace(";", ", ").title()
            hood = place.get("neighbourhood") or place.get("address") or "City Centre"
            cards.append({"type": "food", "data": {
                "name": place["name"],
                "type": osm_category.replace("_", " "),
                "cuisine": cuisine,
                "must_try": f"Ask locally for today's house special",
                "price_range": _money(cuisine),
                "area": hood, "neighbourhood": hood,
                "description": (
                    f"Popular {food_label.lower()} in {hood or city}."
                    if hood else f"Popular {food_label.lower()} in {city}."
                ),
                "address": place.get("address") or "",
                "website": place.get("website") or "",
                "opening_hours": place.get("opening_hours") or "",
                "vibe": "Casual & lively",
            }})
        return cards

    # Placeholder fallback.
    food_types = [food_label, "Traditional", "Local Favourite", "Market", "Fine Dining"]
    cards = []
    for ft in food_types[:5]:
        cards.append({"type": "food", "data": {
            "name": f"{ft} Spot in {city}",
            "cuisine": ft, "must_try": f"Local {ft.lower()} speciality",
            "price_range": _money(ft),
            "area": "City Centre",
            "description": f"Popular {ft.lower()} destination among locals and travellers.",
            "vibe": "Casual & lively",
        }})
    return cards


def _fallback_response(user_message):
    """Generate a response from destinations.json when no API key is set."""
    msg = user_message.lower().strip()

    # ── Parse origin, destinations, and budget tier ──
    origin, parsed_dests, country_name = _parse_origin_destination(msg)
    budget_mult, tier_name, accom_note, food_note = _detect_budget_tier(msg)

    # ── Lock the user's destination (never replaced by later logic) ──
    locked_destination = _resolve_locked_destination(user_message, msg, parsed_dests)

    # ── Parse explicit budget and day count (no hard filtering — advisory only) ──
    user_budget_gbp, user_currency = _extract_user_budget(msg)
    day_match = re.search(r"(\d+)\s*days?", msg)
    num_days_in_msg = int(day_match.group(1)) if day_match else None

    def _finalize(result):
        """
        Enrich the response with budget-fit advisory (plus a reduced-cost plan
        when the budget is too low) and an offline-estimate notice for
        destinations outside the local dataset. Never removes the destination.
        """
        if locked_destination and user_budget_gbp is not None:
            base_days = num_days_in_msg or 5
            cost_per_day = round(locked_destination.get("avg_daily_cost_gbp", 100) * budget_mult)
            estimated_cost = cost_per_day * base_days
            status = _classify_budget_fit(estimated_cost, user_budget_gbp)
            if status:
                cards = result.setdefault("cards", [])
                city = locked_destination["name"]
                cards.append(_build_budget_conflict_card(
                    city, estimated_cost, user_budget_gbp,
                    base_days, cost_per_day, status,
                ))
                if status == "too_low":
                    reduced_cards, adj_days, adj_daily = _build_reduced_plan_cards(
                        locked_destination, user_budget_gbp, base_days,
                        accom_note, food_note, origin,
                    )
                    cards.extend(reduced_cards)
                    if adj_days < base_days:
                        cards.append(_build_skip_notice_card(
                            city,
                            f"days {adj_days + 1}-{base_days}",
                            f"Trip shortened from {base_days} to {adj_days} days so the "
                            f"plan fits £{user_budget_gbp} at ~£{adj_daily}/day.",
                        ))
        return _prepend_estimate_notice(result)

    # ── Zero-hallucination notice for destinations outside the local DB.
    # We still let intent routing build the correct card type (hotels / itinerary /
    # food / etc.), but prepend a transparent "offline-estimate" notice so the
    # user knows specific names and prices are indicative rather than sourced. ──
    def _prepend_estimate_notice(result):
        if not locked_destination or not locked_destination.get("_synthetic"):
            return result
        city = locked_destination["name"]
        notice = _build_skip_notice_card(
            city,
            "offline estimate",
            f"No live data for {city} — figures and names below are generic "
            "estimates. Enable the AI assistant (ANTHROPIC_API_KEY) for real-"
            "time details.",
        )
        result.setdefault("cards", []).insert(0, notice)
        return result

    # ── "where should I go" / recommend — only when NO destination was given ──
    if not locked_destination and any(kw in msg for kw in ["where should", "recommend", "suggest"]):
        import random
        picks = random.sample(DESTINATIONS, min(3, len(DESTINATIONS)))
        cards = []
        for d in picks:
            cards.append({
                "type": "overview",
                "data": {
                    "city": d["name"], "country": d["country"],
                    "description": f"{d['name']} is a fantastic destination known for {', '.join(d['tags'][:3])}. Average daily cost is around £{d['avg_daily_cost_gbp']}.",
                    "vibes": [{"name": t, "score": 8} for t in d["tags"][:4]],
                    "highlights": d.get("sample_activities", [])[:4],
                    "best_time": d.get("best_season", ""),
                    "language": "", "currency": "",
                },
            })
        return {
            "cards": cards,
            "suggestions": [f"Tell me about {picks[0]['name']}", f"Hotels in {picks[1]['name']}", f"Plan 3 days in {picks[0]['name']}"],
        }

    # ── Multi-city: country name resolved to 2-3 cities ──
    is_multi = len(parsed_dests) >= 2
    is_plan_intent = any(kw in msg for kw in ["plan", "itinerary", "days in", "trip", "tour", "visit", "travel", "multi"])

    if is_multi and is_plan_intent:
        # Extract total day count, split across cities
        day_match = re.search(r"(\d+)\s*days?", msg)
        total_days = int(day_match.group(1)) if day_match else len(parsed_dests) * 3
        days_per_city = max(2, total_days // len(parsed_dests))
        remainder = total_days - days_per_city * len(parsed_dests)

        cards = []
        cities_for_budget = []
        for i, d in enumerate(parsed_dests):
            nd = days_per_city + (remainder if i == 0 else 0)
            cost_per_day = round(d["avg_daily_cost_gbp"] * budget_mult)
            cards.append(_build_itinerary_card(d, nd, cost_per_day, accom_note, food_note))
            cities_for_budget.append((d, nd))

        # Combined budget card
        cards.append(_build_budget_card(cities_for_budget, days_per_city, budget_mult, accom_note, food_note, origin))

        country_label = country_name.title() if country_name else parsed_dests[0]["country"]
        first_city = parsed_dests[0]["name"]
        return _finalize({
            "cards": cards,
            "suggestions": [
                f"Hotels in {first_city}",
                f"Visa info for {country_label}",
                f"Food in {first_city}",
                f"Tips for {first_city}",
            ],
        })

    # ── Single destination: use the locked destination (never random-swap) ──
    # Only fall back to random suggestions when the user supplied NO destination.
    matched = locked_destination

    if not matched:
        import random
        picks = random.sample(DESTINATIONS, min(3, len(DESTINATIONS)))
        names = ", ".join(p["name"] for p in picks)
        return {
            "reply": (
                "I couldn't pin down a specific destination from that — could "
                f"you name a city or country? In the meantime, here are a few "
                f"ideas: {names}."
            ),
            "cards": [],
            "suggestions": [f"Tell me about {d['name']}" for d in picks],
        }

    d = matched
    city = d["name"]
    tags = d.get("tags", [])
    activities = d.get("sample_activities", [])
    base_cost = d.get("avg_daily_cost_gbp", 50)
    cost = round(base_cost * budget_mult)

    # ── Intent detection (single city) ──
    # Order matters: specific-type intents (hotels, food, flights, weather,
    # visa, tips, budget) are checked BEFORE the generic plan/days trigger
    # so a follow-up like "cafes in Paris" isn't rerouted to an itinerary
    # just because a stale "for 7 days" slipped into the message.

    if any(kw in msg for kw in ["hotel", "stay", "accommodation", "hostel"]):
        cards = _build_hotel_cards(city, cost, base_cost, country=d.get("country"))
        return _finalize({"cards": cards, "suggestions": [f"Food in {city}", f"Plan 3 days in {city}", f"Budget for {city}"]})

    if re.search(r"\b(streetfood|street\s+food|food|eat|eats|eating|restaurant|restaurants|cuisine|dining|cafe|cafes|pub|pubs|bar|bars|breakfast|lunch|dinner|brunch|snack|snacks|bakery|bakeries)\b", msg):
        # Pick the OSM category that best matches the user's phrasing so "pubs
        # in Dublin" returns pubs, "cafes in Paris" returns cafes, etc.
        if re.search(r"\b(streetfood|street\s+food)\b", msg):
            osm_category, food_label = "street_food", "Street Food"
        elif re.search(r"\b(cafe|cafes|coffee|breakfast|brunch|bakery|bakeries)\b", msg):
            osm_category, food_label = "cafe", "Cafe"
        elif re.search(r"\b(pub|pubs)\b", msg):
            osm_category, food_label = "pub", "Pub"
        elif re.search(r"\b(bar|bars)\b", msg):
            osm_category, food_label = "bar", "Bar"
        else:
            osm_category, food_label = "restaurant", "Restaurant"
        cards = _build_food_cards(city, osm_category, food_label, country=d.get("country"))
        return _finalize({"cards": cards, "suggestions": [f"Hotels in {city}", f"Plan 3 days in {city}", f"Budget for {city}"]})

    if "flight" in msg:
        cards = [{"type": "flight", "data": {"flights": [
            {"airline": "British Airways", "from": "LHR", "to": d.get("iata_code", "???"),
             "departure_time": "08:30", "arrival_time": "14:45", "duration": "6h 15m", "stops": 0, "price": round(cost * 8), "class": "Economy"},
            {"airline": "Emirates", "from": "LHR", "to": d.get("iata_code", "???"),
             "departure_time": "21:00", "arrival_time": "07:30+1", "duration": "10h 30m", "stops": 1, "price": round(cost * 6), "class": "Economy"},
            {"airline": "Ryanair", "from": "STN", "to": d.get("iata_code", "???"),
             "departure_time": "06:15", "arrival_time": "11:00", "duration": "4h 45m", "stops": 0, "price": round(cost * 3), "class": "Economy"},
        ]}}]
        return _finalize({"cards": cards, "suggestions": [f"Hotels in {city}", f"Plan 3 days in {city}", f"Visa info for {d['country']}"]})

    if "budget" in msg:
        num_days = num_days_in_msg if num_days_in_msg else 5
        cards = [_build_budget_card([(d, num_days)], num_days, budget_mult, accom_note, food_note, origin)]
        return _finalize({"cards": cards, "suggestions": [f"Plan {num_days} days in {city}", f"Hotels in {city}", f"Food in {city}"]})

    if any(kw in msg for kw in ["visa", "passport", "entry"]):
        visa = d.get("visa_requirements", {})
        gb_visa = visa.get("GB", "Check embassy website")
        visa_type = "Visa-free" if "free" in gb_visa.lower() else "E-visa" if "e-visa" in gb_visa.lower() else "Visa on arrival" if "arrival" in gb_visa.lower() else "Visa required"
        cards = [{"type": "visa", "data": {
            "country": d["country"], "visa_type": visa_type,
            "duration": gb_visa, "cost": "Varies",
            "documents": ["Valid passport (6+ months)", "Return ticket", "Proof of accommodation"],
            "apply_url": None, "notes": f"UK passport holder: {gb_visa}",
        }}]
        return _finalize({"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Hotels in {city}", f"Weather in {city}"]})

    if "weather" in msg or "climate" in msg:
        climate = d.get("climate", "temperate")
        temp_map = {"tropical": 30, "subtropical": 26, "arid": 33, "mediterranean": 22, "temperate": 18, "continental": 15, "oceanic": 16, "subarctic": 5}
        cards = [{"type": "weather", "data": {
            "city": city, "month": "Year-round average",
            "avg_temp_c": temp_map.get(climate, 20), "conditions": climate.capitalize(),
            "humidity": "60%", "rainfall": "Moderate",
            "what_to_pack": ["Comfortable shoes", "Sunscreen", "Light layers", "Rain jacket"],
        }}]
        return _finalize({"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Tips for {city}", f"Food in {city}"]})

    if re.search(r"\btips?\b", msg):
        cards = [{"type": "tips", "data": {
            "city": city,
            "categories": [
                {"name": "transport", "tips": ["Use public transport — it's cheap and reliable", "Download a local ride-hailing app"]},
                {"name": "money", "tips": [f"Budget about £{cost}/day for comfortable travel", "Carry some local currency for small vendors"]},
                {"name": "culture", "tips": ["Learn a few basic phrases in the local language", "Respect local customs and dress codes"]},
            ],
        }}]
        return _finalize({"cards": cards, "suggestions": [f"Food in {city}", f"Weather in {city}", f"Plan 3 days in {city}"]})

    # Plan / itinerary — checked AFTER specific intents so "cafes in X for
    # 7 days" keeps routing to cafes rather than to an itinerary.
    if (any(kw in msg for kw in ["plan", "itinerary", "days in", "trip to", "visit"])
            or re.search(r"\b\d+\s*days?\b", msg)):
        num_days = num_days_in_msg if num_days_in_msg else 3
        cards = [
            _build_itinerary_card(d, num_days, cost, accom_note, food_note),
            _build_budget_card([(d, num_days)], num_days, budget_mult, accom_note, food_note, origin),
        ]
        return _finalize({"cards": cards, "suggestions": [f"Hotels in {city}", f"Food in {city}", f"Visa info for {d['country']}"]})

    # Default: overview
    cards = [{"type": "overview", "data": {
        "city": city, "country": d["country"],
        "description": f"{city} is known for {', '.join(tags[:3])}. With an average daily cost of £{cost}, it's rated {d.get('avg_rating', 4.5)}/5 by travellers.",
        "vibes": [{"name": t, "score": 8} for t in tags[:5]],
        "highlights": activities[:5],
        "best_time": d.get("best_season", ""), "language": "", "currency": "",
    }}]
    return _finalize({"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Hotels in {city}", f"Food in {city}", f"Budget for {city}"]})


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle chat messages with destination locking, session-based follow-up
    memory, zero-hallucination fallback, output validation, and debug logging.
    Uses Claude API if available, otherwise falls back to local data. The
    frontend may optionally supply a session_id to enable follow-up memory.
    """
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())
    client_history = data.get("conversation_history") or []
    client_trip_context = data.get("trip_context") or None

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # 1. Load session memory (may be None if this is a fresh page load)
    session = _get_session(session_id)

    # 2. Apply follow-up context: inherit last destination / days when the
    #    current message omits them (e.g., "make it cheaper").
    effective_message = _apply_followup_context(message, session)

    # 3. Resolve the locked destination up front so we can validate later.
    lowered = effective_message.lower().strip()
    origin, parsed_dests, _country = _parse_origin_destination(lowered)
    locked_destination = _resolve_locked_destination(
        effective_message, lowered, parsed_dests
    )
    user_budget_gbp, _ccy = _extract_user_budget(lowered)
    day_match = re.search(r"(\d+)\s*days?", lowered)
    num_days = int(day_match.group(1)) if day_match else None
    budget_mult_tier, _tier_name, _a, _f = _detect_budget_tier(lowered)

    # 4. Generate response: Claude first (if configured, with conversation
    #    history for memory), else fallback.
    source = "fallback"
    result = None
    # Prefer the server-side conversation (canonical record) but fall back to
    # whatever the client sent if we have no stored session (e.g., server restart).
    history = (session or {}).get("conversation", []) if session else []
    if not history and isinstance(client_history, list):
        history = [
            h for h in client_history
            if isinstance(h, dict)
            and h.get("role") in ("user", "assistant")
            and h.get("content")
        ][-20:]
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_anthropic_api_key":
        try:
            result = _call_claude(effective_message, history=history)
            if result:
                source = "claude"
        except Exception as e:
            print(f"[Chat] Claude API error: {e}")

    if result is None:
        # Greetings get a friendly reply-only response (no random cards).
        if re.match(r"^\s*(hi|hello|hey|yo|hiya|howdy|greetings|good\s+(morning|afternoon|evening))\b", lowered):
            result = {
                "reply": "Hey! I'm TravelBuddy — I help plan trips, find hotels and restaurants, and share local tips. Where are you thinking of going?",
                "cards": [],
                "suggestions": [
                    "Plan 3 days in Tokyo", "Hotels in Paris",
                    "Where should I go?", "Best food in Bangkok",
                ],
            }
        # Off-topic (no destination + no travel keyword) → friendly refusal.
        elif locked_destination is None and not _looks_travel_related(lowered):
            result = {
                "reply": "I'm TravelBuddy — I can only help with travel. Ask me about destinations, hotels, food, flights, itineraries, or trip planning.",
                "cards": [],
                "suggestions": [
                    "Plan 3 days in Tokyo", "Hotels in Paris",
                    "Where should I go?", "Food in Bangkok",
                ],
            }
        else:
            result = _fallback_response(effective_message)

    # 5. Validate destination lock. If the output drifted to another city
    #    (common with Claude's non-EU redirect), force-correct to a
    #    zero-hallucination response centred on the locked destination.
    # Skip validation for country queries — they intentionally return cards
    # about several cities in the country, so the single "locked" city is
    # just the top pick, not the sole valid result.
    validation_passed = True
    validation_issues = []
    is_country_query = False
    if locked_destination:
        msg_for_country = effective_message.lower()
        for alias in COUNTRY_ALIASES:
            if re.search(rf"\b{re.escape(alias)}\b", msg_for_country):
                is_country_query = True
                break
    if locked_destination and not is_country_query:
        validation_passed, validation_issues = _validate_destination_lock(
            result, locked_destination
        )
        if not validation_passed:
            result = _force_correct_response(
                locked_destination,
                user_budget_gbp=user_budget_gbp,
                num_days=num_days,
                note="Validation corrected an off-topic response.",
            )

    # 6. Derive budget-conflict flag for the log line.
    budget_conflict = False
    if user_budget_gbp is not None and locked_destination:
        base_days = num_days or 5
        est = round(locked_destination.get("avg_daily_cost_gbp", 100) * budget_mult_tier) * base_days
        if _classify_budget_fit(est, user_budget_gbp) == "too_low":
            budget_conflict = True

    # 7. Emit the debug log line required by the spec.
    final_city = None
    for card in result.get("cards", []) or []:
        c = (card.get("data") or {}).get("city")
        if c:
            final_city = c
            break
    _log_chat_debug(
        requested_destination=locked_destination.get("name") if locked_destination else None,
        final_destination=final_city,
        budget_conflict=budget_conflict,
        validation_passed=validation_passed,
        issues=validation_issues if validation_issues else None,
        session_id=session_id,
        source=source,
    )

    # 8. Persist session memory for subsequent follow-ups.
    _save_session(
        session_id, message, result, locked_destination,
        user_budget_gbp, num_days, budget_mult_tier,
    )

    # 9. Echo session_id and trip_context so the frontend can maintain state.
    result["session_id"] = session_id
    trip_context = dict(client_trip_context) if isinstance(client_trip_context, dict) else {}
    if locked_destination:
        trip_context["destination"] = locked_destination.get("name") or trip_context.get("destination")
        if locked_destination.get("country"):
            trip_context["country"] = locked_destination["country"]
    if num_days:
        trip_context["days"] = num_days
    if user_budget_gbp is not None:
        trip_context["budget"] = user_budget_gbp
    # Simple group inference from the last message (complements Claude-side inference)
    msg_lower = message.lower()
    group_guess = None
    if re.search(r"\b(with\s+family|with\s+kids|with\s+my\s+children)\b", msg_lower):
        group_guess = "family"
    elif re.search(r"\b(with\s+partner|with\s+my\s+(boyfriend|girlfriend|husband|wife)|with\s+my\s+date|couple)\b", msg_lower):
        group_guess = "couple"
    elif re.search(r"\b(with\s+friends|with\s+mates|lads|girls\s+trip)\b", msg_lower):
        group_guess = "friends"
    elif re.search(r"\b(solo|by\s+myself|alone)\b", msg_lower):
        group_guess = "solo"
    if group_guess:
        trip_context["group"] = group_guess
    if trip_context:
        result["trip_context"] = trip_context
    return jsonify(result)
