"""
TravelBuddy - Auth API Route
==============================
POST /api/auth/profile     — Save/update user profile
GET  /api/auth/profile     — Get user profile
POST /api/auth/verify      — Verify Firebase token (health check)
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from firebase_config import verify_token, save_user_profile, get_user_profile

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/verify", methods=["POST"])
def verify():
    """Verify a Firebase ID token and return user info."""
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split("Bearer ")[1]
        decoded = verify_token(token)

        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify({
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "verified": True,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500


@auth_bp.route("/api/auth/profile", methods=["POST"])
def update_profile():
    """Save or update user profile (called after onboarding)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Get user from auth token
        auth_header = request.headers.get("Authorization", "")
        uid = "demo-user-001"
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            decoded = verify_token(token)
            if decoded:
                uid = decoded["uid"]

        # Build the profile document
        profile = {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "budget_level": data.get("budget_level", "medium"),
            "travel_style": data.get("travel_style", []),
            "group_type": data.get("group_type", "solo"),
            "preferred_duration": data.get("preferred_duration", "one_week"),
            "nationality": data.get("nationality", "GB"),
            "onboarding_complete": True,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Only set created_at on first save
        existing = get_user_profile(uid)
        if not existing:
            profile["created_at"] = datetime.utcnow().isoformat()
            profile["travel_history"] = []

        success = save_user_profile(uid, profile)

        if success:
            return jsonify({"message": "Profile saved", "profile": profile}), 200
        else:
            return jsonify({"error": "Failed to save profile"}), 500

    except Exception as e:
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500


@auth_bp.route("/api/auth/profile", methods=["GET"])
def get_profile():
    """Get the current user's profile."""
    try:
        auth_header = request.headers.get("Authorization", "")
        uid = "demo-user-001"
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            decoded = verify_token(token)
            if decoded:
                uid = decoded["uid"]

        profile = get_user_profile(uid)

        if profile:
            return jsonify({"profile": profile}), 200
        else:
            return jsonify({"profile": None, "onboarding_complete": False}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500
