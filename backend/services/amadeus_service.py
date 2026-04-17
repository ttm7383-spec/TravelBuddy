"""
TravelBuddy - Amadeus API Service
====================================
Provides real-time flight and hotel search using the Amadeus API.
Falls back to mock data gracefully if API is unavailable or unconfigured.

Dependencies: pip install amadeus
"""

import os
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# IATA Code Cache — avoids repeated API lookups for common cities
# ---------------------------------------------------------------------------
import random

IATA_CACHE = {
    # UK
    "london": "LON", "london heathrow": "LHR", "london gatwick": "LGW",
    "manchester": "MAN", "birmingham": "BHX", "edinburgh": "EDI",
    "glasgow": "GLA", "bristol": "BRS", "liverpool": "LPL",
    "leeds": "LBA", "newcastle": "NCL",
    # Western Europe
    "paris": "CDG", "barcelona": "BCN", "madrid": "MAD",
    "rome": "FCO", "amsterdam": "AMS", "berlin": "BER",
    "lisbon": "LIS", "porto": "OPO", "athens": "ATH",
    "prague": "PRG", "budapest": "BUD", "vienna": "VIE",
    "zurich": "ZRH", "copenhagen": "CPH", "stockholm": "ARN",
    "krakow": "KRK", "warsaw": "WAW", "dublin": "DUB",
    "nice": "NCE", "milan": "MXP", "venice": "VCE",
    "seville": "SVQ", "valencia": "VLC", "malaga": "AGP",
    "dubrovnik": "DBV", "split": "SPU",
    # Eastern Europe & Balkans
    "istanbul": "IST", "tbilisi": "TBS", "sarajevo": "SJJ",
    "belgrade": "BEG", "sofia": "SOF", "bucharest": "OTP",
    "riga": "RIX", "tallinn": "TLL", "vilnius": "VNO",
    # Middle East
    "dubai": "DXB", "abu dhabi": "AUH", "doha": "DOH",
    # Asia
    "bangkok": "BKK", "tokyo": "NRT", "osaka": "KIX",
    "kyoto": "KIX", "seoul": "ICN", "singapore": "SIN",
    "bali": "DPS", "hong kong": "HKG", "taipei": "TPE",
    "hanoi": "HAN", "ho chi minh city": "SGN",
    "chiang mai": "CNX", "kathmandu": "KTM",
    "colombo": "CMB", "kuala lumpur": "KUL",
    # Americas
    "new york": "JFK", "new york city": "JFK",
    "los angeles": "LAX", "miami": "MIA", "cancun": "CUN",
    "toronto": "YYZ", "vancouver": "YVR",
    "mexico city": "MEX", "bogota": "BOG",
    "lima": "LIM", "buenos aires": "EZE",
    "rio de janeiro": "GIG", "sao paulo": "GRU",
    "orlando": "MCO", "san francisco": "SFO",
    "san jose": "SJO", "costa rica": "SJO",
    # Africa
    "cape town": "CPT", "johannesburg": "JNB",
    "marrakech": "RAK", "cairo": "CAI",
    "nairobi": "NBO", "zanzibar": "ZNZ", "zanzibar city": "ZNZ",
    # Oceania
    "sydney": "SYD", "melbourne": "MEL", "queenstown": "ZQN",
    # Islands
    "male": "MLE", "maldives": "MLE", "mauritius": "MRU",
    "santorini": "JTR", "mykonos": "JMK",
    "reykjavik": "KEF", "interlaken": "ZRH",
}

