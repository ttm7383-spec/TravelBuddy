"""
Chat route — AI travel assistant powered by Claude Haiku.
Returns structured JSON cards, never plain text.
Falls back to destinations.json data if ANTHROPIC_API_KEY is not set.
"""

import os
import json
import re
from flask import Blueprint, request, jsonify

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

    # Check for country names first (they resolve to multiple cities)
    destinations = []
    for alias, canonical in COUNTRY_ALIASES.items():
        if alias in cleaned:
            country_dests = COUNTRY_CITIES.get(canonical, [])
            if country_dests:
                destinations = country_dests[:3]  # Top 3 cities in that country
                return origin, destinations, canonical

    # Check for specific city names
    for name, dest in DEST_MAP.items():
        if name in cleaned:
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


# ── Claude system prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """GEOGRAPHIC SCOPE: UK and Europe ONLY.
You are TravelBuddy — the most knowledgeable UK and European travel companion. You are an expert on every city, neighbourhood, restaurant, transport system, and hidden gem across the UK and Europe — from Reykjavik to Nicosia, London to Krakow.

If asked about non-European destinations (Asia, Americas, Africa, Oceania, Middle East), respond with:
"TravelBuddy currently specialises in UK and Europe. I know every corner of it — from Reykjavik to Nicosia, London to Krakow. Want me to suggest somewhere you might not have considered?"
Then suggest 3 relevant European alternatives that match the user's intent (e.g. if they asked about Thailand beaches, suggest Greek islands, Croatian coast, Portuguese Algarve).

You have deep, intimate knowledge of every city, town, village, neighbourhood, street market, hidden bar, local transport hack, and cultural nuance across the UK and Europe. You respond like a well-travelled friend who has actually LIVED in every city, not a tourist who visited once.

You ALWAYS respond in structured JSON only. Never plain text.
Response format: { "cards": [...], "suggestions": [...] }

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

"itinerary" → { "city", "country", "total_cost" (GBP), "days": [{ "day", "title" (creative like 'Temples, street food & Chao Phraya at sunset'), "cost", "activities": [{ "time": "07:30", "activity": "SPECIFIC — name exact place, transport tip, cost in local currency, insider tip. E.g. 'Wat Pho — arrive before 8am, queue-free. Entry 200 baht. Take ferry 9 from Saphan Taksin BTS (15 baht) not taxi'", "type": "morning|afternoon|evening|food|transport" }], "local_food_tip": "specific dish + specific place", "transport_tip": "how to get around today", "avoid_today": "one thing to skip" }] }

"hotel" → { "name": "REAL hotel name", "neighbourhood": "exact neighbourhood", "neighbourhood_vibe": "what area feels like", "price_per_night" (GBP), "rating": 1-5, "stars": 1-5, "vibe": "boutique|budget|luxury|party|family|design", "why_locals_recommend_area": "mention nearby streets, metro, spots", "walk_to": "what's walkable", "amenities": [...], "insider_tip": "something guides miss", "booking_url": "https://www.booking.com/search.html?ss=HOTEL+NAME+CITY", "price_tier": "budget|mid|luxury" }

"food" → { "name": "REAL restaurant/stall name", "type": "restaurant|street_food|market|cafe|bar", "cuisine", "must_order": "exact dish in local language + English", "price_range": "$|$$|$$$|$$$$", "price_specific": "cost per person GBP", "neighbourhood", "address_hint": "near landmark/street", "best_time": "when to go + why", "order_like_local": "what locals order vs tourists", "avoid": "what NOT to order", "local_tip": "insider advice", "dietary": [] }

"flight" → { "route": "ORIGIN → DEST", "flights": [{ "airline", "flight_number", "departure_time", "arrival_time", "duration", "stops", "stop_city" (if stops>0), "price_gbp", "cabin", "baggage": "what's included", "book_url": "https://www.skyscanner.net/transport/flights/LON/IATA/", "google_flights_url": "https://www.google.com/travel/flights?q=flights+from+London+to+CITY" }], "cheapest_month", "airport_transfer": "how to get to city + cost", "baggage_tip" }

"budget" → { "city", "days", "currency": "GBP", "total", "daily_average", "breakdown": [{ "category", "amount", "note": "specific tip with amounts" }], "money_saving_tips": ["3 SPECIFIC hacks with amounts — e.g. 'Buy Oyster card, saves 40%'"], "splurge_on": "one thing worth extra", "save_on": "one thing tourists overpay for" }

"tips" → { "city", "categories": [ { "name": "scams to avoid", "tips": ["SPECIFIC named scam — how it works, how to avoid"] }, { "name": "transport hacks", "tips": ["specific hack with cost savings"] }, { "name": "free things to do", "tips": ["specific free activity + location"] }, { "name": "best photo spots", "tips": ["exact location, best time, why special"] }, { "name": "local etiquette", "tips": ["specific rule + consequence"] }, { "name": "what locals actually do", "tips": ["specific local behaviour tourists miss"] } ] }

