import { useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getItinerary, saveItinerary, getSimilarDestinations } from "../services/api";
import DESTINATION_IMAGES from "../data/destinationImages";

/* ═══ Helpers ═══ */

const getDestImage = (id) =>
  DESTINATION_IMAGES[id] || `https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&h=600&fit=crop`;

const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : "";

const getHotelImage = (name, city) =>
  `https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop`;

const getActivityImage = (name, category) => {
  const kw = category?.toLowerCase().includes("food") ? "restaurant,food"
    : category?.toLowerCase().includes("nature") || category?.toLowerCase().includes("outdoor") ? "nature,park"
    : category?.toLowerCase().includes("culture") || category?.toLowerCase().includes("art") ? "museum,art"
    : category?.toLowerCase().includes("landmark") || category?.toLowerCase().includes("sight") ? "landmark,architecture"
    : "travel,attraction";
  return `https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop`;
};

const WEATHER_ICONS = {
  "01d": "\u2600\uFE0F", "01n": "\uD83C\uDF19", "02d": "\u26C5", "02n": "\u2601\uFE0F",
  "03d": "\u2601\uFE0F", "03n": "\u2601\uFE0F", "04d": "\u2601\uFE0F", "04n": "\u2601\uFE0F",
  "09d": "\uD83C\uDF27\uFE0F", "09n": "\uD83C\uDF27\uFE0F", "10d": "\uD83C\uDF26\uFE0F", "10n": "\uD83C\uDF27\uFE0F",
  "11d": "\u26C8\uFE0F", "11n": "\u26C8\uFE0F", "13d": "\u2744\uFE0F", "13n": "\u2744\uFE0F",
  "50d": "\uD83C\uDF2B\uFE0F", "50n": "\uD83C\uDF2B\uFE0F",
};

const CATEGORY_ICONS = { "Arts & Culture": "\uD83C\uDFDB\uFE0F", "Outdoors & Nature": "\uD83C\uDF3F", "Food & Drink": "\uD83C\uDF7D\uFE0F", "Landmarks & Sightseeing": "\uD83C\uDFF0", "Outdoors & Adventure": "\uD83E\uDDD7", "Shopping": "\uD83D\uDECD\uFE0F" };

function buildDayPlan(activities, restaurants, days) {
  const plan = [];
  const acts = [...(activities || [])];
  const rests = [...(restaurants || [])];
  for (let d = 0; d < days; d++) {
    const dayActs = acts.splice(0, 2);
    const dayRest = rests.splice(0, 1)[0];
    const eveningAct = acts.splice(0, 1)[0];
    plan.push({ day: d + 1, morning: dayActs[0] || null, afternoon: dayActs[1] || null, lunch: dayRest || null, evening: eveningAct || null });
  }
  return plan;
}

/* ═══ Sub-components ═══ */

function LoadingScreen() {
  const [tip, setTip] = useState(0);
  const tips = ["Finding the best local spots\u2026", "Checking flight options\u2026", "Picking hidden gems just for you\u2026", "Almost there \u2014 building your itinerary\u2026"];
  useEffect(() => { const t = setInterval(() => setTip(p => (p + 1) % tips.length), 1800); return () => clearInterval(t); }, []);
  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/></svg>
        </div>
        <div style={{ width: 180, height: 4, borderRadius: 4, background: "var(--border)", margin: "0 auto 20px", overflow: "hidden" }}>
          <div className="animate-pulse" style={{ height: "100%", borderRadius: 4, background: "var(--primary)", width: "60%" }} />
        </div>
        <p style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 700, color: "var(--dark)", margin: "0 0 6px 0" }}>Building your itinerary</p>
        <p style={{ fontSize: 14, color: "var(--muted)", margin: 0 }}>{tips[tip]}</p>
      </div>
    </div>
  );
}