# ---------------------------------------------------------------------------
# Price estimates for common routes (when Amadeus returns nothing)
# Format: "ORIGIN-DEST": (min_price_gbp, max_price_gbp)
# ---------------------------------------------------------------------------
PRICE_ESTIMATES = {
    "LON-BCN": (35, 250), "LON-MAD": (40, 280), "LON-VLC": (45, 260),
    "LON-CDG": (38, 200), "LON-AMS": (40, 180), "LON-FCO": (45, 300),
    "LON-ATH": (60, 350), "LON-IST": (55, 400), "LON-PRG": (35, 220),
    "LON-BUD": (35, 200), "LON-KRK": (30, 180), "LON-LIS": (28, 250),
    "LON-DXB": (200, 800), "LON-BKK": (350, 900), "LON-NRT": (400, 1200),
    "LON-SIN": (380, 950), "LON-DPS": (420, 1000), "LON-SYD": (600, 1800),
    "LON-JFK": (280, 900), "LON-CPT": (400, 1100), "LON-MLE": (450, 1500),
    "LON-RAK": (30, 200), "LON-HAN": (380, 850), "LON-MEX": (400, 1000),
    "LON-CMB": (350, 800), "LON-ZNZ": (380, 900), "LON-KEF": (50, 300),
    "LON-MCO": (300, 900), "LON-ZQN": (650, 1900), "LON-JTR": (80, 400),
    "LON-VIE": (40, 220), "LON-BER": (30, 180), "LON-CPH": (35, 200),
    "LON-ARN": (40, 220), "LON-DBV": (50, 280), "LON-NCE": (35, 200),
    "LON-MXP": (35, 200), "LON-AGP": (30, 180),
}

# Common airlines that fly from London to various regions
REGIONAL_AIRLINES = {
    "europe_short": [
        ("Ryanair", "FR"), ("easyJet", "U2"), ("Wizz Air", "W6"), ("Vueling", "VY"),
    ],
    "europe_long": [
        ("British Airways", "BA"), ("Turkish Airlines", "TK"), ("Lufthansa", "LH"),
    ],
    "middle_east": [
        ("Emirates", "EK"), ("Qatar Airways", "QR"), ("Etihad Airways", "EY"),
    ],
    "asia": [
        ("Emirates", "EK"), ("Qatar Airways", "QR"), ("Singapore Airlines", "SQ"),
        ("Thai Airways", "TG"),
    ],
    "americas": [
        ("British Airways", "BA"), ("Virgin Atlantic", "VS"), ("Norwegian", "DY"),
    ],
    "africa": [
        ("British Airways", "BA"), ("Ethiopian Airlines", "ET"), ("Turkish Airlines", "TK"),
    ],
    "oceania": [
        ("Qantas", "QF"), ("Emirates", "EK"), ("Singapore Airlines", "SQ"),
    ],
}

# Rough flight hours from London by destination IATA
FLIGHT_HOURS = {
    "BCN": 2.2, "MAD": 2.5, "VLC": 2.3, "CDG": 1.2, "AMS": 1.3, "FCO": 2.5,
    "ATH": 3.5, "IST": 3.5, "PRG": 2.0, "BUD": 2.5, "KRK": 2.5, "LIS": 2.8,
    "DXB": 6.5, "BKK": 11.5, "NRT": 11.5, "SIN": 12.5, "DPS": 16, "SYD": 22,
    "JFK": 8, "CPT": 11, "MLE": 10, "RAK": 3.5, "HAN": 11, "MEX": 12,
    "CMB": 10, "ZNZ": 10, "KEF": 3.5, "MCO": 9, "ZQN": 24, "JTR": 3.5,
    "VIE": 2.3, "BER": 2, "CPH": 2, "ARN": 2.5, "DBV": 2.5, "NCE": 2,
    "MXP": 2, "AGP": 2.8,
}

# ---------------------------------------------------------------------------
# Airline code → name lookup (50 major airlines)
# ---------------------------------------------------------------------------
AIRLINE_NAMES = {
    "BA": "British Airways", "EK": "Emirates", "LH": "Lufthansa",
    "FR": "Ryanair", "U2": "easyJet", "TK": "Turkish Airlines",
    "QR": "Qatar Airways", "EY": "Etihad Airways", "VS": "Virgin Atlantic",
    "AF": "Air France", "KL": "KLM", "IB": "Iberia",
    "AA": "American Airlines", "UA": "United Airlines", "DL": "Delta",
    "SQ": "Singapore Airlines", "CX": "Cathay Pacific", "QF": "Qantas",
    "NZ": "Air New Zealand", "EI": "Aer Lingus", "AY": "Finnair",
    "SK": "SAS Scandinavian", "LX": "Swiss International", "OS": "Austrian Airlines",
    "TP": "TAP Portugal", "AZ": "ITA Airways", "VY": "Vueling",
    "W6": "Wizz Air", "PC": "Pegasus Airlines", "SV": "Saudia",
    "WN": "Southwest Airlines", "B6": "JetBlue", "AC": "Air Canada",
    "JL": "Japan Airlines", "NH": "ANA", "KE": "Korean Air",
    "OZ": "Asiana Airlines", "CI": "China Airlines", "BR": "EVA Air",
    "MH": "Malaysia Airlines", "GA": "Garuda Indonesia", "TG": "Thai Airways",
    "VN": "Vietnam Airlines", "AI": "Air India", "PK": "PIA",
    "ET": "Ethiopian Airlines", "SA": "South African Airways",
    "WS": "WestJet", "FI": "Icelandair", "DY": "Norwegian",
}

