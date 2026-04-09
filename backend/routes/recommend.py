"""
TravelBuddy - Recommendation API Route
========================================
POST /api/recommend

Accepts user preferences and returns personalised destination recommendations
using the two-layer recommendation engine (rule-based + TF-IDF content scoring).
"""

from flask import Blueprint, request, jsonify
from recommender.engine import get_recommendations, DESTINATIONS
from firebase_config import verify_token, get_user_profile

recommend_bp = Blueprint("recommend", __name__)


@recommend_bp.route("/api/destinations", methods=["GET"])
def list_destinations():
    """Return all destinations (id, name, country, tags, cost) for the city picker."""
    simple = []
    for d in DESTINATIONS:
        simple.append({
            "id": d["id"],
            "name": d["name"],
            "country": d["country"],
            "avg_daily_cost_gbp": d["avg_daily_cost_gbp"],
            "tags": d["tags"],
            "climate": d["climate"],
        })
    return jsonify({"destinations": simple}), 200


@recommend_bp.route("/api/recommend", methods=["POST"])
def recommend():
    """
    Get personalised destination recommendations.

    Request Body (JSON):
    {
        "user_id": "optional-uid",
        "departure_city": "London",
        "travel_dates": {"start": "2026-04-15", "end": "2026-04-22"},
        "budget_level": "low" | "medium" | "high",
        "style_preferences": ["beach", "culture", ...],
        "group_type": "solo" | "couple" | "family" | "friends"
    }

    Response (JSON):
    {
        "recommendations": [
            { ...destination_fields, "match_score": 0.72, "match_reason": "..." },
            ...
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Extract required fields with defaults
        budget_level = data.get("budget_level", "medium")
        style_preferences = data.get("style_preferences", [])
        group_type = data.get("group_type", "solo")

        # Validate budget_level
        if budget_level not in ("low", "medium", "high"):
            return jsonify({
                "error": f"Invalid budget_level: '{budget_level}'. Must be 'low', 'medium', or 'high'."
            }), 400

        # Validate group_type
        if group_type not in ("solo", "couple", "family", "friends"):
            return jsonify({
                "error": f"Invalid group_type: '{group_type}'. Must be 'solo', 'couple', 'family', or 'friends'."
            }), 400

        # Extract passport country for visa scoring
        passport_country = data.get("passport_country", None)

        # Try to get travel history and passport from user's Firebase profile
        travel_history = []
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            decoded = verify_token(token)
            if decoded:
                profile = get_user_profile(decoded["uid"])
                if profile:
                    travel_history = profile.get("travel_history", [])
                    if not passport_country:
                        passport_country = profile.get("passport_country")

        # Run the recommendation engine
        recommendations = get_recommendations(
            budget_level=budget_level,
            style_preferences=style_preferences,
            group_type=group_type,
            travel_history=travel_history,
            passport_country=passport_country,
            top_n=5
        )

        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        return jsonify({"error": f"Recommendation failed: {str(e)}"}), 500
