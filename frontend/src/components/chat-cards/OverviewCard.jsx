import { useNavigate } from "react-router-dom";

export default function OverviewCard({ data }) {
  const {
    city, country, description, vibes = [], highlights = [], best_time,
    language, currency, suggested_cities = [], budget_recommendation,
  } = data;
  const navigate = useNavigate();

  const vibeColors = {
    culture: "#8B5CF6", nightlife: "#EC4899", food: "#F59E0B", adventure: "#10B981",
    relaxation: "#06B6D4", shopping: "#F97316", nature: "#22C55E", history: "#6366F1",
    romantic: "#E11D48", family: "#3B82F6", budget: "#14B8A6", luxury: "#A855F7",
  };

  const handlePlanCity = (cityName) => {
    navigate(`/chat?q=${encodeURIComponent(`plan a trip to ${cityName}`)}`);
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      {/* Header */}
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #0066FF 0%, #4F46E5 100%)" }}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">🌍</span>
          <div>
            <h3 className="text-white font-bold text-lg m-0">{city}</h3>
            <p className="text-blue-200 text-sm m-0">{country}</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Description */}
        <p className="text-gray-600 text-sm leading-relaxed m-0">{description}</p>

        {/* Vibe scores */}
        {vibes.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider m-0 mb-2">Vibes</p>
            <div className="flex flex-wrap gap-2">
              {vibes.map((v, i) => (
                <span key={i} className="px-3 py-1 rounded-full text-xs font-medium text-white"
                  style={{ background: vibeColors[v.name?.toLowerCase()] || "#6B7280" }}>
                  {v.name} {v.score && `${v.score}/10`}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Quick info */}
        <div className="grid grid-cols-3 gap-3">
          {best_time && (
            <div className="bg-blue-50 rounded-xl p-3 text-center">
              <p className="text-lg m-0">📅</p>
              <p className="text-xs text-gray-500 m-0">Best Time</p>
              <p className="text-sm font-semibold text-gray-800 m-0">{best_time}</p>
            </div>
          )}
          {language && (
            <div className="bg-purple-50 rounded-xl p-3 text-center">
              <p className="text-lg m-0">🗣️</p>
              <p className="text-xs text-gray-500 m-0">Language</p>
              <p className="text-sm font-semibold text-gray-800 m-0">{language}</p>
            </div>
          )}
          {currency && (
            <div className="bg-green-50 rounded-xl p-3 text-center">
              <p className="text-lg m-0">💰</p>
              <p className="text-xs text-gray-500 m-0">Currency</p>
              <p className="text-sm font-semibold text-gray-800 m-0">{currency}</p>
            </div>
          )}
        </div>

        {/* Highlights */}
        {highlights.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider m-0 mb-2">Highlights</p>
            <div className="space-y-1">
              {highlights.map((h, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-blue-500">✦</span> {h}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested cities (country-level overviews) */}
        {suggested_cities.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider m-0 mb-2">
              Cities to visit in {country || city}
            </p>
            <div
              style={{
                display: "flex", gap: 12, overflowX: "auto",
                paddingBottom: 8, scrollSnapType: "x mandatory",
              }}
            >
              {suggested_cities.map((c, i) => (
                <div key={i}
                  style={{
                    minWidth: 240, maxWidth: 260, flexShrink: 0,
                    background: "#FFFFFF",
                    borderLeft: "4px solid #14B8A6",
                    borderTop: "1px solid #E5E7EB",
                    borderRight: "1px solid #E5E7EB",
                    borderBottom: "1px solid #E5E7EB",
                    borderRadius: 10, padding: 14,
                    scrollSnapAlign: "start",
                    display: "flex", flexDirection: "column", gap: 8,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 8 }}>
                    <h4 style={{ fontWeight: 700, fontSize: 15, color: "#111827", margin: 0 }}>{c.name}</h4>
                    {typeof c.budget_per_day === "number" && (
                      <span
                        style={{
                          color: "#14B8A6", fontWeight: 700, fontSize: 14,
                          fontFamily: "'DM Mono', monospace",
                        }}
                      >
                        £{c.budget_per_day}/day
                      </span>
                    )}
                  </div>
                  {c.why && (
                    <p style={{ fontSize: 12, color: "#4B5563", lineHeight: 1.5, margin: 0 }}>{c.why}</p>
                  )}
                  {c.highlight && (
                    <p style={{ fontSize: 11, color: "#6B7280", lineHeight: 1.5, margin: 0, fontStyle: "italic" }}>
                      {c.highlight}
                    </p>
                  )}
                  {Array.isArray(c.best_for) && c.best_for.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {c.best_for.map((tag, j) => (
                        <span key={j}
                          style={{
                            fontSize: 10, padding: "2px 8px", borderRadius: 6,
                            background: "#F0FDFA", color: "#0F766E", fontWeight: 500,
                          }}
                        >{tag}</span>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => handlePlanCity(c.name)}
                    style={{
                      marginTop: "auto", padding: "8px 12px", borderRadius: 8,
                      border: 0, background: "#14B8A6", color: "white",
                      fontSize: 12, fontWeight: 600, cursor: "pointer",
                      fontFamily: "'DM Sans', sans-serif",
                    }}
                  >
                    Plan trip to {c.name}
                  </button>
                </div>
              ))}
            </div>
            {budget_recommendation && (
              <p
                style={{
                  marginTop: 10, fontSize: 12, color: "#4B5563",
                  background: "#F0FDFA", borderLeft: "3px solid #14B8A6",
                  padding: "8px 12px", borderRadius: 6,
                }}
              >
                {budget_recommendation}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
