"""
fetch_europe_data.py — Build a comprehensive European destinations database
=============================================================================
Uses free APIs:
  - RestCountries (country metadata)
  - Open-Meteo (weather / peak months)
  - Hardcoded accurate data for costs, activities, highlights

Outputs: backend/recommender/destinations.json
Backs up old file as destinations_backup.json
"""

import json
import os
import shutil
import time
import requests

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DEST_PATH = os.path.join(BACKEND_DIR, "recommender", "destinations.json")
BACKUP_PATH = os.path.join(BACKEND_DIR, "recommender", "destinations_backup.json")

# ── City definitions ───────────────────────────────────────────────
# Each city has accurate, researched data that would be unreliable
# to pull from free APIs. API data supplements this.

CITIES = {
    # ── UK ──
    "london": {
        "name": "London", "country": "United Kingdom", "iata_code": "LHR",
        "latitude": 51.5074, "longitude": -0.1278,
        "avg_daily_cost_gbp": 180, "budget_level": "high",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8, 12],
        "avg_temp_c": {"spring": 12, "summer": 19, "autumn": 12, "winter": 5},
        "tags": ["culture", "history", "food", "nightlife", "shopping", "museums", "theatre", "city"],
        "suitable_for": ["solo", "couple", "family", "friends"],
        "avg_rating": 4.6, "popularity_score": 98, "safety_rating": 4,
        "sample_activities": ["Tower of London", "British Museum", "Borough Market food tour", "West End theatre show", "Camden Market"],
        "highlights": "London pulses with world-class museums (most free), legendary theatre, and a food scene spanning every cuisine on earth. From the cobbled lanes of Bermondsey to the buzzing energy of Soho, every neighbourhood is its own village.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "edinburgh": {
        "name": "Edinburgh", "country": "United Kingdom", "iata_code": "EDI",
        "latitude": 55.9533, "longitude": -3.1883,
        "avg_daily_cost_gbp": 110, "budget_level": "medium",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [7, 8, 12],
        "avg_temp_c": {"spring": 9, "summer": 15, "autumn": 9, "winter": 4},
        "tags": ["history", "culture", "festivals", "architecture", "whisky", "hiking", "nightlife"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.7, "popularity_score": 85, "safety_rating": 5,
        "sample_activities": ["Edinburgh Castle", "Arthur's Seat hike", "Royal Mile walking tour", "Scotch whisky tasting", "Edinburgh Fringe Festival"],
        "highlights": "Edinburgh is a city of dramatic contrasts — a medieval Old Town perched on volcanic rock alongside elegant Georgian New Town. August transforms it into the world's largest arts festival, but any month rewards with whisky bars, castle views, and wild hikes minutes from the centre.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "manchester": {
        "name": "Manchester", "country": "United Kingdom", "iata_code": "MAN",
        "latitude": 53.4808, "longitude": -2.2426,
        "avg_daily_cost_gbp": 90, "budget_level": "medium",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 10, "summer": 17, "autumn": 10, "winter": 4},
        "tags": ["nightlife", "music", "football", "food", "culture", "shopping", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 72, "safety_rating": 4,
        "sample_activities": ["Old Trafford stadium tour", "Northern Quarter street art walk", "Science and Industry Museum", "Curry Mile food crawl", "Manchester Art Gallery"],
        "highlights": "Manchester is the beating heart of Northern England — a city that gave the world the Industrial Revolution, legendary football, and iconic music from The Smiths to Oasis. The Northern Quarter buzzes with indie bars and street food, while Ancoats has become one of the UK's best food neighbourhoods.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "bath": {
        "name": "Bath", "country": "United Kingdom", "iata_code": "BRS",
        "latitude": 51.3811, "longitude": -2.3590,
        "avg_daily_cost_gbp": 95, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [5, 6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 5},
        "tags": ["history", "architecture", "wellness", "food", "romance"],
        "suitable_for": ["solo", "couple", "family"],
        "avg_rating": 4.6, "popularity_score": 70, "safety_rating": 5,
        "sample_activities": ["Roman Baths", "Royal Crescent walk", "Thermae Bath Spa", "Sally Lunn's Historic Eating House", "Pulteney Bridge photo"],
        "highlights": "Bath is a UNESCO jewel of honey-coloured Georgian architecture and ancient Roman thermal springs. The rooftop pool at Thermae Bath Spa offers steaming views over the abbey, while the surrounding countryside delivers quintessential English charm.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "york": {
        "name": "York", "country": "United Kingdom", "iata_code": "LBA",
        "latitude": 53.9591, "longitude": -1.0815,
        "avg_daily_cost_gbp": 85, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [5, 6, 7, 12],
        "avg_temp_c": {"spring": 10, "summer": 17, "autumn": 10, "winter": 4},
        "tags": ["history", "food", "architecture", "medieval", "culture"],
        "suitable_for": ["solo", "couple", "family"],
        "avg_rating": 4.6, "popularity_score": 68, "safety_rating": 5,
        "sample_activities": ["York Minster", "The Shambles walking tour", "National Railway Museum", "City walls walk", "Betty's Tea Room"],
        "highlights": "York is England's most perfectly preserved medieval city — cobbled Shambles, massive Gothic Minster, and two thousand years of history inside Roman walls. The food scene punches well above its weight with Michelin-starred restaurants alongside traditional pubs.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "oxford": {
        "name": "Oxford", "country": "United Kingdom", "iata_code": "LHR",
        "latitude": 51.7520, "longitude": -1.2577,
        "avg_daily_cost_gbp": 100, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [5, 6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 5},
        "tags": ["history", "culture", "architecture", "education", "literature"],
        "suitable_for": ["solo", "couple", "family"],
        "avg_rating": 4.5, "popularity_score": 72, "safety_rating": 5,
        "sample_activities": ["Bodleian Library tour", "Christ Church college", "Covered Market", "Punting on the Cherwell", "Ashmolean Museum"],
        "highlights": "Oxford's dreaming spires shelter centuries of academic brilliance and architectural grandeur. Harry Potter fans will recognise Christ Church's Great Hall, while the Covered Market serves the best brownies in England. Punting on the river is a rite of passage.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "cambridge": {
        "name": "Cambridge", "country": "United Kingdom", "iata_code": "STN",
        "latitude": 52.2053, "longitude": 0.1218,
        "avg_daily_cost_gbp": 95, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [5, 6, 7],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 5},
        "tags": ["history", "culture", "architecture", "education", "nature"],
        "suitable_for": ["solo", "couple", "family"],
        "avg_rating": 4.5, "popularity_score": 70, "safety_rating": 5,
        "sample_activities": ["Punting on the Cam", "King's College Chapel", "Fitzwilliam Museum", "The Backs walk", "Eagle pub (DNA discovery)"],
        "highlights": "Cambridge rivals Oxford in beauty but feels more intimate — punt past the famous Backs, explore stunning college chapels, and drink in the pub where Crick and Watson announced they'd found the secret of life. The cycling culture gives it a wonderfully Continental feel.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "brighton": {
        "name": "Brighton", "country": "United Kingdom", "iata_code": "LGW",
        "latitude": 50.8225, "longitude": -0.1372,
        "avg_daily_cost_gbp": 90, "budget_level": "medium",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 12, "winter": 6},
        "tags": ["beach", "nightlife", "food", "lgbtq", "arts", "shopping"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 68, "safety_rating": 4,
        "sample_activities": ["The Lanes vintage shopping", "Royal Pavilion", "Brighton Beach & pier", "North Laine street food", "Komedia comedy night"],
        "highlights": "Brighton is London-by-the-sea with a fiercely independent spirit — the UK's LGBTQ+ capital, a street-food paradise in North Laine, and the gloriously bizarre Royal Pavilion. The pebble beach isn't postcard-pretty but the sunsets are spectacular.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "bristol": {
        "name": "Bristol", "country": "United Kingdom", "iata_code": "BRS",
        "latitude": 51.4545, "longitude": -2.5879,
        "avg_daily_cost_gbp": 85, "budget_level": "medium",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 5},
        "tags": ["street-art", "food", "music", "culture", "history", "nightlife"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.4, "popularity_score": 65, "safety_rating": 4,
        "sample_activities": ["Banksy street art trail", "Clifton Suspension Bridge", "St Nicholas Market", "SS Great Britain", "Harbourside walk"],
        "highlights": "Bristol is Britain's most creative city — Banksy's hometown, where colourful houses tumble down hillsides and the harbourside thrums with independent bars and restaurants. The street food at St Nicholas Market is legendary, and the music scene rivals London's.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "liverpool": {
        "name": "Liverpool", "country": "United Kingdom", "iata_code": "LPL",
        "latitude": 53.4084, "longitude": -2.9916,
        "avg_daily_cost_gbp": 80, "budget_level": "low",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 10, "summer": 17, "autumn": 10, "winter": 5},
        "tags": ["music", "culture", "football", "history", "nightlife", "food", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 70, "safety_rating": 4,
        "sample_activities": ["The Beatles Story", "Tate Liverpool", "Albert Dock", "Anfield stadium tour", "Cavern Quarter pubs"],
        "highlights": "Liverpool wears its heart on its sleeve — from the legendary Cavern Club to the stunning waterfront, it's a city built on music, football, and fierce community pride. The Baltic Triangle is one of England's most exciting creative quarters, with street food, galleries, and rooftop bars.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "glasgow": {
        "name": "Glasgow", "country": "United Kingdom", "iata_code": "GLA",
        "latitude": 55.8642, "longitude": -4.2518,
        "avg_daily_cost_gbp": 85, "budget_level": "medium",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 9, "summer": 15, "autumn": 9, "winter": 4},
        "tags": ["music", "art", "architecture", "nightlife", "food", "culture"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 62, "safety_rating": 4,
        "sample_activities": ["Kelvingrove Art Gallery", "Glasgow Cathedral", "West End pub crawl", "Barras Market", "Riverside Museum"],
        "highlights": "Glasgow is Scotland's creative powerhouse — a city of Art Nouveau architecture, world-class museums (all free), and a music scene that's birthed everyone from Franz Ferdinand to Chvrches. The West End around Ashton Lane is a fairy-lit paradise of pubs and restaurants.",
        "language": "English", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },
    "cardiff": {
        "name": "Cardiff", "country": "United Kingdom", "iata_code": "CWL",
        "latitude": 51.4816, "longitude": -3.1791,
        "avg_daily_cost_gbp": 75, "budget_level": "low",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 17, "autumn": 11, "winter": 5},
        "tags": ["rugby", "castle", "culture", "food", "nightlife", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.2, "popularity_score": 55, "safety_rating": 5,
        "sample_activities": ["Cardiff Castle", "Cardiff Bay waterfront", "Principality Stadium tour", "Bute Park walk", "Roald Dahl Plass"],
        "highlights": "Cardiff punches above its weight as a capital city — a Norman castle in the city centre, a regenerated bay waterfront, and match-day atmosphere that rivals anywhere. It's compact, affordable, and the gateway to spectacular Welsh countryside.",
        "language": "English / Welsh", "currency": "British Pound (GBP)", "time_zone": "UTC+0",
    },

    # ── WESTERN EUROPE ──
    "paris": {
        "name": "Paris", "country": "France", "iata_code": "CDG",
        "latitude": 48.8566, "longitude": 2.3522,
        "avg_daily_cost_gbp": 150, "budget_level": "high",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 13, "summer": 21, "autumn": 13, "winter": 5},
        "tags": ["romance", "culture", "food", "art", "architecture", "shopping", "history", "city"],
        "suitable_for": ["solo", "couple", "family", "friends"],
        "avg_rating": 4.7, "popularity_score": 97, "safety_rating": 4,
        "sample_activities": ["Eiffel Tower", "Louvre Museum", "Montmartre walk", "Seine river cruise", "Le Marais food tour"],
        "highlights": "Paris is not a museum piece but a living, breathing city of 20 arrondissements, each a world unto itself. Skip the tourist traps on Champs-Élysées — the real magic is in the canal-side bars of the 10th, the covered passages of the 2nd, and the Vietnamese food of the 13th.",
        "language": "French", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "amsterdam": {
        "name": "Amsterdam", "country": "Netherlands", "iata_code": "AMS",
        "latitude": 52.3676, "longitude": 4.9041,
        "avg_daily_cost_gbp": 130, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [4, 5, 6, 7],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 4},
        "tags": ["culture", "cycling", "food", "nightlife", "art", "canal", "museums"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 90, "safety_rating": 4,
        "sample_activities": ["Rijksmuseum", "Anne Frank House", "Canal bike tour", "Jordaan neighbourhood walk", "Albert Cuyp Market"],
        "highlights": "Amsterdam is best experienced by bicycle — cycling the canal ring at golden hour with the gabled houses reflected in the water is pure magic. Beyond the tourist centre, Jordaan's hidden courtyards (hofjes), De Pijp's multicultural market, and Amsterdam-Noord's industrial-chic scene reveal the real city.",
        "language": "Dutch", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "brussels": {
        "name": "Brussels", "country": "Belgium", "iata_code": "BRU",
        "latitude": 50.8503, "longitude": 4.3517,
        "avg_daily_cost_gbp": 110, "budget_level": "medium",
        "climate": "oceanic", "best_season": "spring",
        "peak_months": [5, 6, 7, 8],
        "avg_temp_c": {"spring": 11, "summer": 18, "autumn": 11, "winter": 4},
        "tags": ["food", "beer", "chocolate", "art-nouveau", "culture", "history"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.1, "popularity_score": 62, "safety_rating": 4,
        "sample_activities": ["Grand Place", "Belgian beer tasting", "Magritte Museum", "Delirium Café (2000+ beers)", "Chocolate workshop"],
        "highlights": "Brussels is Europe's most underrated food capital — beyond waffles and chocolate lies a city of Michelin stars, Art Nouveau masterpieces, and more beer varieties than anywhere on earth. The Grand Place at night, lit gold, is one of Europe's most beautiful squares.",
        "language": "French / Dutch", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "lisbon": {
        "name": "Lisbon", "country": "Portugal", "iata_code": "LIS",
        "latitude": 38.7223, "longitude": -9.1393,
        "avg_daily_cost_gbp": 80, "budget_level": "low",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 17, "summer": 25, "autumn": 18, "winter": 12},
        "tags": ["food", "culture", "nightlife", "history", "beach", "budget-friendly", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 88, "safety_rating": 5,
        "sample_activities": ["Tram 28 ride", "Alfama neighbourhood walk", "Pastéis de Belém", "Time Out Market", "Sunset from Miradouro da Graça"],
        "highlights": "Lisbon cascades down seven hills to the Tagus river in a tumble of pastel-coloured tiles, iron balconies, and hidden miradouros. The city has reinvented itself as Europe's coolest capital — LX Factory for creative culture, Mouraria for authentic fado, and Cais do Sodré for all-night dancing.",
        "language": "Portuguese", "currency": "Euro (EUR)", "time_zone": "UTC+0",
    },
    "madrid": {
        "name": "Madrid", "country": "Spain", "iata_code": "MAD",
        "latitude": 40.4168, "longitude": -3.7038,
        "avg_daily_cost_gbp": 95, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 16, "summer": 28, "autumn": 16, "winter": 7},
        "tags": ["food", "culture", "art", "nightlife", "history", "shopping", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.5, "popularity_score": 85, "safety_rating": 4,
        "sample_activities": ["Prado Museum", "Tapas crawl in La Latina", "Retiro Park boat ride", "Mercado de San Miguel", "Sunset at Temple of Debod"],
        "highlights": "Madrid lives late — dinner at 10pm, bars at midnight, churros con chocolate at 4am. The Prado houses masterpieces that rival the Louvre with a fraction of the crowds. La Latina's Sunday tapas crawl is sacred, and the vermouth scene in Malasaña is having a moment.",
        "language": "Spanish", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "barcelona": {
        "name": "Barcelona", "country": "Spain", "iata_code": "BCN",
        "latitude": 41.3874, "longitude": 2.1686,
        "avg_daily_cost_gbp": 110, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 16, "summer": 26, "autumn": 17, "winter": 10},
        "tags": ["beach", "architecture", "food", "nightlife", "culture", "art", "city"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.6, "popularity_score": 92, "safety_rating": 3,
        "sample_activities": ["Sagrada Família", "Park Güell", "La Boqueria market", "Gothic Quarter walk", "Barceloneta beach"],
        "highlights": "Barcelona is Gaudí's dreamscape made real — from the still-unfinished Sagrada Família to the psychedelic Park Güell. But beyond the architecture, it's the vermouth bars of Poble-sec, the seafood at La Barceloneta, and the electric energy of El Born that make you want to move here.",
        "language": "Catalan / Spanish", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "seville": {
        "name": "Seville", "country": "Spain", "iata_code": "SVQ",
        "latitude": 37.3891, "longitude": -5.9845,
        "avg_daily_cost_gbp": 75, "budget_level": "low",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [3, 4, 5, 10],
        "avg_temp_c": {"spring": 20, "summer": 33, "autumn": 20, "winter": 11},
        "tags": ["flamenco", "culture", "food", "history", "architecture", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 75, "safety_rating": 4,
        "sample_activities": ["Alcázar of Seville", "Flamenco show in Triana", "Seville Cathedral & Giralda", "Tapas in Santa Cruz", "Metropol Parasol sunset"],
        "highlights": "Seville is intoxicating — flamenco spilling from doorways in Triana, orange trees lining every street, and tapas so good (and often free with a drink) you'll never eat dinner. Spring's Feria de Abril is one of Europe's greatest parties. Avoid July-August when it hits 45°C.",
        "language": "Spanish", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "porto": {
        "name": "Porto", "country": "Portugal", "iata_code": "OPO",
        "latitude": 41.1579, "longitude": -8.6291,
        "avg_daily_cost_gbp": 70, "budget_level": "low",
        "climate": "mediterranean", "best_season": "summer",
        "peak_months": [6, 7, 8, 9],
        "avg_temp_c": {"spring": 14, "summer": 21, "autumn": 15, "winter": 10},
        "tags": ["food", "wine", "culture", "history", "architecture", "budget-friendly", "romance"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 78, "safety_rating": 5,
        "sample_activities": ["Port wine tasting in Vila Nova de Gaia", "Livraria Lello bookshop", "Ribeira waterfront walk", "Francesinha sandwich", "São Bento station tiles"],
        "highlights": "Porto is Lisbon's grittier, more authentic sibling — crumbling azulejo-tiled facades hiding world-class restaurants, port wine cellars across the river in Gaia, and a francesinha (meat-stuffed sandwich drowned in cheese sauce) that's worth the trip alone.",
        "language": "Portuguese", "currency": "Euro (EUR)", "time_zone": "UTC+0",
    },
    "valencia": {
        "name": "Valencia", "country": "Spain", "iata_code": "VLC",
        "latitude": 39.4699, "longitude": -0.3763,
        "avg_daily_cost_gbp": 80, "budget_level": "low",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 17, "summer": 27, "autumn": 18, "winter": 11},
        "tags": ["beach", "food", "architecture", "culture", "budget-friendly", "city"],
        "suitable_for": ["solo", "couple", "family", "friends"],
        "avg_rating": 4.4, "popularity_score": 72, "safety_rating": 4,
        "sample_activities": ["City of Arts and Sciences", "Authentic paella in El Palmar", "Central Market", "Turia Gardens cycling", "Malvarrosa Beach"],
        "highlights": "Valencia is the birthplace of paella and fiercely proud of it — eat the real thing at El Palmar, not the tourist traps. The futuristic City of Arts and Sciences contrasts beautifully with the Gothic old town, and the converted riverbed Turia Gardens are perfect for cycling.",
        "language": "Spanish / Valencian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "rome": {
        "name": "Rome", "country": "Italy", "iata_code": "FCO",
        "latitude": 41.9028, "longitude": 12.4964,
        "avg_daily_cost_gbp": 120, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 16, "summer": 27, "autumn": 17, "winter": 9},
        "tags": ["history", "food", "culture", "art", "architecture", "romance", "city"],
        "suitable_for": ["solo", "couple", "family", "friends"],
        "avg_rating": 4.7, "popularity_score": 95, "safety_rating": 4,
        "sample_activities": ["Colosseum", "Vatican Museums & Sistine Chapel", "Trastevere food walk", "Trevi Fountain", "Pantheon"],
        "highlights": "Rome layers three thousand years of history into every street — one moment you're eating the best cacio e pepe of your life in a Trastevere trattoria, the next you're standing in the Pantheon watching rain fall through the oculus. Skip the overpriced restaurants near the sights and eat where locals do in Testaccio.",
        "language": "Italian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "florence": {
        "name": "Florence", "country": "Italy", "iata_code": "FLR",
        "latitude": 43.7696, "longitude": 11.2558,
        "avg_daily_cost_gbp": 115, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 15, "summer": 27, "autumn": 16, "winter": 7},
        "tags": ["art", "food", "history", "architecture", "wine", "romance", "culture"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.7, "popularity_score": 88, "safety_rating": 5,
        "sample_activities": ["Uffizi Gallery", "Florence Cathedral & Brunelleschi's Dome", "Ponte Vecchio", "Tuscan wine tasting", "Piazzale Michelangelo sunset"],
        "highlights": "Florence is the cradle of the Renaissance compressed into a walkable city — Botticelli's Birth of Venus at the Uffizi, Michelangelo's David at the Accademia, and the best bistecca alla fiorentina you'll ever eat at a Trattoria in San Frediano, the local neighbourhood across the Arno.",
        "language": "Italian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "venice": {
        "name": "Venice", "country": "Italy", "iata_code": "VCE",
        "latitude": 45.4408, "longitude": 12.3155,
        "avg_daily_cost_gbp": 130, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 14, "summer": 24, "autumn": 14, "winter": 4},
        "tags": ["romance", "architecture", "culture", "art", "history", "unique"],
        "suitable_for": ["couple", "solo", "friends"],
        "avg_rating": 4.6, "popularity_score": 90, "safety_rating": 5,
        "sample_activities": ["St Mark's Basilica", "Rialto Market morning visit", "Burano island trip", "Cicchetti bar crawl in Cannaregio", "Gondola ride at sunset"],
        "highlights": "Venice is a city that shouldn't exist — 118 islands connected by 400 bridges, slowly sinking into the lagoon. Get lost in the labyrinth of Dorsoduro, eat cicchetti (Venetian tapas) standing at a bacaro in Cannaregio, and take the vaporetto to rainbow-coloured Burano at sunset.",
        "language": "Italian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "milan": {
        "name": "Milan", "country": "Italy", "iata_code": "MXP",
        "latitude": 45.4642, "longitude": 9.1900,
        "avg_daily_cost_gbp": 135, "budget_level": "high",
        "climate": "continental", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 15, "summer": 26, "autumn": 14, "winter": 4},
        "tags": ["fashion", "food", "design", "art", "shopping", "culture", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 78, "safety_rating": 4,
        "sample_activities": ["Last Supper viewing", "Duomo rooftop", "Navigli canal aperitivo", "Quadrilatero della Moda shopping", "Brera district walk"],
        "highlights": "Milan is Italy's most misunderstood city — visitors expecting Renaissance romance find cutting-edge design, world-class aperitivo culture along the Navigli canals, and the best risotto alla milanese in hidden trattorias. Book The Last Supper weeks ahead — it's worth every bit of planning.",
        "language": "Italian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "naples": {
        "name": "Naples", "country": "Italy", "iata_code": "NAP",
        "latitude": 40.8518, "longitude": 14.2681,
        "avg_daily_cost_gbp": 75, "budget_level": "low",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 16, "summer": 27, "autumn": 17, "winter": 9},
        "tags": ["food", "history", "culture", "budget-friendly", "authentic", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 70, "safety_rating": 3,
        "sample_activities": ["Pizza at L'Antica Pizzeria Da Michele", "Naples Underground tour", "Pompeii day trip", "Spaccanapoli walk", "Amalfi Coast excursion"],
        "highlights": "Naples is Italy at its most raw and real — chaotic, loud, crumbling, and absolutely magnificent. This is where pizza was invented, and a margherita from Da Michele or Sorbillo will ruin you for pizza everywhere else. The energy of Spaccanapoli is unlike anywhere in Europe.",
        "language": "Italian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "athens": {
        "name": "Athens", "country": "Greece", "iata_code": "ATH",
        "latitude": 37.9838, "longitude": 23.7275,
        "avg_daily_cost_gbp": 85, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 18, "summer": 30, "autumn": 20, "winter": 10},
        "tags": ["history", "food", "culture", "nightlife", "ancient", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.4, "popularity_score": 82, "safety_rating": 4,
        "sample_activities": ["Acropolis & Parthenon", "Plaka neighbourhood walk", "Monastiraki Flea Market", "Taverna dinner in Psyrri", "Sunset from Lycabettus Hill"],
        "highlights": "Athens has reinvented itself from gritty to glorious — street art-covered Exarchia, rooftop bars with Acropolis views, and a food scene where €3 souvlaki sits alongside Michelin-starred restaurants. The anarchist neighbourhood of Exarchia has some of the best cheap eats in Europe.",
        "language": "Greek", "currency": "Euro (EUR)", "time_zone": "UTC+2",
    },
    "santorini": {
        "name": "Santorini", "country": "Greece", "iata_code": "JTR",
        "latitude": 36.3932, "longitude": 25.4615,
        "avg_daily_cost_gbp": 160, "budget_level": "high",
        "climate": "mediterranean", "best_season": "summer",
        "peak_months": [5, 6, 7, 8, 9],
        "avg_temp_c": {"spring": 17, "summer": 27, "autumn": 20, "winter": 12},
        "tags": ["romance", "beach", "luxury", "photography", "wine", "sunset"],
        "suitable_for": ["couple", "solo", "friends"],
        "avg_rating": 4.8, "popularity_score": 92, "safety_rating": 5,
        "sample_activities": ["Oia sunset", "Caldera boat tour", "Red Beach", "Wine tasting at Santo Wines", "Fira to Oia hike"],
        "highlights": "Santorini's white-and-blue drama needs no introduction — but skip the overcrowded Oia sunset for Imerovigli's equally stunning views with a fraction of the crowds. The volcanic wine (Assyrtiko) is world-class, and the black sand beaches are unlike anything else in Europe.",
        "language": "Greek", "currency": "Euro (EUR)", "time_zone": "UTC+2",
    },
    "mykonos": {
        "name": "Mykonos", "country": "Greece", "iata_code": "JMK",
        "latitude": 37.4467, "longitude": 25.3289,
        "avg_daily_cost_gbp": 180, "budget_level": "high",
        "climate": "mediterranean", "best_season": "summer",
        "peak_months": [6, 7, 8, 9],
        "avg_temp_c": {"spring": 17, "summer": 26, "autumn": 19, "winter": 12},
        "tags": ["nightlife", "beach", "luxury", "party", "lgbtq"],
        "suitable_for": ["couple", "friends"],
        "avg_rating": 4.5, "popularity_score": 85, "safety_rating": 5,
        "sample_activities": ["Little Venice sunset", "Paradise Beach club", "Windmills of Mykonos", "Delos island day trip", "Mykonos Town bar crawl"],
        "highlights": "Mykonos is Europe's ultimate party island — superstar DJs, beach clubs with €20 cocktails, and a labyrinthine old town that's pure Cycladic charm. For a quieter side, take the boat to uninhabited Delos, one of Greece's most important archaeological sites.",
        "language": "Greek", "currency": "Euro (EUR)", "time_zone": "UTC+2",
    },

    # ── CENTRAL EUROPE ──
    "berlin": {
        "name": "Berlin", "country": "Germany", "iata_code": "BER",
        "latitude": 52.5200, "longitude": 13.4050,
        "avg_daily_cost_gbp": 100, "budget_level": "medium",
        "climate": "continental", "best_season": "summer",
        "peak_months": [5, 6, 7, 8, 9],
        "avg_temp_c": {"spring": 11, "summer": 20, "autumn": 10, "winter": 2},
        "tags": ["nightlife", "culture", "history", "art", "food", "budget-friendly", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.5, "popularity_score": 88, "safety_rating": 4,
        "sample_activities": ["Brandenburg Gate", "East Side Gallery", "Berghain (if you can get in)", "Museum Island", "Street food at Markthalle Neun"],
        "highlights": "Berlin is Europe's most creatively free city — a place where Cold War history meets world-famous techno, and abandoned buildings become galleries. Kreuzberg and Neukölln are the beating heart: döner kebabs at 3am, vinyl shops, and a sense that anything goes.",
        "language": "German", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "munich": {
        "name": "Munich", "country": "Germany", "iata_code": "MUC",
        "latitude": 48.1351, "longitude": 11.5820,
        "avg_daily_cost_gbp": 120, "budget_level": "medium",
        "climate": "continental", "best_season": "summer",
        "peak_months": [6, 7, 8, 9, 10],
        "avg_temp_c": {"spring": 11, "summer": 20, "autumn": 10, "winter": 1},
        "tags": ["beer", "culture", "history", "food", "nature", "christmas-market"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.5, "popularity_score": 80, "safety_rating": 5,
        "sample_activities": ["Marienplatz & Glockenspiel", "English Garden surfing", "Hofbräuhaus beer hall", "Nymphenburg Palace", "Day trip to Neuschwanstein Castle"],
        "highlights": "Munich blends Bavarian tradition with cosmopolitan polish — surfers ride the standing wave in the English Garden, beer gardens serve litre steins under chestnut trees, and Oktoberfest is the world's greatest party. The Alps are an hour away for hiking or skiing.",
        "language": "German", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "vienna": {
        "name": "Vienna", "country": "Austria", "iata_code": "VIE",
        "latitude": 48.2082, "longitude": 16.3738,
        "avg_daily_cost_gbp": 115, "budget_level": "medium",
        "climate": "continental", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 12],
        "avg_temp_c": {"spring": 12, "summer": 22, "autumn": 11, "winter": 2},
        "tags": ["culture", "music", "architecture", "food", "coffee", "history", "art"],
        "suitable_for": ["solo", "couple", "family", "friends"],
        "avg_rating": 4.7, "popularity_score": 82, "safety_rating": 5,
        "sample_activities": ["Schönbrunn Palace", "Naschmarkt food tour", "Vienna State Opera", "Coffee house culture at Café Central", "Belvedere Gallery (Klimt's The Kiss)"],
        "highlights": "Vienna is the world's most liveable city and it shows — imperial palaces, the coffee house tradition (UNESCO-listed), and a music heritage from Mozart to Falco. The Naschmarkt is a feast for the senses, and the wine taverns (Heurige) in the vineyard hills are a perfect evening.",
        "language": "German", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "prague": {
        "name": "Prague", "country": "Czech Republic", "iata_code": "PRG",
        "latitude": 50.0755, "longitude": 14.4378,
        "avg_daily_cost_gbp": 70, "budget_level": "low",
        "climate": "continental", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 11, "summer": 20, "autumn": 10, "winter": 1},
        "tags": ["history", "beer", "architecture", "culture", "nightlife", "budget-friendly", "romance"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 85, "safety_rating": 5,
        "sample_activities": ["Charles Bridge at sunrise", "Prague Castle complex", "Old Town Square", "Beer spa experience", "Craft beer in Žižkov"],
        "highlights": "Prague is a Gothic fairy tale that becomes a party town after dark — Charles Bridge at sunrise is genuinely magical, before the crowds arrive. Czech beer is the best and cheapest in Europe (£1.50 a pint in Žižkov), and the new-wave coffee and bar scene in Karlín rivals Berlin's.",
        "language": "Czech", "currency": "Czech Koruna (CZK)", "time_zone": "UTC+1",
    },
    "budapest": {
        "name": "Budapest", "country": "Hungary", "iata_code": "BUD",
        "latitude": 47.4979, "longitude": 19.0402,
        "avg_daily_cost_gbp": 65, "budget_level": "low",
        "climate": "continental", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 13, "summer": 23, "autumn": 12, "winter": 1},
        "tags": ["thermal-baths", "nightlife", "architecture", "food", "budget-friendly", "culture"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 84, "safety_rating": 4,
        "sample_activities": ["Széchenyi Thermal Bath", "Ruin bars in Jewish Quarter", "Hungarian Parliament", "Gellért Hill sunset", "Langos at Central Market Hall"],
        "highlights": "Budapest is two cities divided by the Danube — hilly Buda with its castle and thermal baths, flat Pest with its ruin bars and Art Nouveau boulevards. The ruin bar scene (Szimpla Kert) is legendary, Széchenyi Baths are Europe's grandest, and it's still absurdly cheap.",
        "language": "Hungarian", "currency": "Hungarian Forint (HUF)", "time_zone": "UTC+1",
    },
    "warsaw": {
        "name": "Warsaw", "country": "Poland", "iata_code": "WAW",
        "latitude": 52.2297, "longitude": 21.0122,
        "avg_daily_cost_gbp": 65, "budget_level": "low",
        "climate": "continental", "best_season": "summer",
        "peak_months": [5, 6, 7, 8, 9],
        "avg_temp_c": {"spring": 11, "summer": 20, "autumn": 9, "winter": 0},
        "tags": ["history", "food", "culture", "nightlife", "budget-friendly", "city"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.2, "popularity_score": 60, "safety_rating": 4,
        "sample_activities": ["Old Town (rebuilt from WWII rubble)", "Warsaw Rising Museum", "Praga district street art", "Milk bar lunch", "Nowy Świat walk"],
        "highlights": "Warsaw rose from total WWII destruction to become one of Europe's most dynamic capitals. The meticulously rebuilt Old Town is UNESCO-listed, while the Praga district across the Vistula is the edgy, artistic counterpoint. Eat at a traditional 'milk bar' (bar mleczny) for a filling meal under £3.",
        "language": "Polish", "currency": "Polish Złoty (PLN)", "time_zone": "UTC+1",
    },
    "krakow": {
        "name": "Krakow", "country": "Poland", "iata_code": "KRK",
        "latitude": 50.0647, "longitude": 19.9450,
        "avg_daily_cost_gbp": 60, "budget_level": "low",
        "climate": "continental", "best_season": "spring",
        "peak_months": [4, 5, 6, 9],
        "avg_temp_c": {"spring": 11, "summer": 20, "autumn": 10, "winter": 0},
        "tags": ["history", "food", "culture", "nightlife", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 78, "safety_rating": 5,
        "sample_activities": ["Wawel Castle", "Main Market Square", "Kazimierz Jewish Quarter", "Auschwitz-Birkenau visit", "Wieliczka Salt Mine"],
        "highlights": "Krakow survived WWII intact, leaving one of Europe's most beautiful medieval centres untouched. The Jewish Quarter of Kazimierz is now the city's coolest neighbourhood — hole-in-the-wall bars, live jazz, and pierogi that cost pennies. A pint of excellent Polish craft beer is about £2.",
        "language": "Polish", "currency": "Polish Złoty (PLN)", "time_zone": "UTC+1",
    },

    # ── NORTHERN EUROPE ──
    "copenhagen": {
        "name": "Copenhagen", "country": "Denmark", "iata_code": "CPH",
        "latitude": 55.6761, "longitude": 12.5683,
        "avg_daily_cost_gbp": 160, "budget_level": "high",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 9, "summer": 18, "autumn": 9, "winter": 2},
        "tags": ["design", "food", "cycling", "hygge", "culture", "architecture"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.6, "popularity_score": 78, "safety_rating": 5,
        "sample_activities": ["Nyhavn harbour walk", "Tivoli Gardens", "Torvehallerne food market", "Christiania free town", "Cycling the lakes"],
        "highlights": "Copenhagen invented hygge and it pervades everything — from candlelit wine bars in Vesterbro to the world's best restaurant Noma. The city is built for cycling, Christiania is a genuine 1970s commune, and the harbour baths let you swim in the middle of the city. Expensive but extraordinary.",
        "language": "Danish", "currency": "Danish Krone (DKK)", "time_zone": "UTC+1",
    },
    "stockholm": {
        "name": "Stockholm", "country": "Sweden", "iata_code": "ARN",
        "latitude": 59.3293, "longitude": 18.0686,
        "avg_daily_cost_gbp": 150, "budget_level": "high",
        "climate": "continental", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 8, "summer": 18, "autumn": 8, "winter": -1},
        "tags": ["design", "archipelago", "culture", "food", "nature", "history"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.5, "popularity_score": 72, "safety_rating": 5,
        "sample_activities": ["Gamla Stan (Old Town) walk", "Vasa Museum", "Archipelago ferry trip", "Fotografiska museum", "SoFo (Södermalm) vintage shopping"],
        "highlights": "Stockholm is spread across 14 islands connected by bridges and ferries — Gamla Stan's medieval lanes, Södermalm's hipster coffee shops, and a 30,000-island archipelago reachable by public ferry. The light in midsummer is extraordinary — 18+ hours of daylight and everyone is outdoors.",
        "language": "Swedish", "currency": "Swedish Krona (SEK)", "time_zone": "UTC+1",
    },
    "oslo": {
        "name": "Oslo", "country": "Norway", "iata_code": "OSL",
        "latitude": 59.9139, "longitude": 10.7522,
        "avg_daily_cost_gbp": 180, "budget_level": "high",
        "climate": "continental", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 7, "summer": 17, "autumn": 7, "winter": -2},
        "tags": ["nature", "fjords", "museums", "design", "hiking", "skiing"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.3, "popularity_score": 60, "safety_rating": 5,
        "sample_activities": ["Vigeland Sculpture Park", "Oslo Opera House rooftop", "Munch Museum", "Fjord cruise", "Nordmarka forest hike"],
        "highlights": "Oslo is where Nordic city life meets raw nature — forest and fjord minutes from the centre. The Opera House's walkable marble roof overlooking the harbour is iconic, and the new Munch Museum houses The Scream. Expensive, but the free outdoor access — hiking, swimming, skiing — offsets it.",
        "language": "Norwegian", "currency": "Norwegian Krone (NOK)", "time_zone": "UTC+1",
    },
    "reykjavik": {
        "name": "Reykjavik", "country": "Iceland", "iata_code": "KEF",
        "latitude": 64.1466, "longitude": -21.9426,
        "avg_daily_cost_gbp": 200, "budget_level": "high",
        "climate": "subarctic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 4, "summer": 11, "autumn": 4, "winter": 0},
        "tags": ["nature", "adventure", "northern-lights", "geothermal", "unique", "hiking"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.7, "popularity_score": 75, "safety_rating": 5,
        "sample_activities": ["Golden Circle tour", "Blue Lagoon", "Northern Lights (Sept-March)", "Whale watching", "Hallgrímskirkja church"],
        "highlights": "Reykjavik is the gateway to landscapes that look like another planet — geysers, glaciers, volcanoes, and midnight sun. The city itself is tiny but mighty: colourful tin-clad houses, a thriving music scene, and hot pot culture where Icelanders socialise in geothermal pools year-round.",
        "language": "Icelandic", "currency": "Icelandic Króna (ISK)", "time_zone": "UTC+0",
    },
    "helsinki": {
        "name": "Helsinki", "country": "Finland", "iata_code": "HEL",
        "latitude": 60.1699, "longitude": 24.9384,
        "avg_daily_cost_gbp": 140, "budget_level": "high",
        "climate": "continental", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 6, "summer": 17, "autumn": 6, "winter": -3},
        "tags": ["design", "sauna", "nature", "architecture", "food", "culture"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.3, "popularity_score": 58, "safety_rating": 5,
        "sample_activities": ["Suomenlinna sea fortress", "Public sauna experience", "Design District walk", "Helsinki Cathedral", "Market Square herring"],
        "highlights": "Helsinki is Scandinavia's quiet achiever — a design-obsessed capital where public saunas are a way of life, islands dot the harbour, and Art Nouveau buildings line the streets. The sauna culture is non-negotiable — try Löyly or Allas Sea Pool for a sauna-to-sea-dip combo.",
        "language": "Finnish / Swedish", "currency": "Euro (EUR)", "time_zone": "UTC+2",
    },
    "dublin": {
        "name": "Dublin", "country": "Ireland", "iata_code": "DUB",
        "latitude": 53.3498, "longitude": -6.2603,
        "avg_daily_cost_gbp": 140, "budget_level": "high",
        "climate": "oceanic", "best_season": "summer",
        "peak_months": [6, 7, 8],
        "avg_temp_c": {"spring": 10, "summer": 16, "autumn": 10, "winter": 5},
        "tags": ["pubs", "literature", "music", "culture", "history", "food", "nightlife"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.4, "popularity_score": 80, "safety_rating": 4,
        "sample_activities": ["Temple Bar pub crawl", "Trinity College & Book of Kells", "Guinness Storehouse", "Howth cliff walk", "Literary pub crawl"],
        "highlights": "Dublin is a city that runs on conversation, Guinness, and live music spilling from every pub door. Beyond Temple Bar's tourist prices, the creative neighbourhoods of Stoneybatter and Phibsborough serve pints for half the price. The Howth cliff walk, 30 minutes by train, is spectacular.",
        "language": "English / Irish", "currency": "Euro (EUR)", "time_zone": "UTC+0",
    },

    # ── MEDITERRANEAN ──
    "dubrovnik": {
        "name": "Dubrovnik", "country": "Croatia", "iata_code": "DBV",
        "latitude": 42.6507, "longitude": 18.0944,
        "avg_daily_cost_gbp": 120, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [5, 6, 9, 10],
        "avg_temp_c": {"spring": 16, "summer": 27, "autumn": 18, "winter": 9},
        "tags": ["history", "beach", "architecture", "game-of-thrones", "culture"],
        "suitable_for": ["couple", "solo", "friends"],
        "avg_rating": 4.6, "popularity_score": 80, "safety_rating": 5,
        "sample_activities": ["City walls walk", "Kayaking around the old town", "Lokrum Island trip", "Cable car to Mount Srđ", "Buža Bar cliff-edge drinks"],
        "highlights": "Dubrovnik's walled old town is a real-life film set — Game of Thrones made it famous, but the marble streets, terracotta roofs, and Adriatic views need no fictional enhancement. Visit in shoulder season (May or September) to avoid cruise-ship crowds that make summer unbearable.",
        "language": "Croatian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "split": {
        "name": "Split", "country": "Croatia", "iata_code": "SPU",
        "latitude": 43.5081, "longitude": 16.4402,
        "avg_daily_cost_gbp": 90, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "summer",
        "peak_months": [6, 7, 8, 9],
        "avg_temp_c": {"spring": 15, "summer": 27, "autumn": 17, "winter": 8},
        "tags": ["beach", "history", "food", "nightlife", "island-hopping"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.5, "popularity_score": 72, "safety_rating": 5,
        "sample_activities": ["Diocletian's Palace", "Marjan Hill hike", "Hvar island day trip", "Green Market", "Riva promenade sunset"],
        "highlights": "Split is built inside a Roman emperor's palace — literally, people live in 1,700-year-old walls. It's the gateway to Croatia's islands (Hvar, Brač, Vis), the Riva promenade buzzes with life, and Marjan Hill offers pine-scented hiking minutes from the centre. More authentic and affordable than Dubrovnik.",
        "language": "Croatian", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "valletta": {
        "name": "Valletta", "country": "Malta", "iata_code": "MLA",
        "latitude": 35.8989, "longitude": 14.5146,
        "avg_daily_cost_gbp": 85, "budget_level": "medium",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 17, "summer": 28, "autumn": 21, "winter": 13},
        "tags": ["history", "architecture", "beach", "food", "culture", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends", "family"],
        "avg_rating": 4.4, "popularity_score": 58, "safety_rating": 5,
        "sample_activities": ["St John's Co-Cathedral", "Upper Barrakka Gardens", "Valletta waterfront", "Three Cities boat trip", "Pastizzi at Crystal Palace"],
        "highlights": "Valletta is Europe's smallest capital but packs in more history per square metre than almost anywhere — Knights of Malta fortifications, baroque churches, and a food scene that blends Italian, North African, and British influences. A pastizz (ricotta pastry) costs 30 cents and is the perfect snack.",
        "language": "Maltese / English", "currency": "Euro (EUR)", "time_zone": "UTC+1",
    },
    "nicosia": {
        "name": "Nicosia", "country": "Cyprus", "iata_code": "LCA",
        "latitude": 35.1856, "longitude": 33.3823,
        "avg_daily_cost_gbp": 80, "budget_level": "low",
        "climate": "mediterranean", "best_season": "spring",
        "peak_months": [4, 5, 6, 9, 10],
        "avg_temp_c": {"spring": 20, "summer": 33, "autumn": 22, "winter": 12},
        "tags": ["history", "culture", "food", "unique", "budget-friendly"],
        "suitable_for": ["solo", "couple", "friends"],
        "avg_rating": 4.0, "popularity_score": 40, "safety_rating": 4,
        "sample_activities": ["Cross the Green Line border", "Büyük Han caravanserai", "Ledra Street walk", "Shacolas Tower viewpoint", "Meze dinner"],
        "highlights": "Nicosia is Europe's last divided capital — cross the UN buffer zone from the Greek south to the Turkish north and experience two cultures in one city. The walled old town hides Ottoman hans (inns), Byzantine churches, and some of the best meze in the Mediterranean.",
        "language": "Greek / Turkish", "currency": "Euro (EUR)", "time_zone": "UTC+2",
    },
}

# ── Visa requirements for all European destinations ──
# GB passport holders have visa-free access to all European countries
VISA_TEMPLATE = {
    "GB": {"requirement": "visa-free", "duration_days": 90, "cost_gbp": 0},
    "US": {"requirement": "visa-free", "duration_days": 90, "cost_gbp": 0},
    "EU": {"requirement": "visa-free", "duration_days": 0, "cost_gbp": 0},
    "IN": {"requirement": "visa-required", "duration_days": 90, "cost_gbp": 80},
    "CN": {"requirement": "visa-required", "duration_days": 90, "cost_gbp": 80},
    "AU": {"requirement": "visa-free", "duration_days": 90, "cost_gbp": 0},
    "NG": {"requirement": "visa-required", "duration_days": 90, "cost_gbp": 80},
}

# UK destinations have different visa rules
VISA_UK = {
    "GB": {"requirement": "visa-free", "duration_days": 0, "cost_gbp": 0},
    "US": {"requirement": "visa-free", "duration_days": 180, "cost_gbp": 0},
    "EU": {"requirement": "visa-free", "duration_days": 180, "cost_gbp": 0},
    "IN": {"requirement": "visa-required", "duration_days": 180, "cost_gbp": 100},
    "CN": {"requirement": "visa-required", "duration_days": 180, "cost_gbp": 100},
    "AU": {"requirement": "visa-free", "duration_days": 180, "cost_gbp": 0},
    "NG": {"requirement": "visa-required", "duration_days": 180, "cost_gbp": 100},
}


def fetch_weather_data(lat, lon):
    """Fetch monthly average temperatures from Open-Meteo for peak month validation."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto&forecast_days=7"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            if temps_max and temps_min:
                avg_max = round(sum(temps_max) / len(temps_max), 1)
                avg_min = round(sum(temps_min) / len(temps_min), 1)
                return {"current_avg_high": avg_max, "current_avg_low": avg_min}
    except Exception as e:
        print(f"  [weather] API error: {e}")
    return None


def fetch_country_info(country_name):
    """Fetch country info from RestCountries API."""
    try:
        url = f"https://restcountries.com/v3.1/name/{country_name}?fields=languages,currencies,region,subregion,flags"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"  [country] API error for {country_name}: {e}")
    return None


def build_destinations():
    """Build the complete destinations list with API-enriched data."""
    destinations = []
    country_cache = {}

    total = len(CITIES)
    for idx, (city_id, city) in enumerate(CITIES.items(), 1):
        print(f"[{idx}/{total}] Processing {city['name']}, {city['country']}...")

        # ── Fetch weather data ──
        weather = fetch_weather_data(city["latitude"], city["longitude"])
        if weather:
            print(f"  [OK] Weather: {weather['current_avg_high']}°C high, {weather['current_avg_low']}°C low")

        # ── Fetch country info (cached) ──
        country = city["country"]
        if country == "United Kingdom":
            country_lookup = "United Kingdom"
        else:
            country_lookup = country

        if country_lookup not in country_cache:
            info = fetch_country_info(country_lookup)
            if info:
                country_cache[country_lookup] = info
                print(f"  [OK] Country info fetched for {country_lookup}")
            else:
                print(f"  [FAIL] Country info not found for {country_lookup}")
            time.sleep(0.3)  # Rate limiting

        # ── Build destination entry ──
        visa = VISA_UK if country == "United Kingdom" else VISA_TEMPLATE

        dest = {
            "id": city_id,
            "name": city["name"],
            "country": city["country"],
            "continent": "Europe",
            "iata_code": city["iata_code"],
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "avg_daily_cost_gbp": city["avg_daily_cost_gbp"],
            "budget_level": city["budget_level"],
            "best_season": city["best_season"],
            "peak_months": city["peak_months"],
            "climate": city["climate"],
            "avg_temp_c": city["avg_temp_c"],
            "tags": city["tags"],
            "suitable_for": city["suitable_for"],
            "avg_rating": city["avg_rating"],
            "popularity_score": city["popularity_score"],
            "safety_rating": city["safety_rating"],
            "sample_activities": city["sample_activities"],
            "highlights": city["highlights"],
            "language": city["language"],
            "currency": city["currency"],
            "time_zone": city["time_zone"],
            "visa_requirements": visa,
        }

        destinations.append(dest)
        time.sleep(0.2)  # Be nice to APIs

    return destinations


def main():
    print("=" * 60)
    print("TravelBuddy — European Destinations Database Builder")
    print("=" * 60)
    print()

    # ── Backup existing file ──
    if os.path.exists(DEST_PATH):
        print(f"Backing up existing destinations.json -> destinations_backup.json")
        shutil.copy2(DEST_PATH, BACKUP_PATH)
        print(f"  [OK] Backup saved to {BACKUP_PATH}")
    print()

    # ── Build destinations ──
    print(f"Building database for {len(CITIES)} European cities...")
    print("-" * 60)
    destinations = build_destinations()
    print("-" * 60)
    print()

    # ── Save to file ──
    with open(DEST_PATH, "w", encoding="utf-8") as f:
        json.dump(destinations, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved {len(destinations)} destinations to {DEST_PATH}")
    print(f"  File size: {os.path.getsize(DEST_PATH) / 1024:.1f} KB")
    print()

    # ── Summary ──
    countries = set(d["country"] for d in destinations)
    budget_counts = {}
    for d in destinations:
        budget_counts[d["budget_level"]] = budget_counts.get(d["budget_level"], 0) + 1

    print("Summary:")
    print(f"  Total destinations: {len(destinations)}")
    print(f"  Countries covered: {len(countries)}")
    print(f"  Budget breakdown: {budget_counts}")
    print(f"  Cost range: £{min(d['avg_daily_cost_gbp'] for d in destinations)} - £{max(d['avg_daily_cost_gbp'] for d in destinations)}/day")
    print()
    print("Done! [OK]")


if __name__ == "__main__":
    main()
