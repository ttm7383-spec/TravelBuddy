"""
TravelBuddy Backend - Flask Application Entry Point
=====================================================
This is the main entry point for the TravelBuddy Flask API.
It registers all route blueprints and initialises Firebase.

Run with: python app.py
"""

import os
import time
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, g, request as flask_request
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Import route blueprints
from routes.recommend import recommend_bp
from routes.itinerary import itinerary_bp
from routes.auth import auth_bp
from routes.visa import visa_bp
from routes.chat import chat_bp
from routes.feedback import feedback_bp
from routes.calendar import calendar_bp

# Import Firebase initialisation
from firebase_config import init_firebase


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # Initialise Firebase (gracefully skips if no service account key)
    init_firebase()

    # ---------------------------------------------------------------------------
    # Performance logging — logs every request with response time
    # ---------------------------------------------------------------------------
    os.makedirs("logs", exist_ok=True)

    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.INFO)
    if not perf_logger.handlers:
        handler = logging.FileHandler("logs/performance.log")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        perf_logger.addHandler(handler)

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_response_time(response):
        if hasattr(g, "start_time"):
            elapsed_ms = round((time.time() - g.start_time) * 1000, 2)
            status = "PASS" if elapsed_ms < 5000 else "FAIL"
            perf_logger.info(
                f"{flask_request.method} {flask_request.path} | "
                f"{elapsed_ms}ms | {status} | "
                f"HTTP {response.status_code}"
            )
            response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response

    # Enable CORS so the React frontend can call the API
    CORS(app, origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "https://travel-buddy-five-mu.vercel.app",
        "https://travel-buddy-git-main-ttm7383-specs-projects.vercel.app",
    ])

    # Register route blueprints
    app.register_blueprint(recommend_bp)
    app.register_blueprint(itinerary_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(visa_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(calendar_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
        return jsonify({
            "status": "ok",
            "mock_mode": use_mock,
            "message": "TravelBuddy API is running",
        }), 200

    # Performance metrics endpoint
    @app.route("/api/metrics", methods=["GET"])
    def metrics():
        """
        Return performance metrics parsed from logs/performance.log.
        Shows total requests, average/min/max response times,
        pass rate (< 5000ms threshold), and recent requests.
        """
        log_path = "logs/performance.log"
        if not os.path.exists(log_path):
            return jsonify({
                "total_requests": 0,
                "average_response_ms": 0,
                "min_response_ms": 0,
                "max_response_ms": 0,
                "requests_under_5000ms": 0,
                "requests_over_5000ms": 0,
                "pass_rate_percent": 100.0,
                "meets_kpi": True,
                "recent_requests": [],
            }), 200

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

        response_times = []
        pass_count = 0
        fail_count = 0
        parsed = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" | ")
            if len(parts) >= 4:
                try:
                    timestamp = parts[0]
                    route_info = parts[1]
                    time_str = parts[2]
                    status_info = parts[3]

                    ms = float(time_str.replace("ms", ""))
                    response_times.append(ms)

                    if "PASS" in parts[2] or "PASS" in status_info:
                        pass_count += 1
                    else:
                        fail_count += 1

                    parsed.append({
                        "timestamp": timestamp,
                        "route": route_info,
                        "response_ms": ms,
                        "status": status_info,
                    })
                except (ValueError, IndexError):
                    continue

        total = len(response_times)
        avg = round(sum(response_times) / total, 2) if total else 0
        mn = round(min(response_times), 2) if total else 0
        mx = round(max(response_times), 2) if total else 0
        under = sum(1 for t in response_times if t < 5000)
        over = total - under
        rate = round((under / total) * 100, 1) if total else 100.0

        return jsonify({
            "total_requests": total,
            "average_response_ms": avg,
            "min_response_ms": mn,
            "max_response_ms": mx,
            "requests_under_5000ms": under,
            "requests_over_5000ms": over,
            "pass_rate_percent": rate,
            "meets_kpi": rate >= 95.0,
            "recent_requests": parsed[-10:],
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
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
        print(f"     Get free keys at developers.amadeus.com (2 mins)")
    else:
        print(f"  [OK] Amadeus API configured")
    print(f"{'='*55}\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
