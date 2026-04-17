"""
TravelBuddy - Booking.com Hotel Search (via RapidAPI)
======================================================
Secondary hotel data source when Amadeus hotel data is sparse.
Uses the Booking.com API on RapidAPI (free tier: 500 calls/month).

Sign up: https://rapidapi.com/DataCrawler/api/booking-com15
"""

import os
import requests
from services.amadeus_service import make_booking_url, make_booking_city_url

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"


def _headers():
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }


def is_available():
    """Check if the Booking.com RapidAPI key is configured."""
    return bool(RAPIDAPI_KEY) and RAPIDAPI_KEY != "your_rapidapi_key"


def search_hotels(city, checkin, checkout, adults=1, budget_tier="medium"):
    """
    Search hotels via Booking.com RapidAPI.

    Returns list of hotel dicts, or empty list on failure.
    Each hotel has: name, stars, rating, review_count, price_per_night_gbp,
    image_url, booking_url, location, amenities.
    """
    if not is_available():
        return []

    try:
        # Step 1: Get destination ID for the city
        url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchDestination"
        r = requests.get(url, headers=_headers(), params={"query": city}, timeout=10)
        if r.status_code != 200:
            print(f"[Booking.com] Destination search failed: {r.status_code}")
            return []

        data = r.json().get("data", [])
        if not data:
            return []

        dest_id = data[0].get("dest_id", "")
        dest_type = data[0].get("search_type", "city")

        # Step 2: Search hotels
        url2 = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchHotels"
        params = {
            "dest_id": dest_id,
            "search_type": dest_type,
            "arrival_date": checkin,
            "departure_date": checkout,
            "adults": adults,
            "currency_code": "GBP",
            "sort_by": "price",
            "page_number": 1,
        }
        r2 = requests.get(url2, headers=_headers(), params=params, timeout=15)
        if r2.status_code != 200:
            print(f"[Booking.com] Hotel search failed: {r2.status_code}")
            return []

        hotels_raw = r2.json().get("data", {}).get("hotels", [])[:6]

        results = []
        for h in hotels_raw:
            prop = h.get("property", {})
            price_info = h.get("priceBreakdown", {}).get("grossPrice", {})
            price = price_info.get("value", 0)
            hotel_name = prop.get("name", "Hotel")
            photo_urls = prop.get("photoUrls", [])

            results.append({
                "name": hotel_name,
                "stars": prop.get("accuratePropertyClass", 3),
                "rating": prop.get("reviewScore", 0),
                "review_count": prop.get("reviewCount", 0),
                "price_per_night_gbp": round(price, 2),
                "image_url": photo_urls[0] if photo_urls else None,
                "booking_url": make_booking_url(hotel_name, city),
                "search_url": make_booking_city_url(city, checkin, checkout),
                "location": prop.get("wishlistName", city),
                "amenities": [],
                "source": "booking.com",
            })

        return results

    except Exception as e:
        print(f"[Booking.com] Error: {e}")
        return []
