"""
TravelBuddy - Itinerary API Route
===================================
POST /api/itinerary     — Build an itinerary for a destination
POST /api/itinerary/save — Save an itinerary to Firebase
GET  /api/itineraries    — Get user's saved itineraries
"""

import os
import re
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import requests

from firebase_config import verify_token, save_itinerary, get_user_itineraries
from recommender.engine import DESTINATIONS
from services.amadeus_service import search_flights, search_hotels, get_city_data
from routes.visa import get_visa_info

itinerary_bp = Blueprint("itinerary", __name__)

# Path to mock data files
_MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data")


def _load_mock(filename):
    """Load a mock data JSON file."""
    path = os.path.join(_MOCK_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_destination(destination_id):
    """Look up a destination by ID from the database."""
    for dest in DESTINATIONS:
        if dest["id"] == destination_id:
            return dest
    return None


# ---------------------------------------------------------------------------
# Real API integrations (used when USE_MOCK_DATA=false)
# ---------------------------------------------------------------------------

def _fetch_amadeus_flights(origin, destination, date):
    """Fetch flight offers from Amadeus API."""
    try:
        # Step 1: Get access token
        token_url = "https://api.amadeus.com/v1/security/oauth2/token"
        token_resp = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("AMADEUS_API_KEY"),
            "client_secret": os.getenv("AMADEUS_API_SECRET"),
        }, timeout=10)
        token = token_resp.json().get("access_token")

        if not token:
            return None

        # Step 2: Search flights
        search_url = "https://api.amadeus.com/v2/shopping/flight-offers"
        resp = requests.get(search_url, headers={
            "Authorization": f"Bearer {token}"
        }, params={
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": date,
            "adults": 1,
            "max": 3,
            "currencyCode": "GBP",
        }, timeout=15)

        if resp.status_code != 200:
            return None

        offers = resp.json().get("data", [])
        flights = []
        for offer in offers:
            seg = offer["itineraries"][0]["segments"][0]
            flights.append({
                "airline": seg.get("carrierCode", "Unknown"),
                "flight_number": seg.get("number", ""),
                "price_gbp": float(offer["price"]["total"]),
                "departure": {
                    "airport": seg["departure"]["iataCode"],
                    "time": seg["departure"]["at"].split("T")[1][:5],
                    "date": seg["departure"]["at"].split("T")[0],
                },
                "arrival": {
                    "airport": seg["arrival"]["iataCode"],
                    "time": seg["arrival"]["at"].split("T")[1][:5],
                    "date": seg["arrival"]["at"].split("T")[0],
                },
                "duration": offer["itineraries"][0].get("duration", "N/A"),
                "stops": len(offer["itineraries"][0]["segments"]) - 1,
                "cabin_class": "Economy",
            })
        return flights
    except Exception as e:
        print(f"[Amadeus Flights] Error: {e}")
        return None


def _fetch_amadeus_hotels(city_code, check_in, check_out):
    """Fetch hotel offers from Amadeus API."""
    try:
        token_url = "https://api.amadeus.com/v1/security/oauth2/token"
        token_resp = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("AMADEUS_API_KEY"),
            "client_secret": os.getenv("AMADEUS_API_SECRET"),
        }, timeout=10)
        token = token_resp.json().get("access_token")

        if not token:
            return None

        search_url = "https://api.amadeus.com/v1/reference-data/locations/hotels/by-city"
        resp = requests.get(search_url, headers={
            "Authorization": f"Bearer {token}"
        }, params={
            "cityCode": city_code,
            "radius": 5,
            "radiusUnit": "KM",
        }, timeout=15)

        if resp.status_code != 200:
            return None

        hotels_raw = resp.json().get("data", [])[:3]
        hotels = []
        for h in hotels_raw:
            hotels.append({
                "name": h.get("name", "Hotel"),
                "price_per_night_gbp": 0,
                "rating": 4.0,
                "stars": 3,
                "amenities": [],
                "distance_to_centre": h.get("distance", {}).get("value", "N/A"),
            })
        return hotels
    except Exception as e:
        print(f"[Amadeus Hotels] Error: {e}")
        return None


