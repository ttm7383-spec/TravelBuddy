"""
TravelBuddy - Feedback API Route
==================================
Implements user feedback loop for adaptive learning.
Tracks user interactions (booked, saved, dismissed, viewed) per destination
and provides aggregated stats for the recommendation engine to learn from.
"""

import os
import json
from datetime import datetime
from collections import Counter
from flask import Blueprint, request, jsonify

feedback_bp = Blueprint("feedback", __name__)

_FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.json")

ACTION_WEIGHTS = {
    "booked": 5,
    "saved": 3,
    "dismissed": -2,
    "viewed": 1,
}

VALID_ACTIONS = set(ACTION_WEIGHTS.keys())


def _load_feedback():
    """Load feedback data from JSON file."""
    try:
        with open(_FEEDBACK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_feedback(data):
    """Save feedback data to JSON file."""
    with open(_FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@feedback_bp.route("/api/feedback", methods=["POST"])
def record_feedback():
    """
    Record a user interaction with a destination.

    Request Body:
    {
        "user_id": "string",
        "destination_id": "string",
        "action": "booked" | "saved" | "dismissed" | "viewed",
        "session_id": "optional string"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    user_id = data.get("user_id", "anonymous")
    destination_id = data.get("destination_id")
    action = data.get("action")
    session_id = data.get("session_id", "")

    if not destination_id:
        return jsonify({"error": "destination_id is required"}), 400

    if action not in VALID_ACTIONS:
        return jsonify({
            "error": f"Invalid action: '{action}'. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"
        }), 400

    weight = ACTION_WEIGHTS[action]

    entry = {
        "user_id": user_id,
        "destination_id": destination_id,
        "action": action,
        "weight": weight,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    feedback = _load_feedback()
    feedback.append(entry)
    _save_feedback(feedback)

    return jsonify({"recorded": True, "weight": weight}), 201


@feedback_bp.route("/api/feedback/stats", methods=["GET"])
def feedback_stats():
    """
    Return aggregated feedback statistics.
    """
    feedback = _load_feedback()

    action_breakdown = Counter(f["action"] for f in feedback)

    # Top destinations per action type
    def top_by_action(action, n=5):
        counts = Counter(f["destination_id"] for f in feedback if f["action"] == action)
        return [dest_id for dest_id, _ in counts.most_common(n)]

    return jsonify({
        "total_interactions": len(feedback),
        "most_saved": top_by_action("saved"),
        "most_booked": top_by_action("booked"),
        "most_dismissed": top_by_action("dismissed"),
        "action_breakdown": {
            "booked": action_breakdown.get("booked", 0),
            "saved": action_breakdown.get("saved", 0),
            "dismissed": action_breakdown.get("dismissed", 0),
            "viewed": action_breakdown.get("viewed", 0),
        },
    }), 200


@feedback_bp.route("/api/feedback/destination/<destination_id>", methods=["GET"])
def destination_feedback(destination_id):
    """
    Return feedback summary for a single destination.
    """
    feedback = _load_feedback()
    dest_feedback = [f for f in feedback if f["destination_id"] == destination_id]

    action_counts = Counter(f["action"] for f in dest_feedback)
    sentiment_score = sum(f.get("weight", 0) for f in dest_feedback)

    return jsonify({
        "destination_id": destination_id,
        "total_interactions": len(dest_feedback),
        "sentiment_score": sentiment_score,
        "action_counts": {
            "booked": action_counts.get("booked", 0),
            "saved": action_counts.get("saved", 0),
            "dismissed": action_counts.get("dismissed", 0),
            "viewed": action_counts.get("viewed", 0),
        },
    }), 200