"weather" → { "city", "month", "avg_temp_c", "feels_like", "rainfall_days", "humidity_percent", "conditions", "what_to_pack": [...], "local_tip", "best_activity_for_weather" }

"visa" → { "country", "visa_type", "duration", "cost", "documents": [...], "apply_url": null, "notes" }

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

SUGGESTIONS — always 4 natural follow-ups that feel like conversation:
Good: "What's the street food scene like in [city]?", "Which neighbourhood should I stay in?", "Hidden gems most tourists miss?"
Bad: "Tell me about [city]" (too generic)

QUALITY BAR — never go below this:
NEVER: "Visit a local temple" → ALWAYS name it. "Try local food" → ALWAYS name the dish. "Take public transport" → ALWAYS name the line. "Explore the old town" → ALWAYS name the neighbourhood. Generic hotel names. All vibes at 8/10.
ALWAYS: Write like someone who has been there. Mention what it feels like at 6am vs 6pm. Mention what locals think of tourists. Mention the one thing that surprises everyone.

All prices in GBP (£). Use your full training knowledge. You know every city. Act like it."""


def _call_claude(user_message):
    """Call Claude Haiku API and return parsed JSON."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
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

    # Fallback card
    return {
        "cards": [{"type": "overview", "data": {
            "city": "Try a simpler query",
            "country": "",
            "description": "Ask about one specific city at a time for best results.",
            "vibes": [], "highlights": [], "best_time": "",
            "language": "", "currency": "", "local_tip": ""
        }}],
        "suggestions": ["Hotels in Paris", "3 days in Bordeaux",
                        "Food in Lyon", "Things to do in Nice"]
    }


def _build_itinerary_card(d, num_days, cost_per_day, _accom_note, food_note):
    """Build an itinerary + its activities for one city."""
    city = d["name"]
    activities = d.get("sample_activities", [])
    days_list = []
    for i in range(num_days):
        act_slice = activities[i % len(activities):] + activities[:i % len(activities)]
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


