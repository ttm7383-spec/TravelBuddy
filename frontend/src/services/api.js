const API_BASE = "/api";

async function getToken(user) {
  if (!user) return null;
  try {
    return await user.getIdToken();
  } catch {
    return "demo-token";
  }
}

function headers(token) {
  const h = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

export async function getAllDestinations() {
  const res = await fetch(`${API_BASE}/destinations`);
  if (!res.ok) throw new Error("Failed to fetch destinations");
  return res.json();
}

export async function getRecommendations(user, params) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Request failed");
  return res.json();
}

export async function getItinerary(user, params) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/itinerary`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Request failed");
  return res.json();
}

export async function getMultiCityItinerary(user, params) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/itinerary/multi`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Request failed");
  return res.json();
}

export async function saveItinerary(user, itinerary) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/itinerary/save`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(itinerary),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Save failed");
  return res.json();
}

export async function getItineraries(user) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/itineraries`, {
    headers: headers(token),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Fetch failed");
  return res.json();
}

export async function saveProfile(user, profile) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/auth/profile`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Save failed");
  return res.json();
}

export async function getProfile(user) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/auth/profile`, {
    headers: headers(token),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Fetch failed");
  return res.json();
}

export async function checkVisa(passportCountry, destinationCountry) {
  const res = await fetch(`${API_BASE}/visa-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      passport_country: passportCountry,
      destination_country: destinationCountry,
    }),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Visa check failed");
  return res.json();
}

export async function sendChatMessage(user, message) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Chat request failed");
  return res.json();
}

export async function checkVisaBatch(passportCountry, destinations) {
  const res = await fetch(`${API_BASE}/visa-check/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      passport_country: passportCountry,
      destinations,
    }),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Batch visa check failed");
  return res.json();
}

export async function getSimilarDestinations(destinationId, topN = 5) {
  const res = await fetch(`${API_BASE}/destinations/${destinationId}/similar?top_n=${topN}`);
  if (!res.ok) throw new Error((await res.json()).error || "Failed to fetch similar destinations");
  return res.json();
}

export async function getTrendingDestinations(month = null, topN = 10) {
  const params = new URLSearchParams({ top_n: topN });
  if (month) params.set("month", month);
  const res = await fetch(`${API_BASE}/destinations/trending?${params}`);
  if (!res.ok) throw new Error((await res.json()).error || "Failed to fetch trending");
  return res.json();
}

export async function sendFeedback(userId, destinationId, action) {
  try {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId || "anonymous",
        destination_id: destinationId,
        action,
      }),
    });
  } catch (e) {
    console.warn("Feedback send failed:", e);
  }
}

export async function getFeedbackStats() {
  const res = await fetch(`${API_BASE}/feedback/stats`);
  return res.json();
}

// ── Google Calendar ────────────────────────────────────────────────────────

export async function getCalendarAuthUrl(user) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/calendar/auth-url`, {
    headers: headers(token),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Failed to get auth URL");
  return res.json();
}

export async function getCalendarWindows(user) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/calendar/free-windows`, {
    headers: headers(token),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Failed to fetch windows");
  return res.json();
}

export async function disconnectCalendar(user) {
  const token = await getToken(user);
  const res = await fetch(`${API_BASE}/calendar/disconnect`, {
    method: "POST",
    headers: headers(token),
  });
  if (!res.ok) throw new Error((await res.json()).error || "Disconnect failed");
  return res.json();
}