def _fetch_weather(city_name):
    """Fetch weather forecast from OpenWeatherMap API."""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        url = "https://api.openweathermap.org/data/2.5/forecast"
        resp = requests.get(url, params={
            "q": city_name,
            "appid": api_key,
            "units": "metric",
            "cnt": 40,
        }, timeout=10)

        if resp.status_code != 200:
            return None

        data = resp.json()
        daily = {}
        for item in data.get("list", []):
            date = item["dt_txt"].split(" ")[0]
            if date not in daily:
                daily[date] = {
                    "date": date,
                    "temp_high_c": item["main"]["temp_max"],
                    "temp_low_c": item["main"]["temp_min"],
                    "condition": item["weather"][0]["description"].title(),
                    "icon": item["weather"][0]["icon"],
                    "humidity_percent": item["main"]["humidity"],
                    "wind_kph": round(item["wind"]["speed"] * 3.6, 1),
                }
            else:
                daily[date]["temp_high_c"] = max(daily[date]["temp_high_c"], item["main"]["temp_max"])
                daily[date]["temp_low_c"] = min(daily[date]["temp_low_c"], item["main"]["temp_min"])

        forecasts = list(daily.values())[:7]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for fc in forecasts:
            dt = datetime.strptime(fc["date"], "%Y-%m-%d")
            fc["day"] = days[dt.weekday()]

        return {
            "summary": f"Forecast for {city_name}",
            "daily_forecast": forecasts,
        }
    except Exception as e:
        print(f"[Weather] Error: {e}")
        return None


