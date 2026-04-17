# Google Calendar Integration Setup

This guide explains how to set up the Google Calendar integration for TravelBuddy.
Once configured, users can connect their Google Calendar to automatically find
free travel windows and auto-fill dates in the search form.

## Steps

1. **Go to [console.cloud.google.com](https://console.cloud.google.com)**

2. **Create a new project**
   - Click "Select a project" → "New Project"
   - Name: `TravelBuddy`
   - Click "Create"

3. **Enable Google Calendar API**
   - Go to APIs & Services → Library
   - Search for "Google Calendar API"
   - Click → Enable

4. **Create OAuth 2.0 credentials**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - If prompted, configure the OAuth consent screen first:
     - User Type: External
     - App name: TravelBuddy
     - Add your email as test user
   - Application type: **Web application**
   - Name: `TravelBuddy`
   - Authorised redirect URIs: `http://localhost:5000/api/calendar/callback`
   - Click "Create"

5. **Copy Client ID and Client Secret**
   - From the credentials page, copy both values

6. **Add to your `.env` file** (in the project root):
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:5000/api/calendar/callback
   ```

7. **Restart the backend**
   ```bash
   cd backend
   python app.py
   ```

## How It Works

1. User clicks "Connect Google Calendar" in the Dashboard
2. They are redirected to Google's OAuth consent screen
3. After granting permission, Google redirects back to the app
4. The app reads the user's calendar events for the next 90 days
5. Free windows of 2+ days are displayed as clickable chips
6. Clicking a chip auto-fills the departure and return dates

## Notes

- Only **read-only** calendar access is requested (`calendar.readonly` scope)
- Calendar tokens are stored securely in Firebase
- Users can disconnect at any time from the Dashboard
- In demo mode (no Google credentials), sample windows are shown
