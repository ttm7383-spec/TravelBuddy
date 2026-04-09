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

# ── Claude system prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """You are TravelBuddy AI, a travel assistant that ONLY responds with structured JSON.
You can answer about ANY city on Earth using your knowledge.

RULES:
1. NEVER respond with plain text or paragraphs. ALWAYS return valid JSON.
2. Your response must be a JSON object with two keys: "cards" (array) and "suggestions" (array of 3-4 follow-up questions).
3. Each card in "cards" has "type" and "data" keys.

CARD TYPES AND THEIR DATA SCHEMAS:

"overview" → { "city", "country", "description" (2-3 sentences), "vibes": [{"name","score"}] (score 1-10), "highlights": [...], "best_time", "language", "currency" }

"itinerary" → { "city", "total_cost" (number, GBP), "days": [{ "day", "title", "cost" (number), "activities": [{"time","activity"}] }] }

"hotel" → { "name", "area", "price_per_night" (number, GBP), "rating" (1-5), "vibe" (string), "amenities": [...], "booking_url": null }

"food" → { "name", "cuisine", "must_try", "price_range" ("$"-"$$$$"), "area", "description", "vibe" }

"flight" → { "flights": [{ "airline", "from", "to", "departure_time", "arrival_time", "duration", "stops" (number), "price" (number, GBP), "class" }] }

"visa" → { "country", "visa_type" ("Visa-free"/"Visa on arrival"/"E-visa"/"Visa required"), "duration", "cost", "documents": [...], "apply_url": null, "notes" }

"budget" → { "city", "days" (number), "currency": "GBP", "total" (number), "breakdown": [{ "category", "amount" (number), "note" }] }

"tips" → { "city", "categories": [{ "name", "tips": [...] }] }

"weather" → { "city", "month", "avg_temp_c" (number), "conditions", "humidity", "rainfall", "what_to_pack": [...] }

INTENT MAPPING:
- "plan X days in [city]" → itinerary + budget + visa cards
- "hotels in [city]" → 3 hotel cards
- "food in [city]" / "eat in [city]" / "restaurants in [city]" → 5 food cards
- "flights to [city]" → 1 flight card (with 3 flight options inside)
- "budget for [city]" → 1 budget card
- "tell me about [city]" / "what's [city] like" → overview + weather + 2 food cards
- "where should I go" / "recommend" → 3 overview cards of different destinations
- "visa for [city]" / "visa info [country]" → 1 visa card
- "tips for [city]" → 1 tips card
- "weather in [city]" → 1 weather card

Always use GBP (£) for all prices. Generate realistic, accurate data from your knowledge.
For suggestions, offer natural follow-ups like "Hotels in [city]", "Food in [city]", "Plan 3 days in [city]"."""


def _call_claude(user_message):
    """Call Claude Haiku API and return parsed JSON."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        text = json_match.group(1).strip()

    return json.loads(text)


def _fallback_response(user_message):
    """Generate a response from destinations.json when no API key is set."""
    msg = user_message.lower().strip()

    # Find matching destination
    matched = None
    for name, dest in DEST_MAP.items():
        if name in msg:
            matched = dest
            break

    # "where should I go" / recommend
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

    if not matched:
        # If no match, pick a random destination and suggest it
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
    cost = d.get("avg_daily_cost_gbp", 50)

    # Intent detection
    if any(kw in msg for kw in ["plan", "itinerary", "days in"]):
        # Extract day count
        day_match = re.search(r"(\d+)\s*days?", msg)
        num_days = int(day_match.group(1)) if day_match else 3
        days_list = []
        for i in range(num_days):
            act_slice = activities[i % len(activities):] + activities[:i % len(activities)]
            days_list.append({
                "day": i + 1,
                "title": f"Day {i + 1} — Explore {city}",
                "cost": cost,
                "activities": [
                    {"time": "09:00", "activity": act_slice[0] if act_slice else "Morning exploration"},
                    {"time": "12:00", "activity": "Lunch at local restaurant"},
                    {"time": "14:00", "activity": act_slice[1] if len(act_slice) > 1 else "Afternoon sightseeing"},
                    {"time": "19:00", "activity": "Dinner and evening leisure"},
                ],
            })
        cards = [
            {"type": "itinerary", "data": {"city": city, "total_cost": cost * num_days, "days": days_list}},
            {"type": "budget", "data": {
                "city": city, "days": num_days, "currency": "GBP", "total": cost * num_days,
                "breakdown": [
                    {"category": "accommodation", "amount": round(cost * num_days * 0.35), "note": "Mid-range hotel"},
                    {"category": "food", "amount": round(cost * num_days * 0.25), "note": "Mix of local & restaurants"},
                    {"category": "transport", "amount": round(cost * num_days * 0.15), "note": "Public transport"},
                    {"category": "activities", "amount": round(cost * num_days * 0.20), "note": "Entrance fees & tours"},
                    {"category": "other", "amount": round(cost * num_days * 0.05), "note": "Tips, souvenirs"},
                ],
            }},
        ]
        return {"cards": cards, "suggestions": [f"Hotels in {city}", f"Food in {city}", f"Visa info for {d['country']}"]}

    if any(kw in msg for kw in ["hotel", "stay", "accommodation"]):
        cards = []
        vibes = ["Boutique & Charming", "Modern & Central", "Budget-Friendly"]
        for i, vibe in enumerate(vibes):
            price = round(cost * (0.6 + i * 0.3))
            cards.append({"type": "hotel", "data": {
                "name": f"{vibe.split(' &')[0]} Hotel {city}",
                "area": "City Centre",
                "price_per_night": price,
                "rating": round(4.0 + i * 0.3, 1),
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
        total = cost * num_days
        cards = [{"type": "budget", "data": {
            "city": city, "days": num_days, "currency": "GBP", "total": total,
            "breakdown": [
                {"category": "accommodation", "amount": round(total * 0.35), "note": "Mid-range hotel"},
                {"category": "food", "amount": round(total * 0.25), "note": "Mix of local & restaurants"},
                {"category": "transport", "amount": round(total * 0.15), "note": "Local transport"},
                {"category": "activities", "amount": round(total * 0.20), "note": "Tours & attractions"},
                {"category": "other", "amount": round(total * 0.05), "note": "Miscellaneous"},
            ],
        }}]
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
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": True, "message": "Invalid or missing JSON body"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": True, "message": "Message is required"}), 400

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

    except Exception as e:
        print(f"[Chat] Unexpected error: {e}")
        return jsonify({"error": True, "message": str(e)}), 500


@chat_bp.errorhandler(404)
def chat_not_found(e):
    return jsonify({"error": True, "message": "Chat endpoint not found"}), 404


@chat_bp.errorhandler(405)
def chat_method_not_allowed(e):
    return jsonify({"error": True, "message": "Method not allowed — use POST"}), 405


@chat_bp.errorhandler(500)
def chat_internal_error(e):
    return jsonify({"error": True, "message": "Internal server error"}), 500
