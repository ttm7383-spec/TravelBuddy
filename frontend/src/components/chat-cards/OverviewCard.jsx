export default function OverviewCard({ data }) {
  const { city, country, description, vibes = [], highlights = [], best_time, language, currency } = data;

  const vibeColors = {
    culture: "#8B5CF6", nightlife: "#EC4899", food: "#F59E0B", adventure: "#10B981",
    relaxation: "#06B6D4", shopping: "#F97316", nature: "#22C55E", history: "#6366F1",
    romantic: "#E11D48", family: "#3B82F6", budget: "#14B8A6", luxury: "#A855F7",
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
      </div>
    </div>
  );
}
