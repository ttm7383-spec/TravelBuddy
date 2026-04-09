export default function BudgetCard({ data }) {
  const { city, days, currency = "GBP", total, breakdown = [] } = data;

  const maxVal = Math.max(...breakdown.map(b => b.amount || 0), 1);

  const catColors = {
    accommodation: "#6366F1", flights: "#3B82F6", food: "#F59E0B",
    transport: "#10B981", activities: "#EC4899", shopping: "#F97316",
    visa: "#8B5CF6", insurance: "#06B6D4", other: "#6B7280",
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-5 py-4" style={{ background: "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">💷</span>
            <div>
              <h3 className="text-white font-bold text-lg m-0">{city ? `${city} Budget` : "Budget Breakdown"}</h3>
              {days && <p className="text-amber-200 text-sm m-0">{days} days</p>}
            </div>
          </div>
          {total && (
            <div className="text-right">
              <p className="text-2xl font-bold text-white m-0">£{total}</p>
              <p className="text-amber-200 text-xs m-0">total estimate</p>
            </div>
          )}
        </div>
      </div>

      <div className="p-5 space-y-3">
        {breakdown.map((item, i) => {
          const pct = Math.round((item.amount / maxVal) * 100);
          const color = catColors[item.category?.toLowerCase()] || "#6B7280";
          return (
            <div key={i}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700 capitalize">{item.category}</span>
                <span className="text-sm font-semibold text-gray-800">£{item.amount}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
              </div>
              {item.note && <p className="text-xs text-gray-400 mt-0.5 m-0">{item.note}</p>}
            </div>
          );
        })}

        {total && days && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
            <span className="text-sm text-gray-500">Daily average</span>
            <span className="text-sm font-bold text-amber-600">~£{Math.round(total / days)}/day</span>
          </div>
        )}
      </div>
    </div>
  );
}
