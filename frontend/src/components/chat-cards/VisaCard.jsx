export default function VisaCard({ data }) {
  const { country, visa_type, duration, cost, documents = [], apply_url, notes } = data;

  const typeColors = {
    "visa-free": { bg: "#ECFDF5", text: "#059669", icon: "✅" },
    "visa on arrival": { bg: "#FFF7ED", text: "#EA580C", icon: "🛬" },
    "e-visa": { bg: "#EFF6FF", text: "#2563EB", icon: "💻" },
    "visa required": { bg: "#FEF2F2", text: "#DC2626", icon: "📋" },
  };

  const style = typeColors[visa_type?.toLowerCase()] || typeColors["visa required"];

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ background: style.bg }}>
              {style.icon}
            </div>
            <div>
              <h3 className="font-bold text-gray-800 m-0">{country}</h3>
              <span className="text-sm font-medium px-2 py-0.5 rounded-full" style={{ background: style.bg, color: style.text }}>
                {visa_type}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          {duration && (
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-xs text-gray-400 m-0">Duration</p>
              <p className="text-sm font-semibold text-gray-800 m-0">{duration}</p>
            </div>
          )}
          {cost && (
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-xs text-gray-400 m-0">Cost</p>
              <p className="text-sm font-semibold text-gray-800 m-0">{cost}</p>
            </div>
          )}
        </div>

        {documents.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider m-0 mb-2">Documents Needed</p>
            <div className="space-y-1">
              {documents.map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="text-gray-300">•</span> {d}
                </div>
              ))}
            </div>
          </div>
        )}

        {notes && <p className="text-sm text-gray-500 m-0 mb-4 italic">{notes}</p>}

        {apply_url && (
          <a href={apply_url} target="_blank" rel="noopener noreferrer"
            className="block w-full text-center text-sm font-semibold py-2.5 rounded-xl transition no-underline"
            style={{ background: style.bg, color: style.text }}>
            Apply Now →
          </a>
        )}
      </div>
    </div>
  );
}