# ---------------------------------------------------------------------------
# Mock data paths
# ---------------------------------------------------------------------------
_MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data")
_CITY_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "city_data.json")

# Load city-specific data (real hotel names, restaurants, attractions per city)
try:
    with open(_CITY_DATA_PATH, "r", encoding="utf-8") as f:
        CITY_DATA = json.load(f)
except FileNotFoundError:
    CITY_DATA = {}


def _load_mock(filename):
    path = os.path.join(_MOCK_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Booking URL generators — real deep links, no API key needed
# ---------------------------------------------------------------------------

def make_google_flights_url(origin_iata, dest_iata, depart_date, return_date=None):
    """Generate a Google Flights deep link."""
    url = f"https://www.google.com/travel/flights?q=Flights+from+{origin_iata}+to+{dest_iata}"
    if depart_date:
        url += f"+on+{depart_date}"
    if return_date:
        url += f"+returning+{return_date}"
    return url


def make_skyscanner_url(origin_iata, dest_iata, depart_date, return_date=None, adults=1):
    """Generate a Skyscanner deep link."""
    d = depart_date.replace("-", "") if depart_date else ""
    r = return_date.replace("-", "") if return_date else ""
    path = f"{origin_iata.lower()}/{dest_iata.lower()}/{d}"
    if r:
        path += f"/{r}"
    return f"https://www.skyscanner.net/transport/flights/{path}/?adults={adults}"


def make_booking_url(hotel_name, city_name):
    """Generate a Booking.com search URL for a hotel."""
    from urllib.parse import quote_plus
    q = quote_plus(f"{hotel_name} {city_name}")
    return f"https://www.booking.com/searchresults.html?ss={q}"


def make_booking_city_url(city_name, checkin, checkout):
    """Generate a Booking.com city search URL."""
    from urllib.parse import quote_plus
    return f"https://www.booking.com/searchresults.html?ss={quote_plus(city_name)}&checkin={checkin}&checkout={checkout}"


def get_city_data(city_name):
    """Get city-specific data (hotels, restaurants, attractions, flights).
    Falls back to generic mock data if city not found."""
    # Try exact match first, then case-insensitive
    if city_name in CITY_DATA:
        return CITY_DATA[city_name]
    for key in CITY_DATA:
        if key.lower() == city_name.lower():
            return CITY_DATA[key]
    return None


def _get_iata(city_name, amadeus_client=None):
    """Resolve a city name to an IATA code."""
    key = city_name.lower().strip()
    if key in IATA_CACHE:
        return IATA_CACHE[key]

    # Try Amadeus API lookup if client is available
    if amadeus_client:
        try:
            resp = amadeus_client.reference_data.locations.get(
                keyword=city_name, subType="CITY,AIRPORT"
            )
            if resp.data:
                code = resp.data[0]["iataCode"]
                IATA_CACHE[key] = code
                return code
        except Exception as e:
            print(f"[Amadeus] IATA lookup failed for '{city_name}': {e}")

    return None


def _format_duration(iso_duration):
    """Convert ISO 8601 duration (PT2H45M) to human-readable (2h 45m)."""
    if not iso_duration:
        return "N/A"
    d = iso_duration.replace("PT", "")
    hours = minutes = 0
    if "H" in d:
        parts = d.split("H")
        hours = int(parts[0])
        d = parts[1]
    if "M" in d:
        minutes = int(d.replace("M", ""))
    if hours and minutes:
        return f"{hours}h {minutes:02d}m"
    elif hours:
        return f"{hours}h 00m"
    else:
        return f"{minutes}m"


def _get_amadeus_client():
    """Create an Amadeus client if keys are configured."""
    api_key = os.getenv("AMADEUS_API_KEY", "")
    api_secret = os.getenv("AMADEUS_API_SECRET", "")

    if not api_key or api_key == "your_amadeus_api_key":
        return None

    try:
        from amadeus import Client
        return Client(client_id=api_key, client_secret=api_secret)
    except ImportError:
        print("[Amadeus] Package not installed. Run: pip install amadeus")
        return None
    except Exception as e:
        print(f"[Amadeus] Client init failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Flight Search
# ---------------------------------------------------------------------------

def search_flights(origin_city, destination_city, departure_date, return_date=None, adults=1):
    """
    Search for flights using Amadeus API with mock fallback.

    Returns:
        dict with keys: flights (list), is_mock (bool), updated_at (str)
    """
    use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

    if not use_mock:
        client = _get_amadeus_client()
        if client:
            try:
                origin_iata = _get_iata(origin_city, client)
                dest_iata = _get_iata(destination_city, client)

                if not origin_iata or not dest_iata:
                    print(f"[Amadeus] Could not resolve IATA: {origin_city}={origin_iata}, {destination_city}={dest_iata}")
                    return _mock_flights(origin_city, destination_city, departure_date)

                params = {
                    "originLocationCode": origin_iata,
                    "destinationLocationCode": dest_iata,
                    "departureDate": departure_date,
                    "adults": adults,
                    "currencyCode": "GBP",
                    "max": 5,
                }
                if return_date:
                    params["returnDate"] = return_date

                response = client.shopping.flight_offers_search.get(**params)
                flights = []

                for offer in response.data:
                    # Parse outbound segment
                    itinerary = offer["itineraries"][0]
                    first_seg = itinerary["segments"][0]
                    last_seg = itinerary["segments"][-1]
                    stops = len(itinerary["segments"]) - 1
                    carrier_code = first_seg.get("carrierCode", "??")

                    flights.append({
                        "id": offer.get("id", ""),
                        "airline": AIRLINE_NAMES.get(carrier_code, carrier_code),
                        "airline_code": carrier_code,
                        "flight_number": f"{carrier_code}{first_seg.get('number', '')}",
                        "price_gbp": float(offer["price"]["total"]),
                        "price_per_person_gbp": round(float(offer["price"]["total"]) / adults, 2),
                        "departure": {
                            "airport": first_seg["departure"]["iataCode"],
                            "time": first_seg["departure"]["at"].split("T")[1][:5],
                            "date": first_seg["departure"]["at"].split("T")[0],
                            "city": origin_city,
                        },
                        "arrival": {
                            "airport": last_seg["arrival"]["iataCode"],
                            "time": last_seg["arrival"]["at"].split("T")[1][:5],
                            "date": last_seg["arrival"]["at"].split("T")[0],
                            "city": destination_city,
                        },
                        "duration": _format_duration(itinerary.get("duration", "")),
                        "stops": stops,
                        "stops_label": "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}",
                        "cabin_class": "Economy",
                        "baggage_included": True,
                    })

                flights.sort(key=lambda f: f["price_gbp"])

                # Add booking URLs to every flight
                for fl in flights:
                    fl["google_flights_url"] = make_google_flights_url(
                        origin_iata, dest_iata, departure_date, return_date)
                    fl["skyscanner_url"] = make_skyscanner_url(
                        origin_iata, dest_iata, departure_date, return_date, adults)

                # Mark cheapest and fastest
                if flights:
                    flights[0]["badge"] = "cheapest"
                    fastest = min(flights, key=lambda f: f["duration"])
                    if fastest["id"] != flights[0]["id"]:
                        fastest["badge"] = "fastest"

                return {
                    "flights": flights,
                    "is_mock": False,
                    "updated_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                print(f"[Amadeus] Flight search error: {e}")

    return _mock_flights(origin_city, destination_city, departure_date)


def _mock_flights(origin_city, destination_city, departure_date):
    """Return city-specific mock flights, or generate realistic ones dynamically."""
    city = get_city_data(destination_city)
    origin_iata = IATA_CACHE.get(origin_city.lower(), "LHR")
    dest_iata = IATA_CACHE.get(destination_city.lower(), "")

    if city and "flights_from_london" in city:
        # Use curated city-specific flight data
        flights = []
        for f in city["flights_from_london"]:
            flights.append({
                "airline": f["airline"],
                "airline_code": f["airline_code"],
                "flight_number": f"{f['airline_code']}{random.randint(100,999)}",
                "price_gbp": f["price_gbp"],
                "price_per_person_gbp": f["price_gbp"],
                "departure": {"airport": origin_iata, "city": origin_city,
                              "time": f["departure_time"], "date": departure_date},
                "arrival": {"airport": dest_iata, "city": destination_city,
                            "time": f["arrival_time"], "date": departure_date},
                "duration": f["duration"],
                "stops": f["stops"],
                "stops_label": f["stops_label"],
                "cabin_class": "Economy",
                "baggage_included": f["price_gbp"] > 100,
                "badge": None,
            })
    else:
        # Dynamically generate realistic flights for ANY destination
        flights = _generate_dynamic_flights(origin_city, destination_city, departure_date)

    if flights:
        flights.sort(key=lambda x: x["price_gbp"])
        flights[0]["badge"] = "cheapest"
        if len(flights) > 1:
            fastest = min(flights, key=lambda x: x["duration"])
            if fastest is not flights[0]:
                fastest["badge"] = "fastest"

    # Add booking URLs to every flight
    oi = IATA_CACHE.get(origin_city.lower(), "LHR")
    di = IATA_CACHE.get(destination_city.lower(), "")
    for fl in flights:
        fl["google_flights_url"] = make_google_flights_url(oi, di, departure_date)
        fl["skyscanner_url"] = make_skyscanner_url(oi, di, departure_date)

    return {"flights": flights, "is_mock": True, "updated_at": datetime.utcnow().isoformat()}


def _generate_dynamic_flights(origin_city, destination_city, departure_date):
    """Generate 3 realistic mock flights for any origin→destination pair."""
    origin_iata = IATA_CACHE.get(origin_city.lower(), "LHR")
    dest_iata = IATA_CACHE.get(destination_city.lower(), destination_city[:3].upper())

    # Estimate price range
    route_key = f"{origin_iata}-{dest_iata}"
    lon_key = f"LON-{dest_iata}"
    if route_key in PRICE_ESTIMATES:
        price_min, price_max = PRICE_ESTIMATES[route_key]
    elif lon_key in PRICE_ESTIMATES:
        price_min, price_max = PRICE_ESTIMATES[lon_key]
    else:
        # Estimate based on flight hours
        hours = FLIGHT_HOURS.get(dest_iata, 5)
        price_min = int(50 + hours * 25)
        price_max = int(150 + hours * 60)

    # Pick airlines based on rough region
    hours = FLIGHT_HOURS.get(dest_iata, 5)
    if hours <= 3:
        region = "europe_short"
    elif hours <= 5:
        region = "europe_long"
    elif dest_iata in ("DXB", "AUH", "DOH"):
        region = "middle_east"
    elif dest_iata in ("JFK", "LAX", "MIA", "MCO", "YYZ", "MEX", "CUN", "EZE", "GIG"):
        region = "americas"
    elif dest_iata in ("SYD", "MEL", "ZQN"):
        region = "oceania"
    elif dest_iata in ("CPT", "JNB", "NBO", "ZNZ", "CAI", "RAK"):
        region = "africa"
    else:
        region = "asia"

    airlines = REGIONAL_AIRLINES.get(region, REGIONAL_AIRLINES["europe_long"])
    selected_airlines = random.sample(airlines, min(3, len(airlines)))
    # Always include BA as a reliable option
    if not any(a[1] == "BA" for a in selected_airlines):
        selected_airlines[-1] = ("British Airways", "BA")

    flights = []
    dep_hours = [6, 9, 14]  # morning, mid-morning, afternoon departures
    for i, (airline_name, airline_code) in enumerate(selected_airlines):
        # Price: budget carrier cheapest, flag carrier most expensive
        price_frac = (i + 0.5) / len(selected_airlines)
        price = int(price_min + (price_max - price_min) * price_frac)
        price = price + random.randint(-15, 15)  # slight randomness

        is_direct = (i == 0 and hours < 8) or hours < 4
        actual_hours = hours if is_direct else hours + 2.5
        dur_h = int(actual_hours)
        dur_m = int((actual_hours - dur_h) * 60)

        dep_h = dep_hours[i % len(dep_hours)]
        arr_h = (dep_h + dur_h) % 24
        arr_m = (0 + dur_m) % 60

        flights.append({
            "airline": airline_name,
            "airline_code": airline_code,
            "flight_number": f"{airline_code}{random.randint(100,999)}",
            "price_gbp": max(price, 20),
            "price_per_person_gbp": max(price, 20),
            "departure": {
                "airport": IATA_CACHE.get(origin_city.lower(), "LHR"),
                "city": origin_city,
                "time": f"{dep_h:02d}:{random.choice(['00','15','30','45'])}",
                "date": departure_date,
            },
            "arrival": {
                "airport": dest_iata or destination_city[:3].upper(),
                "city": destination_city,
                "time": f"{arr_h:02d}:{arr_m:02d}",
                "date": departure_date,
            },
            "duration": f"{dur_h}h {dur_m:02d}m",
            "stops": 0 if is_direct else 1,
            "stops_label": "Direct" if is_direct else "1 stop",
            "cabin_class": "Economy",
            "baggage_included": price > 80,
            "badge": None,
        })

    return flights


# ---------------------------------------------------------------------------
# Hotel Search
# ---------------------------------------------------------------------------

def search_hotels(city_name, check_in, check_out, adults=1, budget_level="medium"):
    """
    Search for hotels using Amadeus API with mock fallback.

    Returns:
        dict with keys: hotels (list), is_mock (bool), updated_at (str)
    """
    use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

    # Calculate nights
    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (co - ci).days
    except ValueError:
        nights = 7

    if nights <= 0:
        nights = 7

    if not use_mock:
        client = _get_amadeus_client()
        if client:
            try:
                city_iata = _get_iata(city_name, client)
                if not city_iata:
                    return _mock_hotels(city_name, nights, budget_level)

                # Step 1: Find hotels in city
                hotel_list = client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_iata
                )
                hotel_ids = [h["hotelId"] for h in hotel_list.data[:10]]

                if not hotel_ids:
                    return _mock_hotels(city_name, nights, budget_level)

                # Step 2: Get offers
                offers = client.shopping.hotel_offers_search.get(
                    hotelIds=hotel_ids,
                    checkInDate=check_in,
                    checkOutDate=check_out,
                    adults=adults,
                    currencyCode="GBP",
                    bestRateOnly=True,
                )

                hotels = []
                for hotel_offer in offers.data:
                    h = hotel_offer.get("hotel", {})
                    offer = hotel_offer.get("offers", [{}])[0]
                    price = offer.get("price", {})
                    total = float(price.get("total", 0))
                    per_night = round(total / nights, 2) if nights > 0 else total

                    # Filter by budget
                    if budget_level == "low" and per_night > 80:
                        continue
                    elif budget_level == "medium" and (per_night < 80 or per_night > 200):
                        continue
                    elif budget_level == "high" and per_night < 200:
                        continue

                    rating = int(h.get("rating", 3))
                    rating_labels = {1: "Budget", 2: "Economy", 3: "Standard", 4: "Superior", 5: "Luxury"}

                    cancel = offer.get("policies", {}).get("cancellation", {})
                    cancel_text = "Free cancellation" if cancel.get("type") == "FREE" else "Non-refundable"

                    board = offer.get("boardType", "ROOM_ONLY")
                    board_labels = {
                        "ROOM_ONLY": "Room Only",
                        "BREAKFAST": "Breakfast Included",
                        "ALL_INCLUSIVE": "All Inclusive",
                    }

                    hotel_name = h.get("name", "Hotel")
                    hotels.append({
                        "hotel_id": h.get("hotelId", ""),
                        "name": hotel_name,
                        "price_per_night_gbp": per_night,
                        "total_price_gbp": total,
                        "rating": rating,
                        "stars": rating,
                        "rating_label": rating_labels.get(rating, "Standard"),
                        "amenities": [],
                        "check_in": check_in,
                        "check_out": check_out,
                        "nights": nights,
                        "room_type": offer.get("room", {}).get("description", {}).get("text", "Standard Room"),
                        "cancellation": cancel_text,
                        "board_type": board_labels.get(board, "Room Only"),
                        "is_available": True,
                        "distance_to_centre": "N/A",
                        "booking_url": make_booking_url(hotel_name, city_name),
                        "search_url": make_booking_city_url(city_name, check_in, check_out),
                    })

                hotels.sort(key=lambda h: h["price_per_night_gbp"])

                return {
                    "hotels": hotels[:5],
                    "is_mock": False,
                    "updated_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                print(f"[Amadeus] Hotel search error: {e}")

    return _mock_hotels(city_name, nights, budget_level)


def _mock_hotels(city_name, nights, budget_level):
    """Return city-specific mock hotel data, or generate dynamically."""
    city = get_city_data(city_name)
    rating_labels = {1: "Budget", 2: "Economy", 3: "Standard", 4: "Superior", 5: "Luxury"}

    if city and "hotels" in city:
        hotels = []
        for h in city["hotels"]:
            hname = h["name"]
            hotels.append({
                "name": hname,
                "price_per_night_gbp": h["price_per_night_gbp"],
                "total_price_gbp": round(h["price_per_night_gbp"] * nights, 2),
                "rating": h["rating"],
                "stars": h["stars"],
                "rating_label": rating_labels.get(h["stars"], "Standard"),
                "amenities": h.get("amenities", []),
                "room_type": h.get("room_type", "Standard Room"),
                "cancellation": h.get("cancellation", "Free cancellation"),
                "board_type": h.get("board_type", "Room Only"),
                "is_available": True,
                "nights": nights,
                "distance_to_centre": "City centre",
                "booking_url": make_booking_url(hname, city_name),
                "search_url": make_booking_city_url(city_name, "", ""),
            })
    else:
        # Generate destination-specific hotel names dynamically
        hotels = _generate_dynamic_hotels(city_name, nights)

    return {"hotels": hotels, "is_mock": True, "updated_at": datetime.utcnow().isoformat()}


_BUDGET_CHAINS = [
    "Generator", "Selina", "Moxy by Marriott", "MEININGER", "a]o Hostel",
    "Wombats", "The People Hostel", "Ibis Budget", "easyHotel", "Safestay",
]
_MID_CHAINS = [
    "Ibis Styles", "Holiday Inn Express", "Novotel", "NH Hotel",
    "Mercure", "Best Western", "Radisson RED", "Hampton by Hilton",
    "Courtyard by Marriott", "AC Hotel by Marriott",
]
_LUX_CHAINS = [
    "InterContinental", "Hilton", "Sofitel", "W Hotel",
    "Marriott", "Hyatt Regency", "The Ritz-Carlton", "Mandarin Oriental",
    "Four Seasons", "Fairmont",
]


def _generate_dynamic_hotels(city_name, nights):
    """Generate 6 realistic hotels with real chain names for any destination."""
    name = city_name.split(",")[0].strip()

    budget_names = random.sample(_BUDGET_CHAINS, 2)
    mid_names = random.sample(_MID_CHAINS, 2)
    lux_names = random.sample(_LUX_CHAINS, 2)

    hotels = [
        {
            "name": f"{budget_names[0]} {name}",
            "price_per_night_gbp": random.randint(22, 45),
            "rating": round(random.uniform(3.8, 4.2), 1),
            "stars": 2, "rating_label": "Economy",
            "amenities": ["Free WiFi", "24h Reception", "Shared Kitchen", "Lounge"],
            "room_type": "Private Double Room", "cancellation": "Free cancellation",
            "board_type": "Room Only", "is_available": True, "nights": nights,
            "neighbourhood": "City Centre", "distance_to_centre": "0.8 km",
            "review_count": random.randint(800, 3500),
        },
        {
            "name": f"{budget_names[1]} {name}",
            "price_per_night_gbp": random.randint(30, 55),
            "rating": round(random.uniform(3.6, 4.1), 1),
            "stars": 2, "rating_label": "Economy",
            "amenities": ["Free WiFi", "Bar", "Laundry"],
            "room_type": "Standard Double", "cancellation": "Free cancellation",
            "board_type": "Room Only", "is_available": True, "nights": nights,
            "neighbourhood": "Old Town", "distance_to_centre": "1.2 km",
            "review_count": random.randint(500, 2000),
        },
        {
            "name": f"{mid_names[0]} {name}",
            "price_per_night_gbp": random.randint(75, 130),
            "rating": round(random.uniform(4.2, 4.5), 1),
            "stars": 3, "rating_label": "Standard",
            "amenities": ["Free WiFi", "Breakfast Included", "Gym", "Air Conditioning"],
            "room_type": "Superior Double Room", "cancellation": "Free cancellation",
            "board_type": "Breakfast Included", "is_available": True, "nights": nights,
            "neighbourhood": "City Centre", "distance_to_centre": "0.3 km",
            "review_count": random.randint(1500, 6000),
        },
        {
            "name": f"{mid_names[1]} {name}",
            "price_per_night_gbp": random.randint(90, 160),
            "rating": round(random.uniform(4.3, 4.6), 1),
            "stars": 4, "rating_label": "Superior",
            "amenities": ["Free WiFi", "Breakfast Included", "Pool", "Gym", "Restaurant", "Bar"],
            "room_type": "Deluxe Double Room", "cancellation": "Free cancellation",
            "board_type": "Breakfast Included", "is_available": True, "nights": nights,
            "neighbourhood": "Business District", "distance_to_centre": "0.5 km",
            "review_count": random.randint(2000, 8000),
        },
        {
            "name": f"{lux_names[0]} {name}",
            "price_per_night_gbp": random.randint(200, 350),
            "rating": round(random.uniform(4.6, 4.9), 1),
            "stars": 5, "rating_label": "Luxury",
            "amenities": ["Spa", "Pool", "Fine Dining", "Room Service", "Concierge", "Gym", "Rooftop Bar"],
            "room_type": "Deluxe Suite", "cancellation": "Non-refundable",
            "board_type": "Breakfast Included", "is_available": True, "nights": nights,
            "neighbourhood": "Premium District", "distance_to_centre": "0.2 km",
            "review_count": random.randint(3000, 12000),
        },
        {
            "name": f"{lux_names[1]} {name}",
            "price_per_night_gbp": random.randint(280, 500),
            "rating": round(random.uniform(4.7, 4.9), 1),
            "stars": 5, "rating_label": "Luxury",
            "amenities": ["Spa", "Infinity Pool", "Michelin Restaurant", "Butler Service", "City Views"],
            "room_type": "Grand Suite", "cancellation": "Non-refundable",
            "board_type": "Half Board", "is_available": True, "nights": nights,
            "neighbourhood": "Waterfront", "distance_to_centre": "City centre",
            "review_count": random.randint(5000, 15000),
        },
    ]
    for h in hotels:
        h["total_price_gbp"] = round(h["price_per_night_gbp"] * nights, 2)
        h["booking_url"] = make_booking_url(h["name"], city_name)
        h["search_url"] = make_booking_city_url(city_name, "", "")
    return hotels


# ---------------------------------------------------------------------------
# Cheapest Month Search
# ---------------------------------------------------------------------------

def get_cheapest_month(origin_city, destination_city):
    """
    Find the cheapest month to fly using Amadeus Flight Inspiration Search.
    Falls back to a static estimate if API is unavailable.
    """
    client = _get_amadeus_client()
    origin_iata = IATA_CACHE.get(origin_city.lower(), "LON")
    dest_iata = IATA_CACHE.get(destination_city.lower())

    if client and dest_iata:
        try:
            resp = client.shopping.flight_destinations.get(
                origin=origin_iata,
                destination=dest_iata,
                oneWay=False,
                nonStop=False,
            )
            if resp.data:
                cheapest = min(resp.data, key=lambda x: float(x.get("price", {}).get("total", 9999)))
                dep = cheapest.get("departureDate", "")
                return {
                    "cheapest_departure": dep,
                    "cheapest_price_gbp": float(cheapest["price"]["total"]),
                    "currency": "GBP",
                    "is_live": True,
                }
        except Exception as e:
            print(f"[Amadeus] Cheapest month search error: {e}")

    # Static fallback — return general cheapest months by region
    hours = FLIGHT_HOURS.get(dest_iata, 5)
    if hours <= 4:
        return {"cheapest_month": "January-February", "note": "Low season for European short-haul", "is_live": False}
    elif dest_iata in ("BKK", "HAN", "SGN", "CNX", "DPS", "KUL", "SIN"):
        return {"cheapest_month": "May-June", "note": "Shoulder season before summer holidays", "is_live": False}
    else:
        return {"cheapest_month": "January-March", "note": "Post-holiday low season", "is_live": False}
