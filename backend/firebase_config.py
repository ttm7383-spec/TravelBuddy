"""
TravelBuddy - Firebase Admin SDK Configuration
================================================
This module initialises the Firebase Admin SDK for server-side operations:
- Verifying Firebase Auth ID tokens sent from the frontend
- Reading/writing to Firestore (user profiles, saved itineraries)

In demo mode (USE_MOCK_DATA=true or no service account key), Firebase
operations are skipped gracefully so the app still works.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Track whether Firebase was successfully initialised
_firebase_initialised = False
_db = None


def init_firebase():
    """
    Initialise Firebase Admin SDK using the service account key.
    Call this once at app startup.
    """
    global _firebase_initialised, _db

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")

    if not service_account_path or not os.path.exists(service_account_path):
        print("[Firebase] No service account key found — running without Firebase.")
        print("[Firebase] Set FIREBASE_SERVICE_ACCOUNT_KEY in .env to enable.")
        return False

    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        _firebase_initialised = True
        print("[Firebase] Initialised successfully.")
        return True
    except Exception as e:
        print(f"[Firebase] Init failed: {e}")
        return False


def get_db():
    """Get the Firestore client. Returns None if Firebase is not initialised."""
    return _db


def is_firebase_available():
    """Check if Firebase is available."""
    return _firebase_initialised


def verify_token(id_token):
    """
    Verify a Firebase Auth ID token from the frontend.

    Parameters
    ----------
    id_token : str
        The Firebase ID token from the Authorization header.

    Returns
    -------
    dict or None
        The decoded token (contains uid, email, etc.) or None if invalid.
    """
    if not _firebase_initialised:
        # In demo mode without Firebase, return a mock user
        return {"uid": "demo-user-001", "email": "demo@travelbuddy.com"}

    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        print(f"[Firebase] Token verification failed: {e}")
        return None


def save_user_profile(uid, profile_data):
    """Save or update a user profile in Firestore."""
    if not _firebase_initialised:
        print(f"[Firebase] Would save profile for {uid}: {json.dumps(profile_data)[:100]}")
        return True

    try:
        _db.collection("users").document(uid).set(profile_data, merge=True)
        return True
    except Exception as e:
        print(f"[Firebase] Failed to save profile: {e}")
        return False


def get_user_profile(uid):
    """Get a user profile from Firestore."""
    if not _firebase_initialised:
        return None

    try:
        doc = _db.collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"[Firebase] Failed to get profile: {e}")
        return None


def save_itinerary(uid, itinerary_data):
    """Save an itinerary to Firestore under the user's subcollection."""
    if not _firebase_initialised:
        print(f"[Firebase] Would save itinerary for {uid}")
        return "mock-itinerary-001"

    try:
        doc_ref = _db.collection("users").document(uid).collection("itineraries").add(itinerary_data)
        return doc_ref[1].id
    except Exception as e:
        print(f"[Firebase] Failed to save itinerary: {e}")
        return None


def get_user_itineraries(uid):
    """Get all saved itineraries for a user."""
    if not _firebase_initialised:
        return []

    try:
        docs = _db.collection("users").document(uid).collection("itineraries").stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        print(f"[Firebase] Failed to get itineraries: {e}")
        return []
