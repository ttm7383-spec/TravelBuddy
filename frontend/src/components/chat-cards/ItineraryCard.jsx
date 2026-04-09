export default function ItineraryCard({ data }) {
  const { city, days = [], total_cost } = data;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #10B981 0%, #059669 100%)" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🗓️</span>
            <div>
              <h3 className="text-white font-bold text-lg m-0">{city || "Itinerary"}</h3>
              <p className="text-emerald-200 text-sm m-0">{days.length} day{days.length !== 1 ? "s" : ""} planned</p>
            </div>
          </div>
          {total_cost && (
            <span className="bg-white/20 text-white text-sm font-semibold px-3 py-1 rounded-full">
              ~£{total_cost}
            </span>
          )}
        </div>
      </div>

      <div className="p-5">
        <div className="space-y-4">
          {days.map((day, i) => (
            <div key={i} className="relative pl-8">
              {/* Timeline line */}
              {i < days.length - 1 && (
                <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-emerald-100" />
              )}
              {/* Timeline dot */}
              <div className="absolute left-1 top-1 w-5 h-5 rounded-full bg-emerald-500 text-white text-xs flex items-center justify-center font-bold">
                {i + 1}
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-800 text-sm m-0">
                    {day.title || `Day ${day.day || i + 1}`}
                  </h4>
                  {day.cost && (
                    <span className="text-xs text-emerald-600 font-medium bg-emerald-50 px-2 py-1 rounded-full">
                      £{day.cost}
                    </span>
                  )}
                </div>
                <div className="space-y-1.5">
                  {(day.activities || []).map((act, j) => (
                    <div key={j} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-gray-400 mt-0.5">
                        {act.time ? `${act.time}` : "•"}
                      </span>
                      <span>{typeof act === "string" ? act : act.activity || act.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
