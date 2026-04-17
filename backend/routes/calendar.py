"""
TravelBuddy - Google Calendar Integration Routes
==================================================
Allows users to connect their Google Calendar so the app can
read busy dates and suggest free travel windows automatically.

Endpoints:
  GET  /api/calendar/auth-url      → Google OAuth2 authorisation URL
  GET  /api/calendar/callback      → OAuth2 callback (exchanges code for tokens)
  GET  /api/calendar/free-windows  → Finds free 2+ day windows in next 90 days
  POST /api/calendar/disconnect    → Removes calendar connection
"""

import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, redirect
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from firebase_config import verify_token, get_db, is_firebase_available, save_user_profile, get_user_profile

calendar_bp = Blueprint("calendar", __name__)

# Google OAuth2 scopes — read-only calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_oauth_flow():
    """Build and return a Google OAuth2 Flow using .env credentials."""
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/calendar/callback")],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/calendar/callback")
    return flow


def _extract_uid(req):
    """Extract user UID from the Authorization header (Bearer token)."""
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        decoded = verify_token(token)
        if decoded:
            return decoded.get("uid", "demo-user-001")
    return "demo-user-001"


# ── GET /api/calendar/auth-url ──────────────────────────────────────────────
@calendar_bp.route("/api/calendar/auth-url", methods=["GET"])
def auth_url():
    """Return the Google OAuth2 authorisation URL for calendar access."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return jsonify({"error": "Google Calendar not configured. Set GOOGLE_CLIENT_ID in .env"}), 503

    flow = _get_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return jsonify({"auth_url": authorization_url, "state": state}), 200


# ── GET /api/calendar/callback ──────────────────────────────────────────────
@calendar_bp.route("/api/calendar/callback", methods=["GET"])
def callback():
    """
    Google OAuth2 callback. Exchanges the authorisation code for tokens
    and stores them in Firebase under the user's profile.
    """
    code = request.args.get("code")
    if not code:
        return redirect("http://localhost:5173/dashboard?calendar=error")

    try:
        flow = _get_oauth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }

        # Store tokens in Firebase
        uid = "demo-user-001"  # Callback doesn't have Bearer token; use state or default
        save_user_profile(uid, {
            "google_calendar_connected": True,
            "calendar_tokens": token_data,
        })

        return redirect("http://localhost:5173/dashboard?calendar=connected")

    except Exception as e:
        print(f"[Calendar] OAuth callback error: {e}")
        return redirect("http://localhost:5173/dashboard?calendar=error")


# ── GET /api/calendar/free-windows ──────────────────────────────────────────
@calendar_bp.route("/api/calendar/free-windows", methods=["GET"])
def free_windows():
    """
    Fetch the user's Google Calendar events for the next 90 days
    and return free windows of 2+ days as suggested travel dates.
    """
    uid = _extract_uid(request)

    # Get calendar tokens from Firebase
    profile = get_user_profile(uid)

    # Demo mode: return sample windows when Firebase isn't configured
    if not profile or not profile.get("google_calendar_connected"):
        # If not connected, return demo windows so the feature still works
        if not is_firebase_available():
            return _demo_windows()
        return jsonify({"connected": False, "windows": []}), 200

    token_data = profile.get("calendar_tokens")
    if not token_data:
        return jsonify({"connected": False, "windows": [], "error": "No calendar tokens found"}), 200

    try:
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", os.getenv("GOOGLE_CLIENT_ID", "")),
            client_secret=token_data.get("client_secret", os.getenv("GOOGLE_CLIENT_SECRET", "")),
            scopes=token_data.get("scopes", SCOPES),
        )

        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=90)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        windows = _find_free_windows(events, now, now + timedelta(days=90))

        # Find next free weekend
        next_weekend = _find_next_free_weekend(events, now)

        return jsonify({
            "connected": True,
            "windows": windows[:10],
            "next_free_weekend": next_weekend,
        }), 200

    except Exception as e:
        print(f"[Calendar] Error fetching events: {e}")
        return jsonify({
            "connected": True,
            "windows": [],
            "error": "Could not fetch calendar events. Try reconnecting.",
        }), 200


# ── POST /api/calendar/disconnect ──────────────────────────────────────────
@calendar_bp.route("/api/calendar/disconnect", methods=["POST"])
def disconnect():
    """Remove calendar tokens from Firebase and mark as disconnected."""
    uid = _extract_uid(request)

    save_user_profile(uid, {
        "google_calendar_connected": False,
        "calendar_tokens": None,
    })

    return jsonify({"success": True, "message": "Google Calendar disconnected"}), 200


# ── Helper functions ────────────────────────────────────────────────────────

def _find_free_windows(events, range_start, range_end):
    """
    Given a list of calendar events, find gaps of 2+ days
    between busy periods within the date range.
    """
    busy_dates = set()

    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})

        # Get start date (handle all-day and timed events)
        start_str = start.get("date") or start.get("dateTime", "")[:10]
        end_str = end.get("date") or end.get("dateTime", "")[:10]

        if not start_str or not end_str:
            continue

        try:
            s = datetime.strptime(start_str, "%Y-%m-%d")
            e = datetime.strptime(end_str, "%Y-%m-%d")
            current = s
            while current < e:
                busy_dates.add(current.date())
                current += timedelta(days=1)
            # Also mark the start date for timed events
            busy_dates.add(s.date())
        except ValueError:
            continue

    # Walk through the date range and find free windows
    windows = []
    current_window_start = None
    current = range_start.date() if hasattr(range_start, 'date') else range_start

    end_date = range_end.date() if hasattr(range_end, 'date') else range_end

    day = current
    while day <= end_date:
        if day not in busy_dates:
            if current_window_start is None:
                current_window_start = day
        else:
            if current_window_start is not None:
                duration = (day - current_window_start).days
                if duration >= 2:
                    windows.append(_format_window(current_window_start, day - timedelta(days=1), duration))
                current_window_start = None
        day += timedelta(days=1)

    # Close final window if open
    if current_window_start is not None:
        duration = (end_date - current_window_start).days + 1
        if duration >= 2:
            windows.append(_format_window(current_window_start, end_date, duration))

    return sorted(windows, key=lambda w: w["start"])


def _format_window(start_date, end_date, duration):
    """Format a free window into the response structure."""
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    label_start = start_date.strftime("%-d %b") if os.name != "nt" else start_date.strftime("%#d %b")
    label_end = end_date.strftime("%-d %b") if os.name != "nt" else end_date.strftime("%#d %b")

    # Determine budget suggestion based on duration
    if duration <= 3:
        suggested_budget = "weekend"
    elif duration <= 7:
        suggested_budget = "short_trip"
    else:
        suggested_budget = "full_holiday"

    return {
        "start": start_str,
        "end": end_str,
        "duration_days": duration,
        "label": f"{duration} days free — {label_start} to {label_end}",
        "suggested_budget": suggested_budget,
    }


def _find_next_free_weekend(events, now):
    """Find the next Saturday-Sunday pair that has no events."""
    busy_dates = set()
    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})
        start_str = start.get("date") or start.get("dateTime", "")[:10]
        end_str = end.get("date") or end.get("dateTime", "")[:10]
        if not start_str or not end_str:
            continue
        try:
            s = datetime.strptime(start_str, "%Y-%m-%d")
            e = datetime.strptime(end_str, "%Y-%m-%d")
            current = s
            while current <= e:
                busy_dates.add(current.date())
                current += timedelta(days=1)
        except ValueError:
            continue

    # Look ahead up to 90 days for a free weekend
    day = now.date() if hasattr(now, 'date') else now
    for _ in range(90):
        if day.weekday() == 5:  # Saturday
            sunday = day + timedelta(days=1)
            if day not in busy_dates and sunday not in busy_dates:
                return day.strftime("%Y-%m-%d")
        day += timedelta(days=1)

    return None


def _demo_windows():
    """Return sample free windows for demo mode (no Firebase/Google)."""
    today = datetime.utcnow().date()

    # Generate realistic demo windows starting from upcoming dates
    demo_windows = []
    day = today + timedelta(days=7)

    # Find next Saturday
    while day.weekday() != 5:
        day += timedelta(days=1)

    next_weekend = day.strftime("%Y-%m-%d")

    # Create 5 demo windows
    offsets = [
        (14, 4, "weekend"),
        (25, 7, "short_trip"),
        (40, 3, "weekend"),
        (55, 5, "short_trip"),
        (70, 10, "full_holiday"),
    ]

    for offset, duration, budget in offsets:
        start = today + timedelta(days=offset)
        end = start + timedelta(days=duration - 1)
        demo_windows.append(_format_window(start, end, duration))

    return jsonify({
        "connected": True,
        "windows": demo_windows[:10],
        "next_free_weekend": next_weekend,
        "demo": True,
    }), 200
