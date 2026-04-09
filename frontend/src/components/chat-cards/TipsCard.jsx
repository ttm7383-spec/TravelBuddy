export default function TipsCard({ data }) {
  const { city, categories = [] } = data;

  const catIcons = {
    safety: "🛡️", transport: "🚇", money: "💰", culture: "🎭",
    food: "🍜", language: "🗣️", packing: "🧳", health: "🏥",
    etiquette: "🤝", general: "💡", nightlife: "🌃", shopping: "🛍️",
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)" }}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">💡</span>
          <h3 className="text-white font-bold text-lg m-0">{city ? `${city} Tips` : "Local Tips"}</h3>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {categories.map((cat, i) => (
          <div key={i}>
            <div className="flex items-center gap-2 mb-2">
              <span>{catIcons[cat.name?.toLowerCase()] || "💡"}</span>
              <h4 className="font-semibold text-gray-800 text-sm m-0 capitalize">{cat.name}</h4>
            </div>
            <div className="space-y-1.5 pl-6">
              {(cat.tips || []).map((tip, j) => (
                <div key={j} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-purple-400 mt-0.5 shrink-0">→</span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
