# TravelBuddy - AI-Powered Travel Recommendation App

A full-stack travel planning application that uses machine learning (TF-IDF + cosine similarity) combined with rule-based filtering to recommend personalised travel destinations and build complete itineraries.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Python Flask |
| Database | Firebase Firestore + Firebase Auth |
| ML/Recommendation | scikit-learn (TF-IDF, cosine similarity) |
| APIs | Amadeus (flights/hotels), OpenWeatherMap, Foursquare Places |

## How to Run Locally

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- A Firebase project (free tier works)

### 1. Clone and set up environment variables

```bash
cp .env.example .env
# Edit .env with your Firebase config (required) and API keys (optional)
```

### 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The Flask server runs on `http://localhost:5000`.

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `USE_MOCK_DATA` | Yes | Set to `true` for demo mode (no real API keys needed). Set to `false` to use real APIs. |
| `FIREBASE_API_KEY` | Yes | Firebase project API key (from Firebase Console → Project Settings) |
| `FIREBASE_AUTH_DOMAIN` | Yes | Firebase Auth domain (e.g., `myproject.firebaseapp.com`) |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `FIREBASE_STORAGE_BUCKET` | Yes | Firebase storage bucket |
| `FIREBASE_MESSAGING_SENDER_ID` | Yes | Firebase messaging sender ID |
| `FIREBASE_APP_ID` | Yes | Firebase app ID |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | For backend | Path to Firebase Admin SDK service account JSON |
| `AMADEUS_API_KEY` | If `USE_MOCK_DATA=false` | Amadeus API key for flight/hotel search |
| `AMADEUS_API_SECRET` | If `USE_MOCK_DATA=false` | Amadeus API secret |
| `OPENWEATHER_API_KEY` | If `USE_MOCK_DATA=false` | OpenWeatherMap API key for weather forecasts |
| `FOURSQUARE_API_KEY` | If `USE_MOCK_DATA=false` | Foursquare Places API key for attractions |
| `FLASK_SECRET_KEY` | Yes | Random string for Flask session security |
| `FLASK_DEBUG` | No | Set to `true` for development |
| `FLASK_PORT` | No | Flask port (default: 5000) |

## Switching from Mock to Real APIs

1. Open your `.env` file
2. Change `USE_MOCK_DATA=true` to `USE_MOCK_DATA=false`
3. Fill in the API keys for whichever services you want to use:
   - **Amadeus**: Sign up at [developers.amadeus.com](https://developers.amadeus.com) → get API key and secret
   - **OpenWeatherMap**: Sign up at [openweathermap.org/api](https://openweathermap.org/api) → get API key
   - **Foursquare**: Sign up at [developer.foursquare.com](https://developer.foursquare.com) → get API key
4. Restart the backend server

The app gracefully falls back to mock data if any individual API call fails, so you can enable real APIs one at a time.

## How the Recommendation Engine Works

The engine uses a two-layer approach:

1. **Rule-based filtering**: Filters destinations by budget level and group type compatibility
2. **Content-based scoring**: Uses TF-IDF vectorisation and cosine similarity to match user style preferences (e.g., "beach", "culture") against destination tags and activities

See `backend/recommender/engine.py` for the fully commented implementation.

## Project Structure

```
travelbuddy/
├── frontend/              # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components (Login, Dashboard, etc.)
│   │   ├── context/       # React context (Auth)
│   │   └── services/      # API service layer
│   └── ...
├── backend/               # Python Flask API
│   ├── recommender/
│   │   ├── engine.py      # ML recommendation engine
│   │   └── destinations.json  # Destination database
│   ├── mock_data/         # Mock API responses for demo
│   ├── routes/            # Flask route blueprints
│   ├── app.py             # Flask entry point
│   └── firebase_config.py # Firebase Admin SDK setup
├── .env.example           # Environment variable template
└── README.md
```
