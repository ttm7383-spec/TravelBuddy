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
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
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


_NOMINATIM_CATEGORY_WORDS = {
    "hotel":       "hotel",
    "hostel":      "hostel",
    "guesthouse":  "guesthouse",
    "restaurant":  "restaurant",
    "cafe":        "cafe",
    "bar":         "bar",
    "pub":         "pub",
    "street_food": "street food",
    "bakery":      "bakery",
    "attraction":  "tourist attraction",
    "museum":      "museum",
}


def _nominatim_search_category(city, category, country=None, limit=6, timeout=15):
    """
    Fallback when Overpass is overloaded. Nominatim's free-text search
    returns named POIs by text query. Slower and less precise than Overpass
    but reliable enough to surface real hotel / cafe / restaurant names.
    """
    keyword = _NOMINATIM_CATEGORY_WORDS.get(category, category)
    q = f"{keyword} in {city}, {country}" if country else f"{keyword} in {city}"
    try:
        resp = requests.get(
            _NOMINATIM_URL,
            params={
                "q": q, "format": "json", "limit": max(limit * 2, 10),
                "addressdetails": 1, "extratags": 1,
            },
            headers={"User-Agent": "TravelBuddy/1.0 (university project)"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            print(f"[Places] Nominatim category search HTTP {resp.status_code}")
            return []
        data = resp.json() or []
    except Exception as e:
        print(f"[Places] Nominatim category search failed: {e}")
        return []

    results = []
    seen = set()
    for item in data:
        name = (item.get("namedetails") or {}).get("name") or item.get("name") or item.get("display_name", "").split(",")[0]
        if not name:
            continue
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        addr = item.get("address") or {}
        street = " ".join(
            p for p in [addr.get("house_number"), addr.get("road")] if p
        ).strip()
        neighbourhood = addr.get("suburb") or addr.get("neighbourhood") or addr.get("district") or ""
        extratags = item.get("extratags") or {}
        results.append({
            "name": name,
            "category": category,
            "cuisine": extratags.get("cuisine", ""),
            "stars": extratags.get("stars", ""),
            "address": street or item.get("display_name", ""),
            "neighbourhood": neighbourhood,
            "website": extratags.get("website") or extratags.get("contact:website") or "",
            "phone": extratags.get("phone") or "",
            "opening_hours": extratags.get("opening_hours", ""),
            "lat": float(item["lat"]) if item.get("lat") else None,
            "lon": float(item["lon"]) if item.get("lon") else None,
        })
        if len(results) >= limit:
            break
    return results


def _resolve_city_center(city, country=None, timeout=15):
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


def get_places(city, category, limit=6, timeout=25, country=None):
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
    # Step 2: Overpass "around" radius query. A tight 5 km radius centred on
    # the city keeps the query small enough to complete in a few seconds on
    # the public Overpass servers — 10 km hit 504s for Paris/Barcelona/etc.
    # 5 km still covers the centre of any major city.
    radius_m = 5000
    tag_blocks = []
    for t in tags:
        tag_blocks.append(f"  node(around:{radius_m},{lat},{lon}){t};")
        tag_blocks.append(f"  way(around:{radius_m},{lat},{lon}){t};")
    tag_body = "\n".join(tag_blocks)
    # Short server-side timeout makes Overpass abort fast when the mirror is
    # overloaded so we can move on to another mirror or the Nominatim fallback.
    query = (
        f"[out:json][timeout:12];\n"
        f"(\n{tag_body}\n);\n"
        f"out center tags {limit * 3};\n"
    )

    # Short per-mirror timeout — Overpass public servers frequently 504 when
    # overloaded, and cycling through a long retry list would stall the chat
    # for 30-90 s before we fall through to Nominatim. Cap to 10 s per mirror
    # and bail the whole Overpass attempt as soon as we see a 504 cluster.
    elements = []
    per_mirror_timeout = min(timeout, 10)
    overloaded_count = 0
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(
                url, data=query, timeout=per_mirror_timeout,
                headers={"User-Agent": "TravelBuddy/1.0 (university project)"},
            )
            if resp.status_code == 200:
                payload = resp.json()
                elements = payload.get("elements", [])
                print(f"[Places] Overpass {url} returned {len(elements)} elements for {city}/{category}")
                if elements:
                    break
            else:
                print(f"[Places] Overpass {url} HTTP {resp.status_code}")
                if resp.status_code in (429, 502, 503, 504):
                    overloaded_count += 1
        except Exception as e:
            print(f"[Places] Overpass {url} failed: {e}")
            overloaded_count += 1
        # After 2 mirror failures, assume the Overpass network is overloaded
        # and skip straight to the Nominatim fallback.
        if overloaded_count >= 2 and not elements:
            print("[Places] Overpass appears overloaded — skipping to Nominatim")
            break

    if not elements:
        # Fallback: Nominatim free-text search. Slower per query and capped
        # at 10 results but usually works when Overpass is overloaded.
        nominatim_results = _nominatim_search_category(city, category, country, limit, timeout)
        if nominatim_results:
            _cache_set(cache_key, nominatim_results)
            return nominatim_results
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
