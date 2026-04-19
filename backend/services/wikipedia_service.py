"""
Wikipedia API service — fetches real local knowledge for cities and countries
so the AI Concierge can ground its responses in verifiable public data rather
than relying purely on the model's training set.
"""

import re

import wikipediaapi


wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="TravelBuddy/1.0 (university dissertation project)",
)


def get_city_knowledge(city, country):
    """
    Fetch rich local knowledge from Wikipedia for any city.
    Returns structured dict with neighbourhoods, history, food, transport,
    attractions.
    """
    result = {
        "summary": "",
        "neighbourhoods": [],
        "attractions": [],
        "food_culture": "",
        "transport": "",
        "history": "",
        "best_areas": [],
    }

    page = wiki.page(city)
    if page.exists():
        result["summary"] = page.summary[:600]

    for suffix in [
        f"Neighbourhoods in {city}",
        f"Districts of {city}",
        f"{city} districts",
        f"Areas of {city}",
    ]:
        nbr_page = wiki.page(suffix)
        if nbr_page.exists():
            result["neighbourhoods"] = _extract_list(nbr_page.summary)
            break

    for suffix in [
        f"{city} cuisine",
        f"Cuisine of {city}",
        f"{country} cuisine",
    ]:
        food_page = wiki.page(suffix)
        if food_page.exists():
            result["food_culture"] = food_page.summary[:400]
            break

    for suffix in [
        f"Transport in {city}",
        f"{city} public transport",
        f"{city} Metro",
        f"{city} Underground",
    ]:
        transport_page = wiki.page(suffix)
        if transport_page.exists():
            result["transport"] = transport_page.summary[:300]
            break

    for suffix in [
        f"Tourism in {city}",
        f"Landmarks in {city}",
        f"Attractions in {city}",
    ]:
        attr_page = wiki.page(suffix)
        if attr_page.exists():
            result["attractions"] = _extract_list(attr_page.summary)
            break

    return result


def get_country_knowledge(country):
    """
    Fetch country-level knowledge including major cities, culture, and
    travel context.
    """
    result = {
        "summary": "",
        "major_cities": [],
        "regions": [],
        "culture": "",
        "best_time": "",
    }

    page = wiki.page(country)
    if page.exists():
        result["summary"] = page.summary[:500]

    for suffix in [
        f"Cities in {country}",
        f"List of cities in {country}",
        f"Major cities of {country}",
    ]:
        cities_page = wiki.page(suffix)
        if cities_page.exists():
            result["major_cities"] = _extract_list(cities_page.summary)[:8]
            break

    culture_page = wiki.page(f"Culture of {country}")
    if culture_page.exists():
        result["culture"] = culture_page.summary[:300]

    return result


def get_attraction_detail(attraction, city):
    """
    Get detailed Wikipedia info about a specific attraction.
    Returns opening context, history, what makes it special.
    """
    page = wiki.page(f"{attraction} {city}")
    if not page.exists():
        page = wiki.page(attraction)
    if page.exists():
        return page.summary[:400]
    return ""


def get_neighbourhood_detail(neighbourhood, city):
    """
    Get detailed Wikipedia info about a specific neighbourhood.
    """
    page = wiki.page(f"{neighbourhood}, {city}")
    if not page.exists():
        page = wiki.page(neighbourhood)
    if page.exists():
        return page.summary[:300]
    return ""


def _extract_list(text):
    """Extract named items from Wikipedia summary text."""
    sentences = text.split(".")
    items = []
    for sentence in sentences[:5]:
        words = re.findall(r"\b[A-Z][a-zA-Z\s]{3,25}\b", sentence)
        items.extend([w.strip() for w in words if len(w.strip()) > 4])
    return list(dict.fromkeys(items))[:8]
