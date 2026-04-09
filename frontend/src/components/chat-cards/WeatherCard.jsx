export default function WeatherCard({ data }) {
  const { city, month, avg_temp_c, conditions, humidity, rainfall, what_to_pack = [] } = data;

  const condIcons = {
    sunny: "☀️", hot: "🔥", warm: "🌤️", mild: "⛅", cool: "🌥️",
    cold: "❄️", rainy: "🌧️", monsoon: "🌊", snowy: "🌨️",
    humid: "💧", dry: "🏜️", tropical: "🌴", cloudy: "☁️",
  };
  const icon = condIcons[conditions?.toLowerCase()] || "🌤️";

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌡️</span>
            <div>
              <h3 className="text-white font-bold text-lg m-0">{city || "Weather"}</h3>
              {month && <p className="text-cyan-200 text-sm m-0">{month}</p>}
            </div>
          </div>
          <div className="text-right">
            <span className="text-3xl">{icon}</span>
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-3 gap-3 mb-4">
          {avg_temp_c != null && (
            <div className="bg-cyan-50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-cyan-600 m-0">{avg_temp_c}°</p>
              <p className="text-xs text-gray-500 m-0">Avg Temp</p>
            </div>
          )}
          {humidity && (
            <div className="bg-blue-50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-blue-600 m-0">{humidity}</p>
              <p className="text-xs text-gray-500 m-0">Humidity</p>
            </div>
          )}
          {rainfall && (
            <div className="bg-indigo-50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-indigo-600 m-0">{rainfall}</p>
              <p className="text-xs text-gray-500 m-0">Rainfall</p>
            </div>
          )}
        </div>

        {conditions && (
          <p className="text-sm text-gray-600 m-0 mb-3">
            <span className="font-medium">Conditions:</span> {conditions}
          </p>
        )}

        {what_to_pack.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider m-0 mb-2">What to Pack</p>
            <div className="flex flex-wrap gap-2">
              {what_to_pack.map((item, i) => (
                <span key={i} className="text-xs bg-cyan-50 text-cyan-700 px-3 py-1 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
