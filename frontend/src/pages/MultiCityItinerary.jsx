import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getMultiCityItinerary, saveItinerary } from "../services/api";
import DESTINATION_IMAGES from "../data/destinationImages";
import { toTitleCase as cap, FALLBACK_IMG } from "../utils/helpers";

const getDestImage = (id) => DESTINATION_IMAGES[id] || FALLBACK_IMG;

const getHotelImage = (name, city) =>
  `https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=300&fit=crop`;

const WEATHER_ICONS = {
  "01d": "\u2600\uFE0F", "01n": "\uD83C\uDF19", "02d": "\u26C5", "02n": "\u2601\uFE0F",
  "03d": "\u2601\uFE0F", "04d": "\u2601\uFE0F", "09d": "\uD83C\uDF27\uFE0F",
  "10d": "\uD83C\uDF26\uFE0F", "11d": "\u26C8\uFE0F", "13d": "\u2744\uFE0F", "50d": "\uD83C\uDF2B\uFE0F",
};

export default function MultiCityItinerary() {
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeCity, setActiveCity] = useState(0);
  const [activeSection, setActiveSection] = useState("overview"); // overview, hotels, flights

  useEffect(() => {
    async function load() {
      try {
        const destinations = searchParams.get("destinations")?.split(",") || [];
        const data = await getMultiCityItinerary(user, {
          destination_ids: destinations,
          departure_city: searchParams.get("departure") || "London",
          travel_dates: { start: searchParams.get("start") || "2026-04-15", end: searchParams.get("end") || "2026-04-22" },
          budget_level: searchParams.get("budget") || "medium",
          nationality: searchParams.get("nationality") || "GB",
        });
        setItinerary(data);
      } catch (err) { setError(err.message || "Failed to load itinerary"); }
      finally { setLoading(false); }
    }
    load();
  }, [searchParams, user]);

  const handleSave = async () => { setSaving(true); try { await saveItinerary(user, itinerary); setSaved(true); } catch (err) { console.error(err); } finally { setSaving(false); } };

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/></svg>
        </div>
        <p style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 700, color: "var(--dark)" }}>{"Building your multi-city trip\u2026"}</p>
      </div>
    </div>
  );

  if (error) return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "60px 24px" }}>
      <div style={{ background: "#FFF5F5", borderRadius: 16, padding: 40, textAlign: "center", borderLeft: "4px solid #E53E3E" }}>
        <p style={{ fontSize: 18, fontWeight: 700, color: "var(--dark)", margin: "0 0 8px" }}>{error}</p>
        <button onClick={() => navigate("/dashboard")} style={{ fontSize: 14, padding: "10px 24px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--surface)", cursor: "pointer" }}>Back to Dashboard</button>
      </div>
    </div>
  );

  const { route, total_dates, cities, cost_breakdown, estimated_total_cost_gbp } = itinerary;
  const city = cities[activeCity];

  /* Determine cheapest and fastest flights for the current city */
  const cityFlights = city.flights || [];
  const cheapestFlightIdx = cityFlights.length > 0 ? cityFlights.reduce((minI, f, i, arr) => (f.price_gbp < arr[minI].price_gbp ? i : minI), 0) : -1;
  const fastestFlightIdx = cityFlights.length > 0 ? cityFlights.reduce((minI, f, i, arr) => {
    const dur = (s) => { const m = (s || "").match(/(\d+)h\s*(\d+)?/); return m ? parseInt(m[1]) * 60 + parseInt(m[2] || 0) : 9999; };
    return dur(f.duration) < dur(arr[minI].duration) ? i : minI;
  }, 0) : -1;

  /* Determine best-value hotel */
  const cityHotels = city.hotels || [];
  const bestValueHotelIdx = cityHotels.length > 0 ? cityHotels.reduce((bestI, h, i, arr) => {
    const ratio = (h2) => (h2.rating || 3) / (h2.price_per_night_gbp || 1);
    return ratio(h) > ratio(arr[bestI]) ? i : bestI;
  }, 0) : -1;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>

      {/* ═══ HERO ═══ */}
      <div style={{ background: "#1A1A2E", padding: "24px 0 0", position: "relative" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px" }}>
          <button onClick={() => navigate("/dashboard")} style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", border: 0, background: "transparent", cursor: "pointer", marginBottom: 16 }}>{"\u2190"} Back</button>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div>
              <p className="label-uppercase" style={{ color: "#00A3A3", marginBottom: 8 }}>MULTI-CITY TRIP</p>
              <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 36, fontWeight: 700, color: "white", margin: 0 }}>
                {cities.map(c => cap(c.destination.name)).join(" \u2192 ")}
              </h1>
              <div style={{ display: "flex", gap: 20, color: "rgba(255,255,255,0.5)", fontSize: 14, marginTop: 8 }}>
                <span>{total_dates.start} {"\u2013"} {total_dates.end}</span>
                <span>{total_dates.duration_days} days</span>
                <span>{cities.length} cities</span>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 32, color: "#00A3A3", margin: 0 }}>{"\u00a3"}{estimated_total_cost_gbp?.toLocaleString()}</p>
              <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", margin: 0 }}>total estimated</p>
            </div>
          </div>

          {/* Route bar */}
          <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap", paddingBottom: 20 }}>
            {route.map((stop, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{
                  fontSize: 13, padding: "6px 14px", borderRadius: 8, fontWeight: 600,
                  background: (i === 0 || i === route.length - 1) ? "rgba(255,255,255,0.1)" : "#00A3A3",
                  color: "white",
                }}>{cap(stop)}</span>
                {i < route.length - 1 && <span style={{ color: "rgba(255,255,255,0.3)" }}>{"\u2192"}</span>}
              </div>
            ))}
          </div>

          {/* City tabs */}
          <div style={{ display: "flex", gap: 4, borderBottom: "2px solid rgba(255,255,255,0.1)" }}>
            {cities.map((c, i) => (
              <button key={i} onClick={() => { setActiveCity(i); setActiveSection("overview"); }}
                style={{
                  padding: "12px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer",
                  border: 0, background: "transparent", color: activeCity === i ? "white" : "rgba(255,255,255,0.4)",
                  borderBottom: activeCity === i ? "2px solid #00A3A3" : "2px solid transparent",
                  marginBottom: -2, fontFamily: "'DM Sans', sans-serif",
                }}>
                {cap(c.destination.name)}
                <span style={{ marginLeft: 8, fontSize: 11, opacity: 0.6 }}>{c.dates.duration_days}d</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ CITY CONTENT ═══ */}
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px 24px 60px" }}>

        {/* Section tabs */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          {[
            { id: "overview", label: "Overview" },
            { id: "hotels", label: `Hotels (${city.hotels?.length || 0})` },
            { id: "flights", label: "Flights" },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveSection(t.id)} style={{
              padding: "8px 18px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
              fontFamily: "'DM Sans', sans-serif",
              border: activeSection === t.id ? 0 : "1.5px solid var(--border)",
              background: activeSection === t.id ? "#00A3A3" : "var(--surface)",
              color: activeSection === t.id ? "white" : "var(--body)",
            }}>{t.label}</button>
          ))}
        </div>

        {/* ── Overview ── */}
        {activeSection === "overview" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* City hero card */}
            <div style={{ borderRadius: 16, overflow: "hidden", height: 200, position: "relative" }}>
              <img
                src={getDestImage(city.destination.id)}
                onError={e => { e.target.onerror = null; e.target.src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1000&h=400&fit=crop'; }}
                alt={cap(city.destination.name)}
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
              />
              <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 30%, rgba(26,26,46,0.75))" }} />
              <div style={{ position: "absolute", bottom: 20, left: 24, right: 24, display: "flex", justifyContent: "space-between", alignItems: "end" }}>
                <div>
                  <p style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "white", margin: 0 }}>{cap(city.destination.name)}, {city.destination.country}</p>
                  <p style={{ fontSize: 13, color: "rgba(255,255,255,0.6)", margin: "4px 0 0" }}>{city.dates.start} {"\u2013"} {city.dates.end} &middot; {city.dates.duration_days} days &middot; From {city.flight_from}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 22, color: "#00A3A3", margin: 0 }}>{"\u00a3"}{city.cost_breakdown.total}</p>
                  <p style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", margin: 0 }}>this city</p>
                </div>
              </div>
            </div>

            {/* Visa */}
            {city.visa_info && city.visa_info.visa_required && (
              <div style={{ borderRadius: 12, padding: 16, background: "var(--accent-light)", borderLeft: "4px solid var(--warning)", display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>Visa: {city.visa_info.requirement}</span>
                {city.visa_info.cost_gbp > 0 && <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, color: "var(--dark)" }}>{"\u00a3"}{city.visa_info.cost_gbp}</span>}
              </div>
            )}

            {/* Weather */}
            {city.weather?.daily_forecast && (
              <div style={{ background: "var(--surface)", borderRadius: 16, padding: 20, boxShadow: "var(--shadow-card)" }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--dark)", margin: "0 0 12px" }}>Weather</h3>
                <div className="overflow-x-auto" style={{ display: "flex", gap: 8 }}>
                  {city.weather.daily_forecast.map((d, i) => (
                    <div key={i} style={{ flexShrink: 0, textAlign: "center", padding: "8px 12px", borderRadius: 10, background: "var(--bg)", minWidth: 58 }}>
                      <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600 }}>{d.day?.slice(0, 3)}</div>
                      <div style={{ fontSize: 20, margin: "2px 0" }}>{WEATHER_ICONS[d.icon] || "\u26C5"}</div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 13, color: "var(--dark)" }}>{d.temp_high_c}{"\u00b0"}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Activities */}
            <div style={{ background: "var(--surface)", borderRadius: 16, padding: 20, boxShadow: "var(--shadow-card)" }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--dark)", margin: "0 0 12px" }}>Things to Do</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(city.activities || []).map((a, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: 10, borderRadius: 10, border: "1px solid var(--border)" }}>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 600, color: "var(--dark)", fontSize: 14, margin: 0 }}>{a.name}</p>
                      <p style={{ fontSize: 12, color: "var(--muted)", margin: "2px 0 0" }}>{a.category} &middot; {a.address}</p>
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--warning)" }}>{"\u2605"} {a.rating}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Per-city cost */}
            <div style={{ background: "var(--surface)", borderRadius: 16, padding: 20, boxShadow: "var(--shadow-card)" }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--dark)", margin: "0 0 12px" }}>Cost for {cap(city.destination.name)}</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, textAlign: "center" }}>
                {[
                  ["Flight", city.cost_breakdown.flights],
                  ["Hotel", city.cost_breakdown.accommodation],
                  ["Food", city.cost_breakdown.food],
                  ["Activities", city.cost_breakdown.activities],
                  ["Total", city.cost_breakdown.total],
                ].map(([label, val], i) => (
                  <div key={i}>
                    <p className="label-uppercase" style={{ marginBottom: 4 }}>{label}</p>
                    <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: i === 4 ? 20 : 16, color: i === 4 ? "#00A3A3" : "var(--dark)", margin: 0 }}>{"\u00a3"}{val}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Hotels ── */}
        {activeSection === "hotels" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {(city.hotels || []).map((h, i) => (
              <div key={i} style={{ background: "var(--surface)", borderRadius: 16, overflow: "hidden", boxShadow: "var(--shadow-card)", maxWidth: 340, border: "1px solid var(--border)" }}>
                {/* Hotel image */}
                <div style={{ height: 200, position: "relative", overflow: "hidden" }}>
                  <img
                    src={h.image_url || getHotelImage(h.name, city.destination.name)}
                    onError={e => { e.target.onerror = null; e.target.src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'; }}
                    alt={h.name}
                    style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                  />
                  <div style={{ position: "absolute", top: 10, left: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {i === bestValueHotelIdx && (
                      <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "#15803D", color: "white", fontWeight: 700 }}>Best value</span>
                    )}
                  </div>
                </div>

                {/* Hotel details */}
                <div style={{ padding: 16 }}>
                  {/* Name */}
                  <h3 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 17, color: "var(--dark)", margin: "0 0 6px" }}>{h.name}</h3>

                  {/* Star dots */}
                  <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 8 }}>
                    {Array.from({ length: h.stars || 3 }).map((_, j) => (
                      <span key={j} style={{ width: 7, height: 7, borderRadius: "50%", background: "#00A3A3", display: "inline-block" }} />
                    ))}
                  </div>

                  {/* Review score badge */}
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                    <div style={{
                      width: 34, height: 34, borderRadius: "8px 8px 8px 0", background: "#00A3A3", color: "white",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 13,
                    }}>
                      {h.rating}
                    </div>
                    <div>
                      <p style={{ fontSize: 12, fontWeight: 700, color: "var(--dark)", margin: 0 }}>
                        {h.rating >= 4.5 ? "Exceptional" : h.rating >= 4 ? "Excellent" : h.rating >= 3.5 ? "Very Good" : "Good"}
                      </p>
                      {h.review_count && <p style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>{h.review_count?.toLocaleString()} reviews</p>}
                    </div>
                  </div>

                  {/* Tags */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 10 }}>
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
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                    {(h.amenities || []).slice(0, 4).map(a => (
                      <span key={a} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 6, background: "var(--bg)", color: "var(--body)", fontWeight: 500 }}>{a}</span>
                    ))}
                  </div>

                  {/* Price */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", marginBottom: 12 }}>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 22, color: "#00A3A3" }}>{"\u00a3"}{h.price_per_night_gbp}</span>
                      <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 4 }}>/night</span>
                    </div>
                  </div>

                  {/* Book button */}
                  <a href={h.booking_url || h.search_url || `https://www.booking.com/searchresults.html?ss=${encodeURIComponent((h.name || '') + ' ' + city.destination.name)}`}
                    target="_blank" rel="noopener noreferrer"
                    style={{
                      display: "block", width: "100%", padding: "10px 0", borderRadius: 8,
                      background: "#FF6B2B", color: "white", textDecoration: "none", fontWeight: 700,
                      fontSize: 13, textAlign: "center", fontFamily: "'DM Sans', sans-serif",
                      boxSizing: "border-box",
                    }}>
                    Book on Booking.com
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Flights ── */}
        {activeSection === "flights" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <p style={{ fontSize: 14, color: "var(--muted)", margin: "0 0 8px" }}>{city.flight_from} {"\u2192"} {cap(city.destination.name)}</p>
            {(city.flights || []).map((f, i) => {
              const isCheapest = i === cheapestFlightIdx;
              const isFastest = i === fastestFlightIdx && i !== cheapestFlightIdx;
              return (
                <div key={i} style={{
                  background: "var(--surface)", borderRadius: 16, padding: 20, boxShadow: "var(--shadow-card)",
                  border: isCheapest ? "2px solid #15803D" : isFastest ? "2px solid #00A3A3" : "1px solid var(--border)",
                  position: "relative",
                }}>
                  {/* Badges */}
                  <div style={{ position: "absolute", top: -1, right: 16, display: "flex", gap: 6 }}>
                    {isCheapest && (
                      <span style={{ fontSize: 11, padding: "4px 12px", borderRadius: "0 0 8px 8px", background: "#15803D", color: "white", fontWeight: 700 }}>Cheapest</span>
                    )}
                    {isFastest && (
                      <span style={{ fontSize: 11, padding: "4px 12px", borderRadius: "0 0 8px 8px", background: "#00A3A3", color: "white", fontWeight: 700 }}>Fastest</span>
                    )}
                  </div>

                  {/* Top row: airline + price */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <div style={{ width: 40, height: 40, borderRadius: 8, background: "#00A3A3", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700 }}>
                        {(f.airline_code || "").toUpperCase()}
                      </div>
                      <div>
                        <p style={{ fontWeight: 700, color: "var(--dark)", fontSize: 14, margin: 0 }}>{f.airline}</p>
                        <p style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>{f.flight_number}</p>
                      </div>
                    </div>
                    <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 22, color: "#00A3A3", margin: 0 }}>{"\u00a3"}{f.price_gbp}</p>
                  </div>

                  {/* Route visual */}
                  <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 12 }}>
                    <div style={{ textAlign: "center" }}>
                      <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 20, color: "var(--dark)", margin: 0 }}>{f.departure?.time}</p>
                      <p style={{ fontSize: 11, color: "var(--muted)", margin: 0, fontWeight: 600 }}>{f.departure?.airport}</p>
                    </div>
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <p style={{ fontSize: 11, color: "var(--muted)", margin: "0 0 2px", fontWeight: 600 }}>{f.duration}</p>
                      <div style={{ display: "flex", alignItems: "center", width: "100%", gap: 4 }}>
                        <div style={{ flex: 1, height: 1, borderTop: "2px dashed var(--border)" }} />
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#00A3A3" style={{ flexShrink: 0 }}><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>
                        <div style={{ flex: 1, height: 1, borderTop: "2px dashed var(--border)" }} />
                      </div>
                      <p style={{ fontSize: 11, margin: "2px 0 0", fontWeight: 600,
                        color: f.stops === 0 ? "#15803D" : "#D97706",
                      }}>
                        {f.stops === 0 ? "Direct" : `${f.stops} stop`}
                      </p>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 20, color: "var(--dark)", margin: 0 }}>{f.arrival?.time}</p>
                      <p style={{ fontSize: 11, color: "var(--muted)", margin: 0, fontWeight: 600 }}>{f.arrival?.airport}</p>
                    </div>
                  </div>

                  {/* Booking buttons */}
                  <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                    <a href={f.google_flights_url || `https://www.google.com/travel/flights?q=Flights+from+${f.departure?.airport}+to+${f.arrival?.airport}`}
                      target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 13, padding: "8px 18px", borderRadius: 8, background: "#00A3A3", color: "white", textDecoration: "none", fontWeight: 600 }}>Google Flights</a>
                    <a href={f.skyscanner_url || `https://www.skyscanner.net/transport/flights/${(f.departure?.airport || "").toLowerCase()}/${(f.arrival?.airport || "").toLowerCase()}/`}
                      target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 13, padding: "8px 18px", borderRadius: 8, background: "#FF6B2B", color: "white", textDecoration: "none", fontWeight: 600 }}>Skyscanner</a>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* City navigation */}
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
          <button onClick={() => { setActiveCity(c => c - 1); setActiveSection("overview"); }} disabled={activeCity === 0}
            style={{ fontSize: 14, fontWeight: 600, color: activeCity === 0 ? "transparent" : "var(--body)", border: 0, background: "transparent", cursor: "pointer" }}>
            {"\u2190"} {activeCity > 0 ? cap(cities[activeCity - 1].destination.name) : ""}
          </button>
          <button onClick={() => { setActiveCity(c => c + 1); setActiveSection("overview"); }} disabled={activeCity === cities.length - 1}
            style={{ fontSize: 14, fontWeight: 600, color: activeCity === cities.length - 1 ? "transparent" : "#00A3A3", border: 0, background: "transparent", cursor: "pointer" }}>
            {activeCity < cities.length - 1 ? cap(cities[activeCity + 1].destination.name) : ""} {"\u2192"}
          </button>
        </div>

        {/* ═══ GRAND TOTAL ═══ */}
        <div style={{ background: "var(--surface)", borderRadius: 16, overflow: "hidden", marginTop: 32, boxShadow: "var(--shadow-card)", border: "1px solid var(--border)" }}>
          <div style={{ padding: "20px 24px" }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 22, margin: "0 0 16px" }}>Total Trip Cost</h2>
            {[
              ["All Flights", `${cities.length} legs + return`, cost_breakdown.flights],
              ["Accommodation", `${total_dates.duration_days} nights total`, cost_breakdown.accommodation],
              ["Food & Dining", "", cost_breakdown.food],
              ["Activities", "", cost_breakdown.activities],
              ...(cost_breakdown.visa > 0 ? [["Visa Fees", "", cost_breakdown.visa]] : []),
            ].map(([label, sub, val], i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid var(--border)" }}>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark)", margin: 0 }}>{label}</p>
                  {sub && <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{sub}</p>}
                </div>
                <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 15, color: "var(--dark)", margin: 0 }}>{"\u00a3"}{val?.toLocaleString()}</p>
              </div>
            ))}
          </div>
          <div style={{ padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#1A1A2E" }}>
            <div>
              <p style={{ fontFamily: "'Playfair Display', serif", fontSize: 18, fontWeight: 700, color: "white", margin: 0 }}>Grand Total</p>
              <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", margin: "2px 0 0" }}>per person</p>
            </div>
            <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 28, color: "#00A3A3", margin: 0 }}>{"\u00a3"}{estimated_total_cost_gbp?.toLocaleString()}</p>
          </div>
        </div>
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 8, textAlign: "center" }}>Approximate cost for 1 person across {cities.length} cities.</p>

        {/* Save */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 20 }}>
          <button onClick={handleSave} disabled={saving || saved} style={{
            padding: "12px 28px", borderRadius: 8, border: 0, cursor: "pointer", fontSize: 14, fontWeight: 600,
            fontFamily: "'DM Sans', sans-serif",
            background: saved ? "var(--primary-light)" : "#FF6B2B",
            color: saved ? "var(--primary-dark)" : "white",
          }}>
            {saved ? "\u2713 Saved!" : saving ? "Saving\u2026" : "Save Multi-City Trip"}
          </button>
        </div>
      </div>
    </div>
  );
}
