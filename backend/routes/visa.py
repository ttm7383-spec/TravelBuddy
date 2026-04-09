"""
TravelBuddy - Visa Check API Route
====================================
POST /api/visa-check       — Check visa requirement for one destination
POST /api/visa-check/batch — Check visa requirements for multiple destinations
"""

import json
import os
from flask import Blueprint, request, jsonify

visa_bp = Blueprint("visa", __name__)

# Load visa data once at import
_VISA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "visa_requirements.json")

with open(_VISA_PATH, "r", encoding="utf-8") as f:
    VISA_DATA = json.load(f)


def get_visa_info(passport_country, destination_country):
    """
    Look up visa requirements for a passport → destination combination.

    Returns a dict with requirement, cost, processing time, etc.
    Falls back to a sensible default if the combination isn't in our data.
    """
    passport_data = VISA_DATA.get(passport_country, {})
    info = passport_data.get(destination_country)

    if not info:
        # Default fallback for unknown combinations
        return {
            "requirement": "visa-required",
            "duration_days": 30,
            "cost_gbp": 50,
            "processing_days": 15,
            "notes": "Check embassy website for latest requirements",
            "recommendation": f"We don't have specific data for {passport_country} passports visiting {destination_country}. Check the embassy website.",
        }

    # Build human-readable recommendation
    req = info["requirement"]
    cost = info["cost_gbp"]
    days = info["processing_days"]

    if req == "visa-free":
        rec = f"No visa needed! You can stay up to {info['duration_days']} days."
    elif req == "visa-on-arrival":
        if cost > 0:
            rec = f"You'll get a visa on arrival (£{cost}). No advance paperwork needed."
        else:
            rec = f"Free visa on arrival — up to {info['duration_days']} days."
    elif req == "e-visa":
        rec = f"Apply for an e-visa online (£{cost}). Takes about {days} day(s) to process."
    elif req == "visa-required":
        rec = f"You'll need to apply for a visa at the embassy (£{cost}). Allow {days}+ days for processing."
    elif req == "not-admitted":
        rec = "Entry is currently not permitted for this passport."
    else:
        rec = info.get("notes", "Check embassy website")

    return {
        **info,
        "recommendation": rec,
    }


@visa_bp.route("/api/visa-check", methods=["POST"])
def check_visa():
    """
    Check visa requirement for a single destination.

    Body: { "passport_country": "GB", "destination_country": "Thailand" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        passport = data.get("passport_country", "GB")
        destination = data.get("destination_country", "")

        if not destination:
            return jsonify({"error": "destination_country is required"}), 400

        info = get_visa_info(passport, destination)
        return jsonify(info), 200

    except Exception as e:
        return jsonify({"error": f"Visa check failed: {str(e)}"}), 500


@visa_bp.route("/api/visa-check/batch", methods=["POST"])
def check_visa_batch():
    """
    Check visa requirements for multiple destinations at once.

    Body: { "passport_country": "IN", "destinations": ["Thailand", "Japan", "France"] }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        passport = data.get("passport_country", "GB")
        destinations = data.get("destinations", [])

        if not destinations:
            return jsonify({"error": "destinations list is required"}), 400

        results = {}
        for dest in destinations:
            results[dest] = get_visa_info(passport, dest)

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": f"Batch visa check failed: {str(e)}"}), 500
