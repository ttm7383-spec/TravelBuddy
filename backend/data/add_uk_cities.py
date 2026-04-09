"""Add UK city data to city_data.json. Run once."""
import json, os

path = os.path.join(os.path.dirname(__file__), "city_data.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

uk_cities = {
    "Edinburgh": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "4h 20m", "operator": "LNER", "price_gbp": 40},
        "hotels": [
            {"name": "Castle Rock Hostel", "price_per_night_gbp": 18, "rating": 4.4, "stars": 2, "amenities": ["Free WiFi", "Castle views"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "Motel One Edinburgh-Royal", "price_per_night_gbp": 75, "rating": 4.3, "stars": 3, "amenities": ["Free WiFi", "Bar", "City centre"], "room_type": "Standard Double", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "The Balmoral Hotel", "price_per_night_gbp": 280, "rating": 4.8, "stars": 5, "amenities": ["Spa", "Michelin restaurant", "Pool"], "room_type": "Deluxe Double", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "flights_from_london": [
            {"airline": "easyJet", "airline_code": "U2", "price_gbp": 30, "departure_time": "07:15", "arrival_time": "08:45", "duration": "1h 30m", "stops": 0, "stops_label": "Direct"},
            {"airline": "British Airways", "airline_code": "BA", "price_gbp": 65, "departure_time": "09:00", "arrival_time": "10:25", "duration": "1h 25m", "stops": 0, "stops_label": "Direct"},
            {"airline": "LNER Train", "airline_code": "LN", "price_gbp": 40, "departure_time": "10:00", "arrival_time": "14:20", "duration": "4h 20m", "stops": 0, "stops_label": "Direct train"}
        ],
        "restaurants": [
            {"name": "The Witchery by the Castle", "cuisine": "Scottish Fine Dining", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Castlehill, Royal Mile", "must_try": "Angus beef fillet"},
            {"name": "Dishoom Edinburgh", "cuisine": "Bombay Caf\u00e9", "price_level": "\u00a3\u00a3", "rating": 4.6, "dietary": ["vegan-options", "vegetarian", "halal-options"], "address": "3A St Andrew Square", "must_try": "Black daal and naan"},
            {"name": "Oink", "cuisine": "Scottish Street Food", "price_level": "\u00a3", "rating": 4.5, "dietary": ["gluten-free-options"], "address": "34 Victoria Street", "must_try": "Hog roast roll"},
            {"name": "Ting Thai Caravan", "cuisine": "Thai Street Food", "price_level": "\u00a3", "rating": 4.4, "dietary": ["vegan-options", "gluten-free-options"], "address": "8 Teviot Place", "must_try": "Pad Thai"},
            {"name": "Ondine", "cuisine": "Seafood", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.7, "dietary": ["gluten-free-options"], "address": "2 George IV Bridge", "must_try": "Scottish lobster thermidor"}
        ],
        "attractions": [
            {"name": "Edinburgh Castle", "category": "Landmarks", "rating": 4.7, "address": "Castlehill", "price": "\u00a319.50", "hours": "09:30-17:00"},
            {"name": "Arthur's Seat", "category": "Outdoors", "rating": 4.8, "address": "Holyrood Park", "price": "Free", "hours": "All day"},
            {"name": "Royal Mile", "category": "Landmarks", "rating": 4.6, "address": "Royal Mile", "price": "Free", "hours": "All day"},
            {"name": "Scotch Whisky Experience", "category": "Food & Drink", "rating": 4.5, "address": "354 Castlehill", "price": "\u00a318", "hours": "10:00-18:00"},
            {"name": "National Museum of Scotland", "category": "Arts & Culture", "rating": 4.8, "address": "Chambers Street", "price": "Free", "hours": "10:00-17:00"}
        ],
        "local_tips": ["Take the free walking tour from the Royal Mile", "Avoid restaurants directly on the Royal Mile \u2014 better value one street over", "Climb Calton Hill for the best sunset views", "Get a Lothian Buses day ticket (\u00a34.80) for unlimited travel"]
    },
    "Bath": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "1h 25m", "operator": "GWR", "price_gbp": 25},
        "hotels": [
            {"name": "YHA Bath", "price_per_night_gbp": 22, "rating": 4.2, "stars": 2, "amenities": ["Free WiFi", "Kitchen", "Historic building"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "The Roseate Villa Bath", "price_per_night_gbp": 120, "rating": 4.6, "stars": 4, "amenities": ["Garden", "Free WiFi", "Breakfast"], "room_type": "Superior Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "The Royal Crescent Hotel & Spa", "price_per_night_gbp": 350, "rating": 4.9, "stars": 5, "amenities": ["Spa", "Garden", "Fine dining"], "room_type": "Master Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "Sally Lunn's Historic Eating House", "cuisine": "Traditional English", "price_level": "\u00a3", "rating": 4.5, "dietary": ["vegetarian-options"], "address": "4 North Parade Passage", "must_try": "Sally Lunn bun with cinnamon butter"},
            {"name": "The Circus Restaurant", "cuisine": "Modern British", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "34 Brock Street", "must_try": "Slow-cooked lamb shoulder"},
            {"name": "Yak Yeti Yak", "cuisine": "Nepalese", "price_level": "\u00a3\u00a3", "rating": 4.6, "dietary": ["vegan-options", "vegetarian", "gluten-free-options"], "address": "12 Pierrepont Street", "must_try": "Momos (Nepalese dumplings)"},
            {"name": "Sotto Sotto", "cuisine": "Italian", "price_level": "\u00a3\u00a3", "rating": 4.5, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "10 North Parade", "must_try": "Fresh pasta in underground cellar setting"}
        ],
        "attractions": [
            {"name": "Roman Baths", "category": "Landmarks", "rating": 4.7, "address": "Abbey Churchyard", "price": "\u00a318", "hours": "09:00-18:00"},
            {"name": "Thermae Bath Spa", "category": "Wellness", "rating": 4.6, "address": "The Hetling Pump Room", "price": "\u00a340", "hours": "09:00-21:30"},
            {"name": "Royal Crescent", "category": "Landmarks", "rating": 4.8, "address": "Royal Crescent", "price": "Free", "hours": "All day"},
            {"name": "Pulteney Bridge", "category": "Landmarks", "rating": 4.5, "address": "Bridge Street", "price": "Free", "hours": "All day"},
            {"name": "Bath Abbey", "category": "Arts & Culture", "rating": 4.6, "address": "Abbey Churchyard", "price": "\u00a38", "hours": "10:00-17:00"}
        ],
        "local_tips": ["Book Thermae Bath Spa for the twilight session \u2014 rooftop pool with city views at sunset", "Eat at Sally Lunn's before 11am to avoid the queue", "Take the train not the bus from London \u2014 much faster and scenic"]
    },
    "Lake District": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "3h 30m", "operator": "Avanti West Coast", "price_gbp": 35},
        "hotels": [
            {"name": "YHA Ambleside", "price_per_night_gbp": 20, "rating": 4.3, "stars": 2, "amenities": ["Lake views", "Kitchen", "Drying room"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "Waterhead Hotel", "price_per_night_gbp": 110, "rating": 4.5, "stars": 4, "amenities": ["Lake views", "Restaurant", "Garden"], "room_type": "Lake View Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "Linthwaite House", "price_per_night_gbp": 250, "rating": 4.8, "stars": 5, "amenities": ["Lake views", "Fine dining", "Fell walks from door"], "room_type": "Windermere Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "Homeground Coffee + Kitchen", "cuisine": "Caf\u00e9", "price_level": "\u00a3", "rating": 4.5, "dietary": ["vegan-options", "vegetarian", "gluten-free-options"], "address": "Windermere", "must_try": "Fell-walker's breakfast"},
            {"name": "The Drunken Duck Inn", "cuisine": "Gastropub", "price_level": "\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Barngates, Ambleside", "must_try": "Beer-battered fish with own-brew ale"},
            {"name": "L'Enclume", "cuisine": "Fine Dining (2 Michelin stars)", "price_level": "\u00a3\u00a3\u00a3\u00a3", "rating": 4.9, "dietary": ["vegetarian-options", "vegan-options"], "address": "Cavendish Street, Cartmel", "must_try": "Tasting menu (foraged local ingredients)"},
            {"name": "Chesters by the River", "cuisine": "Caf\u00e9 & Cakes", "price_level": "\u00a3", "rating": 4.6, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Skelwith Bridge", "must_try": "Homemade cakes by the river"}
        ],
        "attractions": [
            {"name": "Windermere Lake Cruises", "category": "Outdoors", "rating": 4.7, "address": "Bowness-on-Windermere", "price": "\u00a312", "hours": "09:00-17:00"},
            {"name": "Helvellyn Summit", "category": "Outdoors", "rating": 4.9, "address": "Between Thirlmere and Ullswater", "price": "Free", "hours": "All day"},
            {"name": "Beatrix Potter's Hill Top", "category": "Arts & Culture", "rating": 4.5, "address": "Near Sawrey", "price": "\u00a313", "hours": "10:00-16:30"},
            {"name": "Castlerigg Stone Circle", "category": "Landmarks", "rating": 4.7, "address": "Near Keswick", "price": "Free", "hours": "All day"}
        ],
        "local_tips": ["Check weather before hiking \u2014 conditions change fast. Use MWIS forecasts", "Grasmere Gingerbread Shop is tiny but worth the queue", "Book L'Enclume months in advance", "Rent a rowing boat on Windermere instead of the cruise"]
    },
    "Cornwall": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "5h", "operator": "GWR", "price_gbp": 30},
        "hotels": [
            {"name": "YHA Treyarnon Bay", "price_per_night_gbp": 18, "rating": 4.3, "stars": 2, "amenities": ["Beach access", "Surf hire nearby"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "The Headland Hotel", "price_per_night_gbp": 130, "rating": 4.5, "stars": 4, "amenities": ["Ocean views", "Pool", "Spa"], "room_type": "Sea View Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "The Scarlet Hotel", "price_per_night_gbp": 280, "rating": 4.8, "stars": 5, "amenities": ["Eco-spa", "Cliff-top pool", "Adults only"], "room_type": "Spectacular Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "The Hidden Hut", "cuisine": "Beach Caf\u00e9 & Feast Nights", "price_level": "\u00a3-\u00a3\u00a3", "rating": 4.8, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Porthcurnick Beach", "must_try": "Feast night BBQ (book months ahead)"},
            {"name": "Prawn on the Lawn", "cuisine": "Seafood", "price_level": "\u00a3\u00a3", "rating": 4.7, "dietary": ["gluten-free-options"], "address": "11 Duke Street, Padstow", "must_try": "Ceviche of the day"},
            {"name": "Porthminster Beach Caf\u00e9", "cuisine": "Seafood & Mediterranean", "price_level": "\u00a3\u00a3", "rating": 4.6, "dietary": ["vegetarian-options", "vegan-options", "gluten-free-options"], "address": "Porthminster Beach, St Ives", "must_try": "Seafood curry with ocean view"},
            {"name": "Ann's Pasties", "cuisine": "Cornish Pasties", "price_level": "\u00a3", "rating": 4.5, "dietary": ["vegetarian-options"], "address": "The Lizard", "must_try": "Traditional Cornish pasty (the real thing)"},
            {"name": "Rick Stein's Caf\u00e9", "cuisine": "Seafood", "price_level": "\u00a3\u00a3", "rating": 4.5, "dietary": ["gluten-free-options"], "address": "10 Middle Street, Padstow", "must_try": "Fish and chips with mushy peas"}
        ],
        "attractions": [
            {"name": "Eden Project", "category": "Outdoors", "rating": 4.6, "address": "Bodelva", "price": "\u00a332.50", "hours": "10:00-16:00"},
            {"name": "Minack Theatre", "category": "Arts & Culture", "rating": 4.8, "address": "Porthcurno", "price": "\u00a38", "hours": "10:00-17:00"},
            {"name": "St Michael's Mount", "category": "Landmarks", "rating": 4.7, "address": "Marazion", "price": "\u00a315", "hours": "Tide dependent"},
            {"name": "Fistral Beach", "category": "Outdoors", "rating": 4.7, "address": "Newquay", "price": "Free", "hours": "All day"},
            {"name": "Tate St Ives", "category": "Arts & Culture", "rating": 4.5, "address": "St Ives", "price": "\u00a310", "hours": "10:00-17:00"}
        ],
        "local_tips": ["The Hidden Hut feast nights sell out in seconds \u2014 set an alarm", "Rent a wetsuit and surfboard at Fistral for about \u00a320/2hrs", "Visit St Michael's Mount at low tide to walk the causeway", "Avoid Padstow in peak August \u2014 September has same weather, half the crowds"]
    },
    "York": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "1h 50m", "operator": "LNER", "price_gbp": 25},
        "hotels": [
            {"name": "Safestay York", "price_per_night_gbp": 16, "rating": 4.1, "stars": 2, "amenities": ["Free WiFi", "Bar", "Historic building"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "Hotel Indigo York", "price_per_night_gbp": 110, "rating": 4.5, "stars": 4, "amenities": ["Restaurant", "Bar", "City centre"], "room_type": "Standard King", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "The Grand, York", "price_per_night_gbp": 200, "rating": 4.7, "stars": 5, "amenities": ["Spa", "Pool", "Fine dining"], "room_type": "Deluxe Room", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "Betty's Caf\u00e9 Tea Rooms", "cuisine": "Traditional English Tea Room", "price_level": "\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "6-8 St Helen's Square", "must_try": "Fat Rascal scone and Yorkshire Tea"},
            {"name": "Shambles Kitchen", "cuisine": "Street Food", "price_level": "\u00a3", "rating": 4.5, "dietary": ["vegan-options", "gluten-free-options"], "address": "28 The Shambles", "must_try": "Pulled pork sandwich"},
            {"name": "Skosh", "cuisine": "Modern Small Plates", "price_level": "\u00a3\u00a3", "rating": 4.8, "dietary": ["vegetarian-options", "vegan-options"], "address": "98 Micklegate", "must_try": "Yorkshire-sourced small plates"},
            {"name": "The Star Inn the City", "cuisine": "Modern British", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.5, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Lendal Engine House", "must_try": "Yorkshire pudding wrap"}
        ],
        "attractions": [
            {"name": "York Minster", "category": "Landmarks", "rating": 4.8, "address": "Deangate", "price": "\u00a316", "hours": "09:30-16:30"},
            {"name": "The Shambles", "category": "Landmarks", "rating": 4.6, "address": "The Shambles", "price": "Free", "hours": "All day"},
            {"name": "JORVIK Viking Centre", "category": "Arts & Culture", "rating": 4.4, "address": "19 Coppergate", "price": "\u00a314", "hours": "10:00-17:00"},
            {"name": "York City Walls", "category": "Landmarks", "rating": 4.7, "address": "Various access points", "price": "Free", "hours": "08:00-dusk"},
            {"name": "National Railway Museum", "category": "Arts & Culture", "rating": 4.7, "address": "Leeman Road", "price": "Free", "hours": "10:00-17:00"}
        ],
        "local_tips": ["Walk the full city walls circuit (3.4km) \u2014 about 2 hours with photos", "Queue at Betty's before 9am or go to Little Betty's instead", "The Shambles inspired Diagon Alley \u2014 visit early morning for photos", "Ghost walks depart from The Minster every evening"]
    },
    "Brighton": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train", "duration": "1h", "operator": "Southern", "price_gbp": 15},
        "hotels": [
            {"name": "Kipps Brighton", "price_per_night_gbp": 18, "rating": 4.2, "stars": 2, "amenities": ["Free WiFi", "Kitchen", "Garden"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "Hotel Pelirocco", "price_per_night_gbp": 95, "rating": 4.4, "stars": 3, "amenities": ["Themed rooms", "Bar", "Seafront"], "room_type": "Rock n Roll Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "The Grand Brighton", "price_per_night_gbp": 200, "rating": 4.6, "stars": 5, "amenities": ["Spa", "Pool", "Seafront", "Fine dining"], "room_type": "Sea View Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "Silo", "cuisine": "Zero-Waste Fine Dining", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "vegan-options", "gluten-free-options"], "address": "39 Upper Gardner Street", "must_try": "Zero-waste tasting menu"},
            {"name": "Fatto a Mano", "cuisine": "Neapolitan Pizza", "price_level": "\u00a3", "rating": 4.6, "dietary": ["vegetarian-options", "vegan-options"], "address": "77 London Road", "must_try": "Nduja pizza"},
            {"name": "Curry Leaf Caf\u00e9", "cuisine": "South Indian", "price_level": "\u00a3\u00a3", "rating": 4.6, "dietary": ["vegan", "vegetarian", "gluten-free-options"], "address": "60 Ship Street", "must_try": "Keralan fish curry"},
            {"name": "Lucky Beach", "cuisine": "Beach Bar & Burgers", "price_level": "\u00a3", "rating": 4.3, "dietary": ["vegan-options", "gluten-free-options"], "address": "183 Kings Road Arches", "must_try": "Wagyu burger on the beach"}
        ],
        "attractions": [
            {"name": "Brighton Palace Pier", "category": "Landmarks", "rating": 4.4, "address": "Madeira Drive", "price": "Free (rides extra)", "hours": "10:00-22:00"},
            {"name": "Royal Pavilion", "category": "Landmarks", "rating": 4.6, "address": "Pavilion Buildings", "price": "\u00a318", "hours": "10:00-17:00"},
            {"name": "The Lanes", "category": "Shopping", "rating": 4.5, "address": "The Lanes", "price": "Free", "hours": "All day"},
            {"name": "North Laine", "category": "Shopping & Food", "rating": 4.6, "address": "North Laine", "price": "Free", "hours": "All day"}
        ],
        "local_tips": ["Skip pier restaurants \u2014 head to the Arches for beach bars", "North Laine on Saturday morning is peak brunch", "Take Volk's Electric Railway along the seafront \u2014 oldest electric railway in the world"]
    },
    "Scottish Highlands": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "sleeper train", "duration": "8h", "operator": "Caledonian Sleeper", "price_gbp": 50},
        "hotels": [
            {"name": "Black Isle Hostel", "price_per_night_gbp": 20, "rating": 4.4, "stars": 2, "amenities": ["Log fire", "Kitchen", "Mountain views"], "room_type": "Dormitory", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "Coul House Hotel", "price_per_night_gbp": 95, "rating": 4.5, "stars": 4, "amenities": ["Garden", "Restaurant", "Whisky bar"], "room_type": "Country View Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "Inverlochy Castle Hotel", "price_per_night_gbp": 380, "rating": 4.9, "stars": 5, "amenities": ["Loch views", "Michelin dining", "Hunting grounds"], "room_type": "Castle Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "The Crannog Seafood Restaurant", "cuisine": "Scottish Seafood", "price_level": "\u00a3\u00a3", "rating": 4.7, "dietary": ["gluten-free-options"], "address": "Town Pier, Fort William", "must_try": "Loch Linnhe langoustines"},
            {"name": "Caf\u00e9 1", "cuisine": "Modern Scottish", "price_level": "\u00a3\u00a3", "rating": 4.6, "dietary": ["vegetarian-options", "vegan-options", "gluten-free-options"], "address": "75 Castle Street, Inverness", "must_try": "Highland venison"},
            {"name": "The Three Chimneys", "cuisine": "Scottish Fine Dining", "price_level": "\u00a3\u00a3\u00a3\u00a3", "rating": 4.9, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Colbost, Isle of Skye", "must_try": "Skye seafood tasting menu"}
        ],
        "attractions": [
            {"name": "Glen Coe", "category": "Outdoors", "rating": 4.9, "address": "Glen Coe", "price": "Free", "hours": "All day"},
            {"name": "Loch Ness", "category": "Outdoors", "rating": 4.5, "address": "Inverness-shire", "price": "Free (boat tours \u00a315)", "hours": "All day"},
            {"name": "Ben Nevis", "category": "Outdoors", "rating": 4.8, "address": "Fort William", "price": "Free", "hours": "Allow 7-9 hours return"},
            {"name": "Isle of Skye", "category": "Outdoors", "rating": 4.9, "address": "Isle of Skye", "price": "Free", "hours": "All day"},
            {"name": "Glenfinnan Viaduct", "category": "Landmarks", "rating": 4.7, "address": "Glenfinnan", "price": "Free", "hours": "Harry Potter train ~10:45 and 15:00"}
        ],
        "local_tips": ["Midges are brutal June-September \u2014 bring Smidge repellent", "NC500 needs at least 5 days to do properly", "Book the Jacobite Steam Train months in advance", "Wild camping is legal in Scotland \u2014 follow the Outdoor Access Code"]
    },
    "Cotswolds": {
        "country": "United Kingdom", "domestic": True,
        "transport_from_london": {"type": "train+bus", "duration": "1h 30m", "operator": "GWR", "price_gbp": 20},
        "hotels": [
            {"name": "YHA Stow-on-the-Wold", "price_per_night_gbp": 20, "rating": 4.2, "stars": 2, "amenities": ["Kitchen", "Garden"], "room_type": "Private Room", "cancellation": "Free cancellation", "board_type": "Room Only"},
            {"name": "The Lygon Arms", "price_per_night_gbp": 150, "rating": 4.6, "stars": 4, "amenities": ["Spa", "Pool", "Historic inn"], "room_type": "Classic Double", "cancellation": "Free cancellation", "board_type": "Breakfast Included"},
            {"name": "Barnsley House", "price_per_night_gbp": 320, "rating": 4.8, "stars": 5, "amenities": ["Cinema", "Spa", "Kitchen garden"], "room_type": "Garden Suite", "cancellation": "Non-refundable", "board_type": "Breakfast Included"}
        ],
        "restaurants": [
            {"name": "The Wild Rabbit", "cuisine": "Modern British", "price_level": "\u00a3\u00a3\u00a3", "rating": 4.7, "dietary": ["vegetarian-options", "gluten-free-options"], "address": "Church Street, Kingham", "must_try": "Sunday roast"},
            {"name": "Daylesford Farm Caf\u00e9", "cuisine": "Organic British", "price_level": "\u00a3\u00a3", "rating": 4.5, "dietary": ["vegan-options", "vegetarian", "gluten-free"], "address": "Daylesford", "must_try": "Organic farmhouse breakfast"},
            {"name": "Chef's Dozen", "cuisine": "Bakery", "price_level": "\u00a3", "rating": 4.6, "dietary": ["vegetarian-options"], "address": "Chipping Norton", "must_try": "Sourdough cinnamon bun"}
        ],
        "attractions": [
            {"name": "Bibury (Arlington Row)", "category": "Landmarks", "rating": 4.7, "address": "Bibury", "price": "Free", "hours": "All day"},
            {"name": "Bourton-on-the-Water", "category": "Landmarks", "rating": 4.5, "address": "Bourton-on-the-Water", "price": "Free", "hours": "All day"},
            {"name": "Blenheim Palace", "category": "Landmarks", "rating": 4.7, "address": "Woodstock", "price": "\u00a330", "hours": "10:00-17:30"},
            {"name": "Castle Combe", "category": "Landmarks", "rating": 4.8, "address": "Castle Combe", "price": "Free", "hours": "All day"}
        ],
        "local_tips": ["You really need a car \u2014 public transport between villages is sparse", "Bourton-on-the-Water gets rammed in summer \u2014 visit early morning", "Castle Combe was used in War Horse and Stardust"]
    }
}

data.update(uk_cities)

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Added {len(uk_cities)} UK cities. Total cities: {len(data)}")
