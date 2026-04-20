function parseDurationMins(d) {
  if (!d) return 9999;
  // Handles "2h 15m", "PT2H15M", "1h30" and similar
  const m = d.match(/(\d+)\s*h(?:\s*(\d+))?/i)
    || d.match(/PT(\d+)H(?:(\d+)M)?/i);
  if (!m) return 9999;
  return parseInt(m[1], 10) * 60 + parseInt(m[2] || 0, 10);
}

function googleFlightsUrl(f) {
  const dep = f.from || f.departure?.airport || f.departure?.city || "";
  const dest = f.to || f.arrival?.airport || f.arrival?.city || "";
  const date = f.departure?.date || f.date || "";
  const query = `flights from ${dep} to ${dest}${date ? ` on ${date}` : ""}`;
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(query)}`;
}

function skyscannerUrl(f) {
  const origin = (f.from || f.departure?.airport || "lon").toLowerCase();
  const dest = (f.to || f.arrival?.airport || "").toLowerCase();
  return `https://www.skyscanner.net/transport/flights/${origin}/${dest}/`;
}

export default function FlightCard({ data }) {
  const { flights = [] } = data;

  // Identify cheapest + fastest (fastest only if it's not the same as cheapest)
  const priceOf = (f) => f.price_gbp ?? f.price ?? Infinity;
  let cheapestIdx = -1;
  let fastestIdx = -1;
  if (flights.length) {
    cheapestIdx = flights.reduce((min, f, i, arr) => priceOf(f) < priceOf(arr[min]) ? i : min, 0);
    fastestIdx = flights.reduce((min, f, i, arr) => parseDurationMins(f.duration) < parseDurationMins(arr[min].duration) ? i : min, 0);
    if (fastestIdx === cheapestIdx) fastestIdx = -1;
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)" }}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{"\u2708\uFE0F"}</span>
          <h3 className="text-white font-bold text-lg m-0">Flight Options</h3>
        </div>
      </div>

      <div className="p-5 space-y-3">
        {flights.map((f, i) => {
          const depTime = f.departure_time || f.departure?.time;
          const arrTime = f.arrival_time || f.arrival?.time;
          const fromAirport = f.from || f.departure?.airport;
          const toAirport = f.to || f.arrival?.airport;
          const price = f.price_gbp ?? f.price;
          const isCheapest = i === cheapestIdx;
          const isFastest = i === fastestIdx;
          return (
            <div key={i} className="border border-gray-100 rounded-xl p-4 transition"
              style={{
                borderColor: isCheapest ? "#15803D" : isFastest ? "#1a73e8" : undefined,
                borderWidth: (isCheapest || isFastest) ? 2 : 1,
              }}>
              {/* Badge row */}
              {(isCheapest || isFastest) && (
                <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
                  {isCheapest && (
                    <span style={{
                      fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 999,
                      background: "#DCFCE7", color: "#15803D",
                    }}>{"\uD83D\uDC9A"} Best price</span>
                  )}
                  {isFastest && (
                    <span style={{
                      fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 999,
                      background: "#DBEAFE", color: "#1a73e8",
                    }}>{"\u26A1"} Fastest</span>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-800 text-sm">{f.airline} {f.flight_number && <span className="text-gray-400 font-normal">&middot; {f.flight_number}</span>}</span>
                {price != null && <span className="text-lg font-bold text-blue-600">{"\u00a3"}{price}</span>}
              </div>

              <div className="flex items-center gap-3 mb-3">
                <div className="text-center">
                  <p className="font-semibold text-gray-800 m-0">{depTime}</p>
                  <p className="text-xs text-gray-400 m-0">{fromAirport}</p>
                </div>
                <div className="flex-1 flex items-center gap-1">
                  <div className="h-px flex-1 bg-gray-200" />
                  <div className="text-center px-2">
                    <p className="text-xs text-gray-400 m-0">{f.duration}</p>
                    <p className="text-xs text-gray-400 m-0">{f.stops === 0 ? "Direct" : (f.stops_label || `${f.stops} stop${f.stops > 1 ? "s" : ""}`)}</p>
                  </div>
                  <div className="h-px flex-1 bg-gray-200" />
                </div>
                <div className="text-center">
                  <p className="font-semibold text-gray-800 m-0">{arrTime}</p>
                  <p className="text-xs text-gray-400 m-0">{toAirport}</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                {(f.class || f.cabin_class) && (
                  <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium">{f.class || f.cabin_class}</span>
                )}
                <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                  <a href={googleFlightsUrl(f)} target="_blank" rel="noopener noreferrer"
                    style={{
                      background: "#1a73e8", color: "white", padding: "8px 16px",
                      borderRadius: 8, fontWeight: 600, fontSize: 13, textDecoration: "none",
                      display: "inline-flex", alignItems: "center", gap: 6,
                    }}>
                    {"\uD83D\uDD35"} Google Flights
                  </a>
                  <a href={skyscannerUrl(f)} target="_blank" rel="noopener noreferrer"
                    style={{
                      background: "#FF6B35", color: "white", padding: "8px 16px",
                      borderRadius: 8, fontWeight: 600, fontSize: 13, textDecoration: "none",
                      display: "inline-flex", alignItems: "center", gap: 6,
                    }}>
                    {"\uD83D\uDFE0"} Skyscanner
                  </a>
                </div>
              </div>
            </div>
          );
        })}

        {flights.length > 0 && (
          <p style={{
            margin: "6px 2px 0", fontSize: 11, color: "#9CA3AF", lineHeight: 1.5,
          }}>
            Prices are estimates. Click to check live prices on Google Flights or Skyscanner.
          </p>
        )}
      </div>
    </div>
  );
}