function DayCard({ day, dayNum, date, weather }) {
  const slots = [
    { time: "MORNING", item: day.morning, type: "activity" },
    { time: "AFTERNOON", item: day.afternoon, type: "activity" },
    { time: "LUNCH", item: day.lunch, type: "restaurant" },
    { time: "EVENING", item: day.evening, type: "activity" },
  ].filter(s => s.item);

  return (
    <div style={{ display: "flex", gap: 20 }}>
      {/* Day badge + timeline */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 48 }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--primary)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, fontFamily: "'DM Sans', sans-serif" }}>
          {dayNum}
        </div>
        <div style={{ flex: 1, width: 2, background: "var(--primary)", opacity: 0.2, marginTop: 8 }} />
      </div>

      {/* Card */}
      <div style={{ flex: 1, background: "var(--surface)", borderRadius: 16, boxShadow: "var(--shadow-card)", borderLeft: "4px solid var(--primary)", overflow: "hidden" }}>
        {/* Header */}
        <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid var(--border)" }}>
          <div>
            <p style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 16, color: "var(--dark)", margin: 0 }}>{date || `Day ${dayNum}`}</p>
          </div>
          {weather && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--body)" }}>
              <span style={{ fontSize: 20 }}>{WEATHER_ICONS[weather.icon] || "\uD83C\uDF24\uFE0F"}</span>
              <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 14 }}>{weather.temp_high_c}{"\u00b0"}</span>
            </div>
          )}
        </div>

        {/* Slots */}
        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          {slots.map((slot, i) => (
            <div key={i}>
              <p className="label-uppercase" style={{ marginBottom: 8 }}>{slot.time}</p>
              {slot.type === "activity" && slot.item && (
                <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
                  <div style={{ height: 100, position: "relative", backgroundImage: `url(${getActivityImage(slot.item.name, slot.item.category)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
                    <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 40%, rgba(26,26,46,0.6))" }} />
                    <div style={{ position: "absolute", bottom: 10, left: 12, right: 12 }}>
                      <p style={{ color: "white", fontWeight: 700, fontSize: 14, margin: 0, fontFamily: "'DM Sans', sans-serif" }}>{slot.item.name}</p>
                    </div>
                  </div>
                  <div style={{ padding: "10px 12px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 11, padding: "3px 8px", borderRadius: 6, background: "var(--primary-light)", color: "var(--primary-dark)", fontWeight: 500 }}>
                      {CATEGORY_ICONS[slot.item.category] || "\uD83D\uDCCD"} {slot.item.category}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--warning)" }}>{"\u2605"} {slot.item.rating}</span>
                  </div>
                </div>
              )}
              {slot.type === "restaurant" && slot.item && (
                <div style={{ borderRadius: 12, padding: 14, background: "var(--accent-light)", border: "1px solid #FFD6BF" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8 }}>
                    <div>
                      <p style={{ fontWeight: 600, color: "var(--dark)", fontSize: 14, margin: 0 }}>{slot.item.name}</p>
                      <p style={{ fontSize: 12, color: "var(--body)", margin: "2px 0 0" }}>{slot.item.cuisine} &middot; {slot.item.price_level}</p>
                      {slot.item.must_try && <p style={{ fontSize: 12, color: "var(--accent)", margin: "4px 0 0", fontWeight: 500 }}>Must try: {slot.item.must_try}</p>}
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--warning)", flexShrink: 0 }}>{"\u2605"} {slot.item.rating}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
          {slots.length === 0 && (
            <p style={{ color: "var(--muted)", fontSize: 14, textAlign: "center", padding: "16px 0", margin: 0 }}>{"Free day \u2014 explore at your own pace!"}</p>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══ Main Component ═══ */

export default function Itinerary() {
  const { destinationId } = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [similarDests, setSimilarDests] = useState([]);
  const [activeTab, setActiveTab] = useState("itinerary");
  const [activityFilter, setActivityFilter] = useState("All");

  useEffect(() => {
    if (destinationId && !destinationId.startsWith("custom")) {
      getSimilarDestinations(destinationId, 4).then(d => setSimilarDests(d.similar || [])).catch(() => {});
    }
  }, [destinationId]);

  useEffect(() => {
    async function load() {
      try {
        const customCity = searchParams.get("custom_city");
        const params = {
          departure_city: searchParams.get("departure") || "London",
          travel_dates: { start: searchParams.get("start") || "2026-04-15", end: searchParams.get("end") || "2026-04-22" },
          budget_level: searchParams.get("budget") || "medium",
          nationality: searchParams.get("nationality") || "GB",
        };
        if (customCity) params.custom_city = customCity;
        else params.destination_id = destinationId;
        const data = await getItinerary(user, params);
        setItinerary(data);
      } catch (err) { setError(err.message || "Failed to load itinerary"); }
      finally { setLoading(false); }
    }
    load();
  }, [destinationId, searchParams, user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Persist to localStorage so /my-trips always has something (works offline).
      try {
        const key = "travelbuddy_saved_trips";
        const existing = JSON.parse(localStorage.getItem(key) || "[]");
        const id = itinerary?.destination?.id || `custom-${Date.now()}`;
        const entry = {
          id,
          destination_id: itinerary?.destination?.id,
          name: itinerary?.destination?.name,
          country: itinerary?.destination?.country,
          image: getDestImage(itinerary?.destination?.id),
          start_date: itinerary?.dates?.start,
          end_date: itinerary?.dates?.end,
          dates: itinerary?.dates,
          total_cost_gbp: itinerary?.estimated_total_cost_gbp,
          saved_at: new Date().toISOString(),
        };
        const deduped = existing.filter((t) => t.id !== id);
        localStorage.setItem(key, JSON.stringify([entry, ...deduped].slice(0, 50)));
      } catch (storageErr) {
        console.warn("localStorage save failed:", storageErr);
      }
      // Also try the backend save (non-fatal if it fails — localStorage is the source of truth for MyTrips).
      try { await saveItinerary(user, itinerary); } catch (e) { console.warn("Backend save skipped:", e); }
      setSaved(true);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingScreen />;

  if (error) return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "60px 24px" }}>
      <div style={{ background: "#FFF5F5", borderRadius: 16, padding: 40, textAlign: "center", borderLeft: "4px solid #E53E3E" }}>
        <p style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 700, color: "var(--dark)", margin: "0 0 8px" }}>{"Couldn't load your itinerary"}</p>
        <p style={{ fontSize: 14, color: "#E53E3E", margin: "0 0 20px" }}>{error}</p>
        <button onClick={() => navigate("/dashboard")} style={{ fontSize: 14, fontWeight: 600, padding: "10px 24px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--surface)", color: "var(--body)", cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>
          Back to Dashboard
        </button>
      </div>
    </div>
  );

  const { destination, dates, weather, flights, hotels, activities, restaurants, estimated_total_cost_gbp, visa_info, cost_breakdown, is_live_prices } = itinerary;
  const dayPlan = buildDayPlan(activities, restaurants, dates?.duration_days || 7);
  const destName = cap(destination?.name);
  const allCategories = ["All", ...new Set((activities || []).map(a => a.category).filter(Boolean))];
  const filteredActivities = activityFilter === "All" ? activities : activities?.filter(a => a.category === activityFilter);

  const insiderTips = [
    { tip: `Use public transport in ${destName} \u2014 it's much cheaper than taxis` },
    { tip: "Visit popular attractions first thing in the morning to avoid queues" },
    { tip: "Carry some local cash \u2014 many smaller places don't take cards" },
    { tip: "Learn a few words of the local language \u2014 locals really appreciate it" },
    { tip: "Download offline maps before you go \u2014 roaming data can be expensive" },
    { tip: "The best photos happen at golden hour \u2014 1 hour after sunrise and before sunset" },
  ];

  const avgTemp = weather?.daily_forecast?.length
    ? Math.round(weather.daily_forecast.reduce((s, d) => s + (d.temp_high_c || 20), 0) / weather.daily_forecast.length) : 20;
  const packingList = avgTemp > 25
    ? ["Light breathable clothing", "Sunglasses", "SPF 50+ sunscreen", "Sun hat", "Reusable water bottle", "Comfortable sandals"]
    : avgTemp > 15
    ? ["Light jacket for evenings", "Comfortable walking shoes", "Compact umbrella", "Layers", "Water bottle"]
    : ["Warm layers", "Waterproof jacket", "Sturdy boots", "Gloves & scarf", "Umbrella"];

  /* Determine cheapest and fastest flights */
  const cheapestFlightIdx = (flights || []).reduce((minI, f, i, arr) => (f.price_gbp < arr[minI].price_gbp ? i : minI), 0);
  const fastestFlightIdx = (flights || []).reduce((minI, f, i, arr) => {
    const dur = (s) => { const m = (s || "").match(/(\d+)h\s*(\d+)?/); return m ? parseInt(m[1]) * 60 + parseInt(m[2] || 0) : 9999; };
    return dur(f.duration) < dur(arr[minI].duration) ? i : minI;
  }, 0);

  /* Determine best-value hotel (best rating/price ratio, fallback to first sorted by price) */
  const bestValueHotelIdx = (hotels || []).reduce((bestI, h, i, arr) => {
    const ratio = (h2) => (h2.rating || 3) / (h2.price_per_night_gbp || 1);
    return ratio(h) > ratio(arr[bestI]) ? i : bestI;
  }, 0);

  const TABS = [
    { id: "itinerary", label: "Itinerary" },
    { id: "hotels", label: "Hotels" },
    { id: "flights", label: "Flights" },
    { id: "cost", label: "Budget" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>

      {/* ═══ HERO ═══ */}
      <div style={{ height: 420, position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, backgroundImage: `url(${getDestImage(destination?.id)})`, backgroundSize: "cover", backgroundPosition: "center" }} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(26,26,46,0.25) 0%, rgba(26,26,46,0.8) 100%)" }} />
        <div style={{ position: "absolute", inset: 0, maxWidth: 960, margin: "0 auto", padding: "0 24px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <button onClick={() => navigate("/dashboard")} style={{
            marginTop: 24, alignSelf: "flex-start", fontSize: 14, color: "rgba(255,255,255,0.6)", cursor: "pointer",
            border: 0, background: "transparent", fontFamily: "'DM Sans', sans-serif",
          }}
            onMouseEnter={e => e.currentTarget.style.color = "white"}
            onMouseLeave={e => e.currentTarget.style.color = "rgba(255,255,255,0.6)"}>
            {"\u2190"} Back
          </button>
          <div style={{ paddingBottom: 32 }}>
            <p style={{ fontSize: 16, fontWeight: 500, color: "var(--primary)", margin: "0 0 4px", fontFamily: "'DM Sans', sans-serif" }}>
              {destination?.country || ""}
            </p>
            <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 44, fontWeight: 700, color: "white", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
              {destName}
            </h1>
            <div style={{ display: "flex", gap: 20, color: "rgba(255,255,255,0.6)", fontSize: 14 }}>
              <span>{dates?.start} {"\u2013"} {dates?.end}</span>
              <span>{dates?.duration_days} days</span>
              <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, color: "var(--primary)" }}>{"\u00a3"}{destination?.avg_daily_cost_gbp}/day avg</span>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ STICKY TABS ═══ */}
      <div style={{ position: "sticky", top: 64, zIndex: 20, background: "var(--surface)", borderBottom: "2px solid var(--border)", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex" }}>
            {TABS.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                padding: "16px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer",
                border: 0, background: "transparent", fontFamily: "'DM Sans', sans-serif",
                color: activeTab === tab.id ? "var(--primary)" : "var(--muted)",
                borderBottom: activeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
                marginBottom: -2, transition: "all 200ms",
              }}>{tab.label}</button>
            ))}
          </div>
          <button onClick={handleSave} disabled={saving || saved} style={{
            padding: "8px 20px", borderRadius: 8, border: 0, cursor: "pointer", fontSize: 14, fontWeight: 600,
            fontFamily: "'DM Sans', sans-serif", transition: "all 200ms",
            background: saved ? "var(--primary-light)" : "var(--accent)",
            color: saved ? "var(--primary-dark)" : "white",
            opacity: saving ? 0.6 : 1,
          }}>
            {saved ? "\u2713 Saved" : saving ? "Saving\u2026" : "Save Trip"}
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 960, margin: "0 auto", padding: "32px 24px 60px" }}>

        {/* ── Visa Alert ── */}
        {visa_info && (
          <div style={{
            borderRadius: 12, padding: 20, marginBottom: 28, display: "flex", alignItems: "start", gap: 16,
            background: visa_info.visa_required ? "var(--accent-light)" : "var(--primary-light)",
            borderLeft: `4px solid ${visa_info.visa_required ? "var(--warning)" : "var(--success)"}`,
          }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 700, color: "var(--dark)", fontSize: 15, margin: "0 0 4px" }}>Visa & Entry</p>
              <p style={{ fontSize: 14, color: visa_info.visa_required ? "var(--accent)" : "var(--primary-dark)", fontWeight: 500, margin: 0 }}>
                {visa_info.requirement === "visa-free" ? "No visa required" : visa_info.requirement === "visa-on-arrival" ? "Visa on arrival" : visa_info.requirement === "e-visa" ? "E-Visa required" : "Visa required"}
                {visa_info.duration_days > 0 && ` \u2014 up to ${visa_info.duration_days} days`}
              </p>
              {visa_info.processing_days > 0 && <p style={{ fontSize: 12, color: "var(--warning)", fontWeight: 600, margin: "6px 0 0" }}>Apply at least {visa_info.processing_days} days before departure</p>}
            </div>
            {visa_info.cost_gbp > 0 && (
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 20, color: "var(--dark)", margin: 0 }}>{"\u00a3"}{visa_info.cost_gbp}</p>
                <p style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>visa fee</p>
              </div>
            )}
          </div>
        )}

        {/* ═══ TAB: ITINERARY ═══ */}
        {activeTab === "itinerary" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>

            {/* Weather strip */}
            {weather?.daily_forecast && (
              <div style={{ background: "var(--surface)", borderRadius: 16, padding: 24, boxShadow: "var(--shadow-card)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <h2 style={{ fontSize: 20, margin: 0 }}>Weather Forecast</h2>
                  <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{weather.summary}</p>
                </div>
                <div className="overflow-x-auto" style={{ display: "flex", gap: 8, paddingBottom: 4 }}>
                  {weather.daily_forecast.map((day, i) => (
                    <div key={i} style={{ flexShrink: 0, textAlign: "center", padding: "10px 14px", borderRadius: 10, background: "var(--bg)", minWidth: 64 }}>
                      <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, letterSpacing: "0.5px" }}>{day.day?.slice(0, 3)}</div>
                      <div style={{ fontSize: 22, margin: "4px 0" }}>{WEATHER_ICONS[day.icon] || "\uD83C\uDF24\uFE0F"}</div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 14, color: "var(--dark)" }}>{day.temp_high_c}{"\u00b0"}</div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: "var(--muted)" }}>{day.temp_low_c}{"\u00b0"}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Day-by-day */}
            <div>
              <h2 style={{ fontSize: 24, marginBottom: 20 }}>Your Itinerary</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {dayPlan.map((day, i) => (
                  <DayCard key={i} day={day} dayNum={day.day}
                    date={weather?.daily_forecast?.[i] ? `${weather.daily_forecast[i].day}, ${dates?.start ? new Date(new Date(dates.start).getTime() + i * 86400000).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : ""}` : null}
                    weather={weather?.daily_forecast?.[i]} />
                ))}
              </div>
            </div>

            {/* All activities */}
            <div style={{ background: "var(--surface)", borderRadius: 16, padding: 24, boxShadow: "var(--shadow-card)" }}>
              <h2 style={{ fontSize: 20, marginBottom: 16 }}>All Things To Do</h2>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
                {allCategories.map(cat => (
                  <button key={cat} onClick={() => setActivityFilter(cat)} style={{
                    padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: 12, fontWeight: 600,
                    fontFamily: "'DM Sans', sans-serif", border: activityFilter === cat ? 0 : "1px solid var(--border)",
                    background: activityFilter === cat ? "var(--primary)" : "var(--bg)",
                    color: activityFilter === cat ? "white" : "var(--body)", transition: "all 150ms",
                  }}>{CATEGORY_ICONS[cat] || ""} {cat}</button>
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {(filteredActivities || []).map((a, i) => (
                  <div key={i} style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)", display: "flex" }}>
                    <div style={{ width: 96, flexShrink: 0, backgroundImage: `url(${getActivityImage(a.name, a.category)})`, backgroundSize: "cover", backgroundPosition: "center" }} />
                    <div style={{ padding: 12, flex: 1 }}>
                      <p style={{ fontWeight: 600, color: "var(--dark)", fontSize: 13, margin: "0 0 4px" }}>{a.name}</p>
                      <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 6, background: "var(--primary-light)", color: "var(--primary-dark)", fontWeight: 500 }}>
                        {CATEGORY_ICONS[a.category] || "\uD83D\uDCCD"} {a.category}
                      </span>
                      {a.address && <p style={{ fontSize: 11, color: "var(--muted)", margin: "4px 0 0" }}>{a.address}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Where to eat */}
            {restaurants && restaurants.length > 0 && (
              <div style={{ background: "var(--surface)", borderRadius: 16, padding: 24, boxShadow: "var(--shadow-card)" }}>
                <h2 style={{ fontSize: 20, marginBottom: 16 }}>Where to Eat</h2>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  {restaurants.map((r, i) => (
                    <div key={i} style={{ borderRadius: 12, padding: 16, border: "1px solid var(--border)", transition: "border-color 200ms" }}
                      onMouseEnter={e => e.currentTarget.style.borderColor = "var(--primary)"}
                      onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border)"}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8, marginBottom: 4 }}>
                        <p style={{ fontWeight: 600, color: "var(--dark)", fontSize: 14, margin: 0 }}>{r.name}</p>
                        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--warning)", flexShrink: 0 }}>{"\u2605"} {r.rating}</span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--body)", margin: 0 }}>{r.cuisine} &middot; {r.price_level}</p>
                      {r.must_try && <p style={{ fontSize: 12, color: "var(--accent)", fontWeight: 500, margin: "4px 0 0" }}>Must try: {r.must_try}</p>}
                      {r.dietary && r.dietary.length > 0 && (
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 8 }}>
                          {r.dietary.map(d => (
                            <span key={d} style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "var(--primary-light)", color: "var(--primary-dark)", fontWeight: 500 }}>
                              {d.replace("-options", " friendly").replace("-", " ")}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Insider tips */}
            <div style={{ background: "var(--primary-light)", borderLeft: "4px solid var(--primary)", borderRadius: 12, padding: 24 }}>
              <h2 style={{ fontSize: 20, marginBottom: 16 }}>Local Insider Tips</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {insiderTips.map((t, i) => (
                  <p key={i} style={{ fontSize: 14, color: "var(--body)", margin: 0, lineHeight: 1.6 }}>{"\u2022"} {t.tip}</p>
                ))}
              </div>
            </div>

            {/* Packing */}
            <div style={{ background: "var(--surface)", borderRadius: 16, padding: 24, boxShadow: "var(--shadow-card)" }}>
              <h2 style={{ fontSize: 20, marginBottom: 4 }}>What to Pack</h2>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 16 }}>Based on {avgTemp > 25 ? "warm" : avgTemp > 15 ? "mild" : "cool"} weather (avg {avgTemp}{"\u00b0"}C)</p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {packingList.map((item, i) => (
                  <span key={i} style={{ fontSize: 13, padding: "8px 14px", borderRadius: 8, background: "var(--bg)", color: "var(--body)", fontWeight: 500 }}>{item}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: HOTELS ═══ */}
        {activeTab === "hotels" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 24, marginBottom: 0 }}>Hotels in {destName}</h2>
            <p style={{ color: "var(--muted)", fontSize: 14, margin: "-12px 0 0" }}>{dates?.duration_days} nights &middot; {dates?.start} to {dates?.end}</p>
            {(hotels || []).map((h, i) => (
              <div key={i} style={{ background: "var(--surface)", borderRadius: 16, overflow: "hidden", boxShadow: "var(--shadow-card)", border: "1px solid var(--border)" }}>
                {/* Hotel image */}
                <div style={{ height: 200, position: "relative", overflow: "hidden" }}>
                  <img
                    src={h.image_url || getHotelImage(h.name, destination?.name)}
                    onError={e => { e.target.onerror = null; e.target.src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'; }}
                    alt={h.name}
                    style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                  />
                  <div style={{ position: "absolute", top: 12, left: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {i === bestValueHotelIdx && (
                      <span style={{ fontSize: 11, padding: "4px 12px", borderRadius: 6, background: "#15803D", color: "white", fontWeight: 700, letterSpacing: "0.3px" }}>Best value</span>
                    )}
                    {h.cancellation === "Free cancellation" && (
                      <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "rgba(0,0,0,0.6)", color: "#4ADE80", fontWeight: 600, backdropFilter: "blur(4px)" }}>Free cancellation</span>
                    )}
                    {h.board_type && h.board_type !== "Room Only" && (
                      <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "rgba(0,0,0,0.6)", color: "#00A3A3", fontWeight: 600, backdropFilter: "blur(4px)" }}>{h.board_type}</span>
                    )}
                  </div>
                </div>

                {/* Hotel details */}
                <div style={{ padding: "20px 24px" }}>
                  {/* Name + star dots */}
                  <div style={{ display: "flex", alignItems: "start", justifyContent: "space-between", gap: 16, marginBottom: 10 }}>
                    <div>
                      <h3 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 17, color: "var(--dark)", margin: "0 0 6px" }}>{h.name}</h3>
                      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        {Array.from({ length: h.stars || 3 }).map((_, j) => (
                          <span key={j} style={{ width: 8, height: 8, borderRadius: "50%", background: "#00A3A3", display: "inline-block" }} />
                        ))}
                        <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 4 }}>{h.stars || 3}-star hotel</span>
                      </div>
                    </div>

                    {/* Review score badge (booking.com style) */}
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                      <div style={{ textAlign: "right" }}>
                        <p style={{ fontSize: 12, fontWeight: 700, color: "var(--dark)", margin: 0 }}>
                          {h.rating >= 4.5 ? "Exceptional" : h.rating >= 4 ? "Excellent" : h.rating >= 3.5 ? "Very Good" : "Good"}
                        </p>
                        {h.review_count && <p style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>{h.review_count?.toLocaleString()} reviews</p>}
                      </div>
                      <div style={{
                        width: 40, height: 40, borderRadius: "8px 8px 8px 0", background: "#00A3A3", color: "white",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 15,
                      }}>
                        {h.rating}
                      </div>
                    </div>
                  </div>

                  {/* Tags row */}
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                    {h.cancellation === "Free cancellation" && (
                      <span style={{ fontSize: 12, color: "#15803D", fontWeight: 600 }}>Free cancellation</span>
                    )}
                    {h.board_type && h.board_type !== "Room Only" && (
                      <span style={{ fontSize: 12, color: "#00A3A3", fontWeight: 600 }}>
                        {h.board_type === "Breakfast Included" || h.board_type?.toLowerCase().includes("breakfast") ? "Breakfast included" : h.board_type}
                      </span>
                    )}
                  </div>

                  {/* Amenities */}
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
                    {(h.amenities || []).slice(0, 5).map(a => (
                      <span key={a} style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "var(--bg)", color: "var(--body)", fontWeight: 500 }}>{a}</span>
                    ))}
                  </div>

                  {/* Price + book button */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
                    <div />
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 22, color: "#00A3A3" }}>{"\u00a3"}{h.price_per_night_gbp}</span>
                      <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 4 }}>/night</span>
                    </div>
                  </div>

                  <a href={h.booking_url || h.search_url || `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(h.name + ' ' + (destination?.name || ''))}`}
                    target="_blank" rel="noopener noreferrer"
                    style={{
                      display: "block", width: "100%", padding: "12px 0", borderRadius: 8, border: 0, cursor: "pointer",
                      background: "#FF6B2B", color: "white", fontSize: 14, fontWeight: 700,
                      fontFamily: "'DM Sans', sans-serif", textAlign: "center", textDecoration: "none",
                      boxSizing: "border-box",
                    }}>
                    Book on Booking.com
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ═══ TAB: FLIGHTS ═══ */}
        {activeTab === "flights" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 24, margin: 0 }}>Flights</h2>
              {!is_live_prices && <span style={{ fontSize: 12, padding: "4px 12px", borderRadius: 6, background: "var(--bg)", color: "var(--muted)", fontWeight: 500 }}>Estimated prices</span>}
            </div>
            {(flights || []).map((f, i) => {
              const isCheapest = i === cheapestFlightIdx;
              const isFastest = i === fastestFlightIdx && i !== cheapestFlightIdx;
              return (
                <div key={i} style={{
                  background: "var(--surface)", borderRadius: 16, padding: 24, boxShadow: "var(--shadow-card)",
                  border: isCheapest ? "2px solid #15803D" : isFastest ? "2px solid #00A3A3" : "1px solid var(--border)",
                  position: "relative",
                }}>
                  {/* Badges */}
                  <div style={{ position: "absolute", top: -1, right: 16, display: "flex", gap: 6 }}>
                    {isCheapest && (
                      <span style={{ fontSize: 11, padding: "4px 12px", borderRadius: "0 0 8px 8px", background: "#15803D", color: "white", fontWeight: 700 }}>{"\uD83D\uDC9A"} Best price</span>
                    )}
                    {isFastest && (
                      <span style={{ fontSize: 11, padding: "4px 12px", borderRadius: "0 0 8px 8px", background: "#1a73e8", color: "white", fontWeight: 700 }}>{"\u26A1"} Fastest</span>
                    )}
                  </div>

                  {/* Top row: airline + price */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <div style={{ width: 44, height: 44, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, background: "#00A3A3", color: "white", fontFamily: "'DM Sans', sans-serif" }}>
                        {(f.airline_code || f.airline?.slice(0, 2) || "\u2708").toUpperCase()}
                      </div>
                      <div>
                        <p style={{ fontWeight: 700, color: "var(--dark)", fontSize: 15, margin: 0 }}>{f.airline}</p>
                        <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{f.flight_number}</p>
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 22, color: "#00A3A3", margin: 0 }}>{"\u00a3"}{f.price_gbp}</p>
                    </div>
                  </div>

                  {/* Route visual */}
                  <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
                    <div style={{ textAlign: "center" }}>
                      <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 20, color: "var(--dark)", margin: 0 }}>{f.departure?.time}</p>
                      <p style={{ fontSize: 12, color: "var(--muted)", margin: 0, fontWeight: 600 }}>{f.departure?.airport}</p>
                    </div>
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <p style={{ fontSize: 12, color: "var(--muted)", margin: "0 0 4px", fontWeight: 600 }}>{f.duration}</p>
                      <div style={{ display: "flex", alignItems: "center", width: "100%", gap: 4 }}>
                        <div style={{ flex: 1, height: 1, borderTop: "2px dashed var(--border)" }} />
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#00A3A3" style={{ flexShrink: 0 }}><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>
                        <div style={{ flex: 1, height: 1, borderTop: "2px dashed var(--border)" }} />
                      </div>
                      <p style={{ fontSize: 11, margin: "4px 0 0", fontWeight: 600,
                        color: f.stops === 0 ? "#15803D" : "#D97706",
                      }}>
                        {f.stops_label || (f.stops === 0 ? "Direct" : `${f.stops} stop`)}
                      </p>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 20, color: "var(--dark)", margin: 0 }}>{f.arrival?.time}</p>
                      <p style={{ fontSize: 12, color: "var(--muted)", margin: 0, fontWeight: 600 }}>{f.arrival?.airport}</p>
                    </div>
                  </div>

                  {/* Cabin class + booking buttons */}
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                    <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "var(--bg)", color: "var(--muted)", fontWeight: 500 }}>{f.cabin_class || "Economy"}</span>
                    <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                      <a href={f.google_flights_url || `https://www.google.com/travel/flights?q=${encodeURIComponent(`flights from ${f.departure?.airport} to ${f.arrival?.airport}${f.departure?.date ? ` on ${f.departure.date}` : ""}`)}`}
                        target="_blank" rel="noopener noreferrer"
                        style={{ fontSize: 13, padding: "8px 16px", borderRadius: 8, background: "#1a73e8", color: "white", textDecoration: "none", fontWeight: 600 }}>
                        {"\uD83D\uDD35"} Google Flights
                      </a>
                      <a href={f.skyscanner_url || `https://www.skyscanner.net/transport/flights/${(f.departure?.airport || "lhr").toLowerCase()}/${(f.arrival?.airport || "").toLowerCase()}/`}
                        target="_blank" rel="noopener noreferrer"
                        style={{ fontSize: 13, padding: "8px 16px", borderRadius: 8, background: "#FF6B35", color: "white", textDecoration: "none", fontWeight: 600 }}>
                        {"\uD83D\uDFE0"} Skyscanner
                      </a>
                    </div>
                  </div>
                </div>
              );
            })}
            {(flights && flights.length > 0) && (
              <p style={{ fontSize: 12, color: "var(--muted)", margin: "4px 2px 0", lineHeight: 1.5 }}>
                Prices are estimates. Click to check live prices on Google Flights or Skyscanner.
              </p>
            )}
          </div>
        )}

        {/* ═══ TAB: BUDGET ═══ */}
        {activeTab === "cost" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 24, margin: 0 }}>Cost Breakdown</h2>
            <div style={{ background: "var(--surface)", borderRadius: 16, overflow: "hidden", boxShadow: "var(--shadow-card)", border: "1px solid var(--border)" }}>
              {cost_breakdown && [
                { label: "Return Flights", sub: "Cheapest option \u00d7 2", val: cost_breakdown.flights },
                { label: "Accommodation", sub: `Cheapest hotel \u00d7 ${dates?.duration_days} nights`, val: cost_breakdown.accommodation },
                { label: "Food & Dining", sub: `Estimated \u00d7 ${dates?.duration_days} days`, val: cost_breakdown.food },
                { label: "Activities", sub: `Estimated \u00d7 ${dates?.duration_days} days`, val: cost_breakdown.activities },
                { label: "Visa & Entry", sub: visa_info?.requirement || "N/A", val: cost_breakdown.visa, free: cost_breakdown.visa === 0 },
                ...(cost_breakdown.insurance > 0 ? [{ label: "Travel Insurance", sub: "~3% of trip cost", val: cost_breakdown.insurance }] : []),
              ].map((row, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, padding: "16px 24px", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark)", margin: 0 }}>{row.label}</p>
                    <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{row.sub}</p>
                  </div>
                  <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 16, color: row.free ? "var(--success)" : "var(--dark)", margin: 0 }}>
                    {row.free ? "Free" : `\u00a3${(row.val || 0).toLocaleString()}`}
                  </p>
                </div>
              ))}
              <div style={{ padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#1A1A2E" }}>
                <div>
                  <p style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 18, color: "white", margin: 0 }}>Total</p>
                  <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", margin: "2px 0 0" }}>per person</p>
                </div>
                <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 28, color: "#00A3A3", margin: 0 }}>
                  {"\u00a3"}{(estimated_total_cost_gbp || 0).toLocaleString()}
                </p>
              </div>
            </div>
            <p style={{ fontSize: 12, color: "var(--muted)", textAlign: "center" }}>Approximate cost based on cheapest available options.</p>
          </div>
        )}

        {/* ═══ SIMILAR DESTINATIONS ═══ */}
        {similarDests.length > 0 && (
          <div style={{ marginTop: 48 }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 24, marginBottom: 16 }}>You might also like</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              {similarDests.map(dest => (
                <div key={dest.id} className="card-hover" style={{ borderRadius: 16, overflow: "hidden", cursor: "pointer", boxShadow: "var(--shadow-card)" }}
                  onClick={() => { const p = new URLSearchParams(searchParams); navigate(`/itinerary/${dest.id}?${p}`); }}>
                  <div style={{ height: 120, position: "relative", overflow: "hidden" }}>
                    <img
                      src={getDestImage(dest.id)}
                      onError={e => { e.target.onerror = null; e.target.src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop'; }}
                      alt={cap(dest.name)}
                      style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                    />
                    <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 35%, rgba(26,26,46,0.7))" }} />
                    <div style={{ position: "absolute", bottom: 10, left: 12, right: 12 }}>
                      <p style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontStyle: "italic", color: "white", fontSize: 15, margin: 0 }}>{cap(dest.name)}</p>
                      <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 12, margin: 0 }}>{dest.country}</p>
                    </div>
                  </div>
                  <div style={{ padding: "10px 12px", background: "var(--surface)" }}>
                    <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 12, color: "var(--primary)", margin: 0 }}>
                      {Math.round((dest.similarity_score || 0) * 100)}% similar
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
