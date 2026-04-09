"""
TravelBuddy Backend - Flask Application Entry Point
=====================================================
This is the main entry point for the TravelBuddy Flask API.
It registers all route blueprints and initialises Firebase.

Run with: python app.py
"""

import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Import route blueprints
from routes.recommend import recommend_bp
from routes.itinerary import itinerary_bp
from routes.auth import auth_bp
from routes.visa import visa_bp
from routes.chat import chat_bp

# Import Firebase initialisation
from firebase_config import init_firebase


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # Enable CORS so the React frontend can call the API
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
    ]
    # Allow Vercel deployment URLs in production
    vercel_url = os.getenv("VERCEL_FRONTEND_URL")
    if vercel_url:
        cors_origins.append(vercel_url)
    CORS(app, origins=cors_origins, supports_credentials=True)

    # Register route blueprints
    app.register_blueprint(recommend_bp)
    app.register_blueprint(itinerary_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(visa_bp)
    app.register_blueprint(chat_bp)

    # Global error handlers — always return JSON, never HTML
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": True, "message": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": True, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": True, "message": "Internal server error"}), 500

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
        return jsonify({
            "status": "ok",
            "mock_mode": use_mock,
            "message": "TravelBuddy API is running",
        }), 200

    return app


# Initialise Firebase (gracefully skips if no service account key)
init_firebase()

# Create the app instance (used by gunicorn: gunicorn app:app)
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    amadeus_key = os.getenv("AMADEUS_API_KEY", "")
    has_amadeus = amadeus_key and amadeus_key != "your_amadeus_api_key"

    print(f"\n{'='*55}")
    print(f"  TravelBuddy API running on http://localhost:{port}")
    print(f"{'='*55}")
    if use_mock:
        print(f"  Mode: MOCK DATA (demo mode)")
        print(f"  Flights & hotels use city-specific mock data")
    else:
        print(f"  Mode: LIVE APIs")
    if not has_amadeus:
        print(f"  [!] AMADEUS_API_KEY not set - using smart mock data")
        print(f"      Get free keys at developers.amadeus.com (2 mins)")
    else:
        print(f"  [OK] Amadeus API configured")
    print(f"{'='*55}\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
