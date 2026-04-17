"""
TravelBuddy - Recommendation API Route
========================================
POST /api/recommend

Accepts user preferences and returns personalised destination recommendations
using the two-layer recommendation engine (rule-based + TF-IDF content scoring).
"""

from flask import Blueprint, request, jsonify
from recommender.engine import (
    get_recommendations,
    get_similar_destinations,
    get_trending_destinations,
    get_svd_recommendations,
    evaluate_recommendations,
    DESTINATIONS,
)
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
            "continent": d.get("continent", "Unknown"),
            "avg_daily_cost_gbp": d["avg_daily_cost_gbp"],
            "budget_level": d.get("budget_level", "medium"),
            "tags": d["tags"],
            "climate": d["climate"],
            "popularity_score": d.get("popularity_score", 50),
            "safety_rating": d.get("safety_rating", 3),
            "highlights": d.get("highlights", ""),
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

        # Validate style_preferences
        if not isinstance(style_preferences, list):
            return jsonify({"error": "style_preferences must be an array"}), 400
        if len(style_preferences) > 20:
            return jsonify({"error": "Maximum 20 style preferences allowed"}), 400

        # Sanitise — keep only known valid styles, ignore unknown ones
        VALID_STYLES = {
            "beach", "adventure", "culture", "city", "nature", "nightlife",
            "food", "history", "wellness", "hiking", "romance", "wildlife",
            "skiing", "diving", "surfing", "photography", "architecture",
            "shopping", "family", "budget", "luxury",
        }
        style_preferences = [s.lower() for s in style_preferences
                             if isinstance(s, str) and s.lower() in VALID_STYLES]

        # Extract passport country for visa scoring
        passport_country = data.get("passport_country", None)

        # Extract optional temporal parameters for seasonal scoring
        travel_month = data.get("travel_month", None)
        travel_date = data.get("travel_date", None)

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
            top_n=5,
            travel_month=travel_month,
            travel_date=travel_date,
        )

        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        return jsonify({"error": f"Recommendation failed: {str(e)}"}), 500


@recommend_bp.route("/api/destinations/<destination_id>/similar", methods=["GET"])
def similar_destinations(destination_id):
    """Get destinations similar to a given one."""
    top_n = request.args.get("top_n", 5, type=int)
    results = get_similar_destinations(destination_id, top_n=top_n)
    if results is None:
        return jsonify({"error": f"Destination '{destination_id}' not found"}), 404
    return jsonify({"similar": results}), 200


@recommend_bp.route("/api/destinations/trending", methods=["GET"])
def trending_destinations():
    """Get trending destinations, optionally for a specific month."""
    month = request.args.get("month", None, type=int)
    top_n = request.args.get("top_n", 10, type=int)
    results = get_trending_destinations(month=month, top_n=top_n)
    return jsonify({"trending": results}), 200


@recommend_bp.route("/api/recommendations/collaborative", methods=["POST"])
def collaborative_recommendations():
    """
    Get recommendations using SVD collaborative filtering.

    Request Body (JSON):
    {
        "user_history": ["bali", "bangkok", "tokyo"],
        "all_user_histories": [
            ["bali", "bangkok"],
            ["tokyo", "kyoto", "osaka"],
            ["bali", "sri-lanka", "maldives"],
            ...at least 5 users
        ],
        "budget_level": "medium",
        "group_type": "solo",
        "top_n": 5
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        user_history = data.get("user_history", [])
        all_user_histories = data.get("all_user_histories", [])
        budget_level = data.get("budget_level", "medium")
        group_type = data.get("group_type", "solo")
        top_n = data.get("top_n", 5)

        results = get_svd_recommendations(
            user_history=user_history,
            all_user_histories=all_user_histories,
            budget_level=budget_level,
            group_type=group_type,
            top_n=top_n,
        )

        return jsonify({"recommendations": results, "method": "collaborative_svd"}), 200

    except Exception as e:
        return jsonify({"error": f"Collaborative filtering failed: {str(e)}"}), 500


@recommend_bp.route("/api/recommendations/evaluate", methods=["POST"])
def evaluate():
    """
    Evaluate recommendation engine accuracy.

    Request Body (JSON):
    {
        "test_cases": [
            {
                "input": {"budget_level": "low", "style_preferences": ["beach"], "group_type": "solo", "top_n": 5},
                "relevant": ["bali", "zanzibar", "goa", "phuket", "sri-lanka"]
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or "test_cases" not in data:
            return jsonify({"error": "test_cases array required"}), 400

        metrics = evaluate_recommendations(data["test_cases"])
        return jsonify(metrics), 200

    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500