def _fetch_places(city_name):
    """Fetch nearby places from Foursquare Places API."""
    try:
        api_key = os.getenv("FOURSQUARE_API_KEY")
        url = "https://api.foursquare.com/v3/places/search"
        resp = requests.get(url, headers={
            "Authorization": api_key,
            "Accept": "application/json",
        }, params={
            "near": city_name,
            "categories": "10000,16000,13000",  # Arts, Outdoors, Food
            "limit": 5,
            "sort": "RELEVANCE",
        }, timeout=10)

        if resp.status_code != 200:
            return None

        places_raw = resp.json().get("results", [])
        places = []
        for p in places_raw:
            cats = p.get("categories", [])
            category = cats[0]["name"] if cats else "General"
            places.append({
                "name": p.get("name", "Unknown Place"),
                "category": category,
                "address": p.get("location", {}).get("formatted_address", "N/A"),
                "rating": 4.0,
            })
        return places
    except Exception as e:
        print(f"[Foursquare] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Main Itinerary Endpoint
# ---------------------------------------------------------------------------

@itinerary_bp.route("/api/itinerary", methods=["POST"])
def build_itinerary():
    """
    Build a complete itinerary for a chosen destination.

    Request Body:
    {
        "destination_id": "bali",
        "departure_city": "London",
        "travel_dates": {"start": "2026-04-15", "end": "2026-04-22"},
        "budget_level": "low"
    }

    Response: Full itinerary with flights, hotels, weather, activities, cost estimate.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        destination_id = data.get("destination_id")
        custom_city = data.get("custom_city")
        departure_city = data.get("departure_city", "London")
        travel_dates = data.get("travel_dates", {})
        budget_level = data.get("budget_level", "medium")
        nationality = data.get("nationality", "GB")

        if not destination_id and not custom_city:
            return jsonify({"error": "destination_id or custom_city is required"}), 400

        # Look up the destination (or build a custom one)
        if custom_city:
            destination = {
                "id": "custom-" + custom_city.lower().replace(" ", "-"),
                "name": custom_city,
                "country": "",
                "iata_code": "",
                "avg_daily_cost_gbp": 100,
                "climate": "temperate",
                "tags": ["city"],
            }
        else:
            destination = _find_destination(destination_id)
            if not destination:
                return jsonify({"error": f"Destination '{destination_id}' not found"}), 404

        # Calculate trip duration
        start_date = travel_dates.get("start", "2026-04-15")
        end_date = travel_dates.get("end", "2026-04-22")
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            duration_days = (end_dt - start_dt).days
        except ValueError:
            duration_days = 7

        if duration_days <= 0:
            duration_days = 7

        # --- Flights (via Amadeus service with mock fallback) ---
        flight_result = search_flights(
            origin_city=departure_city,
            destination_city=destination["name"],
            departure_date=start_date,
            return_date=end_date,
        )
        flights = flight_result["flights"]
        flights_is_mock = flight_result["is_mock"]

        # --- Hotels (via Amadeus service with mock fallback) ---
        hotel_result = search_hotels(
            city_name=destination["name"],
            check_in=start_date,
            check_out=end_date,
            budget_level=budget_level,
        )
        hotels = hotel_result["hotels"]
        hotels_is_mock = hotel_result["is_mock"]

        # --- Dietary preferences ---
        dietary_prefs = data.get("dietary_preferences", [])

        # --- City-specific data (restaurants, attractions) ---
        city = get_city_data(destination["name"])
        use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

        if city:
            # Use real city data for attractions
            places = city.get("attractions", _load_mock("places.json"))
            # Get restaurants, filter by dietary preferences
            all_restaurants = city.get("restaurants", [])
            if dietary_prefs:
                restaurants = [r for r in all_restaurants
                    if any(d in r.get("dietary", []) for d in dietary_prefs)
                       or any(d + "-options" in r.get("dietary", []) for d in dietary_prefs)]
                # If filter is too strict, include all
                if not restaurants:
                    restaurants = all_restaurants
            else:
                restaurants = all_restaurants
        else:
            places = _load_mock("places.json")
            restaurants = []

        if not use_mock:
            weather = _fetch_weather(destination["name"])
            if not weather:
                weather = _load_mock("weather.json")
            if not city:
                fetched_places = _fetch_places(destination["name"])
                if fetched_places:
                    places = fetched_places
        else:
            weather = _load_mock("weather.json")

        # --- Visa info (from visa_requirements.json) ---
        visa = get_visa_info(nationality, destination["country"])
        visa_cost = visa.get("cost_gbp", 0)
        visa_info = {
            "nationality": nationality,
            "requirement": visa.get("requirement", "visa-required"),
            "duration_days": visa.get("duration_days"),
            "cost_gbp": visa_cost,
            "processing_days": visa.get("processing_days", 0),
            "notes": visa.get("notes", ""),
            "recommendation": visa.get("recommendation", ""),
            "visa_required": visa.get("requirement", "") not in ("visa-free",),
        }

        # --- Cost breakdown ---
        cheapest_flight = min(f["price_gbp"] for f in flights) if flights else 0
        cheapest_hotel = min(h["price_per_night_gbp"] for h in hotels) if hotels else 0
        daily_cost = destination["avg_daily_cost_gbp"]

        flight_cost = round(cheapest_flight * 2, 2)
        accommodation_cost = round(cheapest_hotel * duration_days, 2)
        food_cost = round(daily_cost * duration_days * 0.4, 2)
        activities_cost = round(daily_cost * duration_days * 0.3, 2)
        insurance_cost = round((flight_cost + accommodation_cost) * 0.03, 2)

        estimated_total = round(
            flight_cost + accommodation_cost + food_cost + activities_cost + visa_cost + insurance_cost, 2
        )

        cost_breakdown = {
            "flights": flight_cost,
            "accommodation": accommodation_cost,
            "food": food_cost,
            "activities": activities_cost,
            "visa": visa_cost,
            "insurance": insurance_cost,
            "total": estimated_total,
        }

        # Local tips and transport info (from city_data.json)
        local_tips = city.get("local_tips", []) if city else []
        transport_from_london = city.get("transport_from_london") if city else None
        is_domestic = destination.get("domestic", False) or (city.get("domestic", False) if city else False)

        # Build the response
        itinerary = {
            "destination": {
                "id": destination["id"],
                "name": destination["name"],
                "country": destination["country"],
                "avg_daily_cost_gbp": destination["avg_daily_cost_gbp"],
                "climate": destination["climate"],
                "tags": destination["tags"],
                "is_domestic": is_domestic,
            },
            "dates": {
                "start": start_date,
                "end": end_date,
                "duration_days": duration_days,
            },
            "weather": weather,
            "flights": flights,
            "hotels": hotels,
            "activities": places,
            "restaurants": restaurants,
            "local_tips": local_tips,
            "transport_from_london": transport_from_london,
            "visa_info": visa_info,
            "cost_breakdown": cost_breakdown,
            "estimated_total_cost_gbp": estimated_total,
            "is_live_prices": not flights_is_mock or not hotels_is_mock,
            "prices_updated_at": flight_result.get("updated_at"),
        }

        return jsonify(itinerary), 200

    except Exception as e:
        return jsonify({"error": f"Failed to build itinerary: {str(e)}"}), 500


@itinerary_bp.route("/api/itinerary/multi", methods=["POST"])
def build_multi_city_itinerary():
    """
    Build a multi-city itinerary across several destinations.

    Request Body:
    {
        "destination_ids": ["bali", "bangkok", "hanoi"],
        "departure_city": "London",
        "travel_dates": {"start": "2026-04-15", "end": "2026-04-29"},
        "budget_level": "medium",
        "nationality": "GB"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        destination_ids = data.get("destination_ids", [])
        departure_city = data.get("departure_city", "London")
        travel_dates = data.get("travel_dates", {})
        budget_level = data.get("budget_level", "medium")
        nationality = data.get("nationality", "GB")

        if not destination_ids or len(destination_ids) < 2:
            return jsonify({"error": "At least 2 destination_ids required"}), 400

        # Look up all destinations (supports "custom:CityName" for custom cities)
        destinations = []
        for did in destination_ids:
            if did.startswith("custom:"):
                # Custom city — create a lightweight destination object
                city_name = did.split(":", 1)[1]
                destinations.append({
                    "id": did,
                    "name": city_name,
                    "country": "",
                    "iata_code": "",
                    "avg_daily_cost_gbp": 100,
                    "best_season": "any",
                    "climate": "temperate",
                    "tags": ["city"],
                    "suitable_for": ["solo", "couple", "family", "friends"],
                    "avg_rating": 4.0,
                    "sample_activities": [],
                })
            else:
                dest = _find_destination(did)
                if not dest:
                    return jsonify({"error": f"Destination '{did}' not found"}), 404
                destinations.append(dest)

        # Calculate total trip duration and split across cities
        start_date = travel_dates.get("start", "2026-04-15")
        end_date = travel_dates.get("end", "2026-04-29")
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            total_days = (end_dt - start_dt).days
        except ValueError:
            total_days = len(destinations) * 3

        if total_days <= 0:
            total_days = len(destinations) * 3

        # Split days across cities (at least 2 days each, remainder to first city)
        num_cities = len(destinations)
        base_days = max(2, total_days // num_cities)
        remainder = total_days - (base_days * num_cities)

        use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

        cities = []
        grand_total = 0
        grand_breakdown = {"flights": 0, "accommodation": 0, "food": 0, "activities": 0, "visa": 0}
        current_date = start_dt

        for i, dest in enumerate(destinations):
            # Days for this city
            city_days = base_days + (remainder if i == 0 else 0)
            city_start = current_date
            city_end = current_date + timedelta(days=city_days)

            # Determine flight leg: origin → city or previous_city → city
            if i == 0:
                flight_from = departure_city
            else:
                flight_from = destinations[i - 1]["name"]

            # Load data via Amadeus service (handles mock fallback internally)
            dep_date = city_start.strftime("%Y-%m-%d")
            end_date_str = city_end.strftime("%Y-%m-%d")

            flight_result = search_flights(flight_from, dest["name"], dep_date)
            flights = flight_result["flights"]

            hotel_result = search_hotels(dest["name"], dep_date, end_date_str, budget_level=budget_level)
            hotels = hotel_result["hotels"]

            if use_mock:
                weather = _load_mock("weather.json")
                places = _load_mock("places.json")
            else:
                weather = _fetch_weather(dest["name"])
                if not weather:
                    weather = _load_mock("weather.json")
                places = _fetch_places(dest["name"])
                if not places:
                    places = _load_mock("places.json")

            # Cost for this leg
            cheapest_flight = min(f["price_gbp"] for f in flights) if flights else 0
            cheapest_hotel = min(h["price_per_night_gbp"] for h in hotels) if hotels else 0
            daily_cost = dest["avg_daily_cost_gbp"]

            leg_flights = round(cheapest_flight, 2)
            leg_accommodation = round(cheapest_hotel * city_days, 2)
            leg_food = round(daily_cost * city_days * 0.4, 2)
            leg_activities = round(daily_cost * city_days * 0.3, 2)

            # Visa (from visa_requirements.json)
            visa = get_visa_info(nationality, dest["country"])
            visa_cost = visa.get("cost_gbp", 0)

            leg_total = round(leg_flights + leg_accommodation + leg_food + leg_activities + visa_cost, 2)

            grand_breakdown["flights"] += leg_flights
            grand_breakdown["accommodation"] += leg_accommodation
            grand_breakdown["food"] += leg_food
            grand_breakdown["activities"] += leg_activities
            grand_breakdown["visa"] += visa_cost
            grand_total += leg_total

            cities.append({
                "destination": {
                    "id": dest["id"],
                    "name": dest["name"],
                    "country": dest["country"],
                    "avg_daily_cost_gbp": dest["avg_daily_cost_gbp"],
                    "climate": dest["climate"],
                    "tags": dest["tags"],
                },
                "dates": {
                    "start": city_start.strftime("%Y-%m-%d"),
                    "end": city_end.strftime("%Y-%m-%d"),
                    "duration_days": city_days,
                },
                "flight_from": flight_from,
                "weather": weather,
                "flights": flights,
                "hotels": hotels,
                "activities": places,
                "visa_info": {
                    "nationality": nationality,
                    "requirement": visa.get("requirement", "visa-required"),
                    "cost_gbp": visa_cost,
                    "processing_days": visa.get("processing_days", 0),
                    "notes": visa.get("notes", ""),
                    "recommendation": visa.get("recommendation", ""),
                    "visa_required": visa.get("requirement", "") not in ("visa-free",),
                },
                "cost_breakdown": {
                    "flights": leg_flights,
                    "accommodation": leg_accommodation,
                    "food": leg_food,
                    "activities": leg_activities,
                    "visa": visa_cost,
                    "total": leg_total,
                },
            })

            current_date = city_end

        # Add return flight cost (last city → home)
        return_flight_cost = grand_breakdown["flights"] / len(destinations) if destinations else 0
        grand_breakdown["flights"] = round(grand_breakdown["flights"] + return_flight_cost, 2)
        grand_total = round(grand_total + return_flight_cost, 2)

        # Round all grand breakdown values
        for k in grand_breakdown:
            grand_breakdown[k] = round(grand_breakdown[k], 2)
        grand_breakdown["total"] = round(grand_total, 2)

        # Build route summary
        route = [departure_city] + [d["name"] for d in destinations] + [departure_city]

        response = {
            "multi_city": True,
            "route": route,
            "total_dates": {
                "start": start_date,
                "end": end_date,
                "duration_days": total_days,
            },
            "cities": cities,
            "cost_breakdown": grand_breakdown,
            "estimated_total_cost_gbp": round(grand_total, 2),
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed to build multi-city itinerary: {str(e)}"}), 500


@itinerary_bp.route("/api/itinerary/save", methods=["POST"])
def save_itinerary_route():
    """Save an itinerary to the user's Firebase account."""
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

        # Add timestamp
        data["saved_at"] = datetime.utcnow().isoformat()

        itinerary_id = save_itinerary(uid, data)

        if itinerary_id:
            return jsonify({"id": itinerary_id, "message": "Itinerary saved"}), 201
        else:
            return jsonify({"error": "Failed to save itinerary"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to save: {str(e)}"}), 500


@itinerary_bp.route("/api/itineraries", methods=["GET"])
def list_itineraries():
    """Get all saved itineraries for the authenticated user."""
    try:
        auth_header = request.headers.get("Authorization", "")
        uid = "demo-user-001"
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            decoded = verify_token(token)
            if decoded:
                uid = decoded["uid"]

        itineraries = get_user_itineraries(uid)
        return jsonify({"itineraries": itineraries}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch itineraries: {str(e)}"}), 500
