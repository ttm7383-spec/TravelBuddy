"""
Real-world places service — uses the OpenStreetMap Overpass API (free, no
API key required) to fetch real hotels, restaurants, cafes, bars, pubs and
fast-food spots by city name. The AI Concierge falls back to this when it
isn't using Claude so card listings show real names instead of placeholders.

Overpass docs: https://wiki.openstreetmap.org/wiki/Overpass_API
"""

import time

import requests


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

_CATEGORY_TAGS = {
    "hotel":       ['["tourism"="hotel"]'],
    "hostel":      ['["tourism"="hostel"]'],
    "guesthouse":  ['["tourism"="guest_house"]'],
    "restaurant":  ['["amenity"="restaurant"]'],
    "cafe":        ['["amenity"="cafe"]'],
    "bar":         ['["amenity"="bar"]'],
    "pub":         ['["amenity"="pub"]'],
    "street_food": ['["amenity"="fast_food"]', '["amenity"="food_court"]'],
    "bakery":      ['["shop"="bakery"]'],
    "attraction":  ['["tourism"="attraction"]'],
    "museum":      ['["tourism"="museum"]'],
}

# Simple in-process cache keyed by (city, category). 1-hour TTL is plenty
# for a dissertation demo and keeps Overpass happy with its rate limits.
_CACHE = {}
_CACHE_TTL = 3600


def _cache_get(key):
    entry = _CACHE.get(key)
    if not entry:
        return None
    value, ts = entry
    if time.time() - ts > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key, value):
    _CACHE[key] = (value, time.time())


_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_BBOX_CACHE = {}
_BBOX_CACHE_TTL = 7 * 24 * 3600  # 1 week — city boundaries barely change


def _resolve_city_center(city, country=None, timeout=10):
    """
    Use Nominatim to look up the city (optionally scoped to a country) and
    return (lat, lon) of its centroid, or None on failure. Nominatim's result
    ranking disambiguates common cases like London, UK vs London, Ontario.
    """
    key = (city.strip().lower(), (country or "").strip().lower())
    cached = _BBOX_CACHE.get(key)
    if cached:
        value, ts = cached
        if time.time() - ts < _BBOX_CACHE_TTL:
            return value
    query = city if not country else f"{city}, {country}"
    try:
        resp = requests.get(
            _NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "addressdetails": 0},
            headers={"User-Agent": "TravelBuddy/1.0 (university project)"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None
        lat = float(data[0].get("lat"))
        lon = float(data[0].get("lon"))
        center = (lat, lon)
        _BBOX_CACHE[key] = (center, time.time())
        return center
    except Exception as e:
        print(f"[Places] Nominatim lookup failed for {query!r}: {e}")
        return None


def get_places(city, category, limit=6, timeout=12, country=None):
    """
    Fetch up to `limit` real places of the given category for a city.

    Parameters
    ----------
    city : str        City name as written on OSM (e.g. "Paris", "Tokyo").
    category : str    One of the keys in _CATEGORY_TAGS.
    limit : int       Max number of results to return.
    timeout : int     Overpass request timeout in seconds.
    country : str     Optional country name to disambiguate ("London" UK vs
                      "London" Ontario). When provided we restrict the area
                      lookup to the named country.

    Returns
    -------
    list[dict]   Each: { name, category, cuisine, stars, address,
                         neighbourhood, website, phone, lat, lon }.
                 Empty list on any failure — caller decides how to degrade.
    """
    if not city or not category:
        return []
    tags = _CATEGORY_TAGS.get(category)
    if not tags:
        return []

    cache_key = (city.strip().lower(), category, limit, (country or "").strip().lower())
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # Build two lightweight Overpass queries — one by native name, one by
    # name:en — and run them sequentially. The single-area query is fast;
    # the :en fallback catches cities with non-English primary names
    # (Bangkok / กรุงเทพ, Moscow / Москва, Tokyo / 東京).
    # Step 1: resolve the city to its centroid via Nominatim. Passing the
    # country (e.g. "London, United Kingdom") disambiguates cities that share
    # a name ("London" UK vs Ontario, "Cambridge" UK vs Massachusetts).
    center = _resolve_city_center(city, country, timeout)
    if not center:
        _cache_set(cache_key, [])
        return []

    lat, lon = center
    # Step 2: Overpass "around" radius query. 10 km covers central London,
    # Paris, Tokyo, Bangkok etc. in seconds — bbox queries time out on very
    # large metropolitan areas because they hit millions of nodes.
    radius_m = 10000
    tag_blocks = []
    for t in tags:
        tag_blocks.append(f"  node(around:{radius_m},{lat},{lon}){t};")
        tag_blocks.append(f"  way(around:{radius_m},{lat},{lon}){t};")
    tag_body = "\n".join(tag_blocks)
    query = (
        f"[out:json][timeout:{timeout}];\n"
        f"(\n{tag_body}\n);\n"
        f"out center tags {limit * 3};\n"
    )

    elements = []
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(
                url, data=query, timeout=timeout,
                headers={"User-Agent": "TravelBuddy/1.0 (university project)"},
            )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                if elements:
                    break
        except Exception as e:
            print(f"[Places] Overpass {url} failed: {e}")
            continue

    if not elements:
        _cache_set(cache_key, [])
        return []

    # Keep only named places, dedupe by name, prefer entries with more tags
    # (more tags = richer data), cap to `limit`.
    by_name = {}
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name") or tags.get("name:en")
        if not name:
            continue
        key = name.strip().lower()
        if key in by_name and len(by_name[key].get("tags", {})) >= len(tags):
            continue
        by_name[key] = {**el, "tags": tags}

    results = []
    for el in list(by_name.values())[:limit]:
        t = el.get("tags") or {}
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        street = " ".join(
            part for part in [t.get("addr:housenumber"), t.get("addr:street")] if part
        ).strip()
        results.append({
            "name": t.get("name") or t.get("name:en"),
            "category": category,
            "cuisine": t.get("cuisine", ""),
            "stars": t.get("stars", ""),
            "address": street or t.get("addr:full", ""),
            "neighbourhood": t.get("addr:suburb") or t.get("addr:district") or "",
            "website": t.get("website") or t.get("contact:website") or "",
            "phone": t.get("phone") or t.get("contact:phone") or "",
            "opening_hours": t.get("opening_hours", ""),
            "lat": lat, "lon": lon,
        })

    _cache_set(cache_key, results)
    return results
