import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toTitleCase, unsplashImage, onImgError } from "../utils/helpers";

const STORAGE_KEY = "travelbuddy_saved_trips";

function loadTrips() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function removeTrip(id) {
  const next = loadTrips().filter((t) => t.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export default function MyTrips() {
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);

  useEffect(() => { setTrips(loadTrips()); }, []);

  const handleRemove = (id) => setTrips(removeTrip(id));

  if (trips.length === 0) {
    return (
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
        <div style={{
          width: 80, height: 80, borderRadius: 20,
          background: "var(--primary-light)", color: "var(--primary)",
          display: "flex", alignItems: "center", justifyContent: "center",
          margin: "0 auto 20px", fontSize: 36,
        }}>{"\u2708\uFE0F"}</div>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 30, fontWeight: 700, color: "var(--dark)", margin: "0 0 8px",
        }}>No trips saved yet</h1>
        <p style={{ color: "var(--muted)", fontSize: 15, margin: "0 0 24px" }}>
          Save a trip and it'll show up here next time you visit.
        </p>
        <button onClick={() => navigate("/dashboard")} style={{
          padding: "12px 28px", borderRadius: 10, border: 0, cursor: "pointer",
          background: "var(--accent)", color: "white", fontSize: 15, fontWeight: 600,
          fontFamily: "'DM Sans', sans-serif",
        }}>Plan your first trip</button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1120, margin: "0 auto", padding: "40px 24px 60px" }}>
      <h1 style={{
        fontFamily: "'Playfair Display', serif",
        fontSize: 30, fontWeight: 700, color: "var(--dark)", margin: "0 0 20px",
      }}>My Trips</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
        {trips.map((t) => (
          <div key={t.id || t.destination_id || t.name} className="card-hover" style={{
            borderRadius: 16, overflow: "hidden", background: "var(--surface)",
            boxShadow: "var(--shadow-card)",
          }}>
            <div style={{ height: 160, position: "relative" }}>
              <img
                src={t.image || unsplashImage(t.destination_id || t.name || "paris", 600)}
                onError={onImgError}
                alt={t.name}
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
              />
              <div style={{
                position: "absolute", inset: 0,
                background: "linear-gradient(transparent 40%, rgba(26,26,46,0.75))",
              }} />
              <div style={{ position: "absolute", bottom: 10, left: 14, right: 14 }}>
                <p style={{
                  margin: 0, color: "white",
                  fontFamily: "'Playfair Display', serif",
                  fontWeight: 700, fontSize: 18,
                }}>{toTitleCase(t.name || t.destination || "Your Trip")}</p>
                {t.country && (
                  <p style={{ margin: 0, color: "rgba(255,255,255,0.7)", fontSize: 12 }}>{t.country}</p>
                )}
              </div>
            </div>
            <div style={{ padding: 16 }}>
              {(t.start_date || t.dates?.start) && (
                <p style={{ fontSize: 13, color: "var(--muted)", margin: "0 0 6px" }}>
                  {t.start_date || t.dates?.start}
                  {(t.end_date || t.dates?.end) && ` \u2013 ${t.end_date || t.dates?.end}`}
                </p>
              )}
              {t.total_cost_gbp != null && (
                <p style={{
                  fontFamily: "'DM Mono', monospace", fontWeight: 700,
                  color: "var(--primary)", fontSize: 16, margin: 0,
                }}>{"\u00a3"}{t.total_cost_gbp}</p>
              )}
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button onClick={() => navigate(`/itinerary/${t.destination_id || t.id}`)} style={{
                  flex: 1, padding: "10px 0", borderRadius: 8, border: 0, cursor: "pointer",
                  background: "var(--accent)", color: "white", fontSize: 13, fontWeight: 600,
                  fontFamily: "'DM Sans', sans-serif",
                }}>View</button>
                <button onClick={() => handleRemove(t.id || t.destination_id || t.name)} style={{
                  padding: "10px 16px", borderRadius: 8, cursor: "pointer",
                  background: "var(--surface)", color: "var(--muted)",
                  border: "1px solid var(--border)", fontSize: 13, fontWeight: 500,
                  fontFamily: "'DM Sans', sans-serif",
                }}>Remove</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
