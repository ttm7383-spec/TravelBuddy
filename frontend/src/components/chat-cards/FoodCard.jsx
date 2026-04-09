export default function FoodCard({ data }) {
  const { name, cuisine, must_try, price_range, area, description, vibe } = data;

  const priceMap = { "$": "Budget", "$$": "Mid-range", "$$$": "Fine dining", "$$$$": "Premium" };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="p-5">
        <div className="flex items-start gap-3 mb-3">
          <div className="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center text-2xl">🍽️</div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-gray-800 m-0">{name}</h3>
              {price_range && (
                <span className="text-sm font-semibold text-orange-500">{price_range}</span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1">
              {cuisine && <span className="text-xs bg-orange-50 text-orange-600 px-2 py-0.5 rounded-full font-medium">{cuisine}</span>}
              {area && <span className="text-xs text-gray-400">{area}</span>}
            </div>
          </div>
        </div>

        {description && <p className="text-sm text-gray-600 m-0 mb-3">{description}</p>}

        {must_try && (
          <div className="bg-amber-50 rounded-xl p-3 flex items-start gap-2">
            <span className="text-lg">⭐</span>
            <div>
              <p className="text-xs font-semibold text-amber-700 m-0">Must Try</p>
              <p className="text-sm text-amber-800 m-0">{must_try}</p>
            </div>
          </div>
        )}

        {vibe && (
          <p className="text-xs text-gray-400 mt-3 m-0 italic">Vibe: {vibe}</p>
        )}
      </div>
    </div>
  );
}
