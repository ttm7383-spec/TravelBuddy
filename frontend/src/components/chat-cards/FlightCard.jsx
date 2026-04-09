export default function FlightCard({ data }) {
  const { flights = [] } = data;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)" }}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">✈️</span>
          <h3 className="text-white font-bold text-lg m-0">Flight Options</h3>
        </div>
      </div>

      <div className="p-5 space-y-3">
        {flights.map((f, i) => (
          <div key={i} className="border border-gray-100 rounded-xl p-4 hover:border-blue-200 transition">
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold text-gray-800 text-sm">{f.airline}</span>
              <span className="text-lg font-bold text-blue-600">£{f.price}</span>
            </div>

            <div className="flex items-center gap-3 mb-2">
              <div className="text-center">
                <p className="font-semibold text-gray-800 m-0">{f.departure_time}</p>
                <p className="text-xs text-gray-400 m-0">{f.from}</p>
              </div>
              <div className="flex-1 flex items-center gap-1">
                <div className="h-px flex-1 bg-gray-200" />
                <div className="text-center px-2">
                  <p className="text-xs text-gray-400 m-0">{f.duration}</p>
                  <p className="text-xs text-gray-400 m-0">{f.stops === 0 ? "Direct" : `${f.stops} stop${f.stops > 1 ? "s" : ""}`}</p>
                </div>
                <div className="h-px flex-1 bg-gray-200" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-gray-800 m-0">{f.arrival_time}</p>
                <p className="text-xs text-gray-400 m-0">{f.to}</p>
              </div>
            </div>

            {f.class && (
              <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium">{f.class}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