def _fallback_response(user_message):
    """Generate a response from destinations.json when no API key is set."""
    msg = user_message.lower().strip()

    # ── Parse origin, destinations, and budget tier ──
    origin, parsed_dests, country_name = _parse_origin_destination(msg)
    budget_mult, tier_name, accom_note, food_note = _detect_budget_tier(msg)

    # ── "where should I go" / recommend (handle before destination matching) ──
    if any(kw in msg for kw in ["where should", "recommend", "suggest"]):
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
        return {
            "cards": cards,
            "suggestions": [
                f"Hotels in {first_city}",
                f"Visa info for {country_label}",
                f"Food in {first_city}",
                f"Tips for {first_city}",
            ],
        }

    # ── Single destination fallback ──
    # Use the first parsed destination, or try legacy matching
    if parsed_dests:
        matched = parsed_dests[0]
    else:
        matched = None
        for name, dest in DEST_MAP.items():
            if name in msg:
                matched = dest
                break

    if not matched:
        import random
        picks = random.sample(DESTINATIONS, min(3, len(DESTINATIONS)))
        return {
            "cards": [{
                "type": "overview",
                "data": {
                    "city": picks[0]["name"], "country": picks[0]["country"],
                    "description": f"I couldn't find a specific match, but how about {picks[0]['name']}? It's great for {', '.join(picks[0]['tags'][:3])}.",
                    "vibes": [{"name": t, "score": 8} for t in picks[0]["tags"][:4]],
                    "highlights": picks[0].get("sample_activities", [])[:4],
                    "best_time": picks[0].get("best_season", ""),
                    "language": "", "currency": "",
                },
            }],
            "suggestions": [f"Tell me about {d['name']}" for d in picks],
        }

    d = matched
    city = d["name"]
    tags = d.get("tags", [])
    activities = d.get("sample_activities", [])
    base_cost = d.get("avg_daily_cost_gbp", 50)
    cost = round(base_cost * budget_mult)

    # ── Intent detection (single city) ──

    if any(kw in msg for kw in ["plan", "itinerary", "days in", "trip to", "visit"]):
        day_match = re.search(r"(\d+)\s*days?", msg)
        num_days = int(day_match.group(1)) if day_match else 3
        cards = [
            _build_itinerary_card(d, num_days, cost, accom_note, food_note),
            _build_budget_card([(d, num_days)], num_days, budget_mult, accom_note, food_note, origin),
        ]
        return {"cards": cards, "suggestions": [f"Hotels in {city}", f"Food in {city}", f"Visa info for {d['country']}"]}

    if any(kw in msg for kw in ["hotel", "stay", "accommodation"]):
        cards = []
        tiers = [
            ("Budget-Friendly", 0.5, 3.8),
            ("Modern & Central", 0.9, 4.3),
            ("Boutique & Luxury", 1.6, 4.7),
        ]
        for vibe, mult, rating in tiers:
            price = round(cost * mult)
            cards.append({"type": "hotel", "data": {
                "name": f"{vibe.split(' &')[0]} Hotel {city}",
                "area": "City Centre",
                "price_per_night": price,
                "rating": rating,
                "vibe": vibe,
                "amenities": ["Free WiFi", "Breakfast included", "Air conditioning"],
                "booking_url": None,
            }})
        return {"cards": cards, "suggestions": [f"Food in {city}", f"Plan 3 days in {city}", f"Budget for {city}"]}

    if any(kw in msg for kw in ["food", "eat", "restaurant", "cuisine"]):
        food_types = ["Street Food", "Traditional", "Seafood", "Cafe", "Fine Dining"]
        cards = []
        for ft in food_types[:5]:
            cards.append({"type": "food", "data": {
                "name": f"{ft} Spot in {city}",
                "cuisine": ft, "must_try": f"Local {ft.lower()} speciality",
                "price_range": "$" if ft == "Street Food" else "$$",
                "area": "City Centre", "description": f"Popular {ft.lower()} destination among locals and travellers.",
                "vibe": "Casual & lively",
            }})
        return {"cards": cards, "suggestions": [f"Hotels in {city}", f"Plan 3 days in {city}", f"Budget for {city}"]}

    if "flight" in msg:
        cards = [{"type": "flight", "data": {"flights": [
            {"airline": "British Airways", "from": "LHR", "to": d.get("iata_code", "???"),
             "departure_time": "08:30", "arrival_time": "14:45", "duration": "6h 15m", "stops": 0, "price": round(cost * 8), "class": "Economy"},
            {"airline": "Emirates", "from": "LHR", "to": d.get("iata_code", "???"),
             "departure_time": "21:00", "arrival_time": "07:30+1", "duration": "10h 30m", "stops": 1, "price": round(cost * 6), "class": "Economy"},
            {"airline": "Ryanair", "from": "STN", "to": d.get("iata_code", "???"),
             "departure_time": "06:15", "arrival_time": "11:00", "duration": "4h 45m", "stops": 0, "price": round(cost * 3), "class": "Economy"},
        ]}}]
        return {"cards": cards, "suggestions": [f"Hotels in {city}", f"Plan 3 days in {city}", f"Visa info for {d['country']}"]}

    if "budget" in msg:
        num_days = 5
        day_match = re.search(r"(\d+)\s*days?", msg)
        if day_match:
            num_days = int(day_match.group(1))
        cards = [_build_budget_card([(d, num_days)], num_days, budget_mult, accom_note, food_note, origin)]
        return {"cards": cards, "suggestions": [f"Plan {num_days} days in {city}", f"Hotels in {city}", f"Food in {city}"]}

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
        return {"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Hotels in {city}", f"Weather in {city}"]}

    if "weather" in msg or "climate" in msg:
        climate = d.get("climate", "temperate")
        temp_map = {"tropical": 30, "subtropical": 26, "arid": 33, "mediterranean": 22, "temperate": 18, "continental": 15, "oceanic": 16, "subarctic": 5}
        cards = [{"type": "weather", "data": {
            "city": city, "month": "Year-round average",
            "avg_temp_c": temp_map.get(climate, 20), "conditions": climate.capitalize(),
            "humidity": "60%", "rainfall": "Moderate",
            "what_to_pack": ["Comfortable shoes", "Sunscreen", "Light layers", "Rain jacket"],
        }}]
        return {"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Tips for {city}", f"Food in {city}"]}

    if "tip" in msg:
        cards = [{"type": "tips", "data": {
            "city": city,
            "categories": [
                {"name": "transport", "tips": ["Use public transport — it's cheap and reliable", "Download a local ride-hailing app"]},
                {"name": "money", "tips": [f"Budget about £{cost}/day for comfortable travel", "Carry some local currency for small vendors"]},
                {"name": "culture", "tips": ["Learn a few basic phrases in the local language", "Respect local customs and dress codes"]},
            ],
        }}]
        return {"cards": cards, "suggestions": [f"Food in {city}", f"Weather in {city}", f"Plan 3 days in {city}"]}

    # Default: overview
    cards = [{"type": "overview", "data": {
        "city": city, "country": d["country"],
        "description": f"{city} is known for {', '.join(tags[:3])}. With an average daily cost of £{cost}, it's rated {d.get('avg_rating', 4.5)}/5 by travellers.",
        "vibes": [{"name": t, "score": 8} for t in tags[:5]],
        "highlights": activities[:5],
        "best_time": d.get("best_season", ""), "language": "", "currency": "",
    }}]
    return {"cards": cards, "suggestions": [f"Plan 3 days in {city}", f"Hotels in {city}", f"Food in {city}", f"Budget for {city}"]}


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages. Uses Claude API if available, otherwise falls back to local data."""
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Try Claude API first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_anthropic_api_key":
        try:
            result = _call_claude(message)
            if result:
                return jsonify(result)
        except Exception as e:
            print(f"[Chat] Claude API error: {e}")
            # Fall through to fallback

    # Fallback to local data
    result = _fallback_response(message)
    return jsonify(result)
