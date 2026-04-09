export default function HotelCard({ data }) {
  const { name, area, price_per_night, rating, vibe, amenities = [], booking_url } = data;

  const stars = "★".repeat(Math.round(rating || 4)) + "☆".repeat(5 - Math.round(rating || 4));

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-2xl">🏨</div>
            <div>
              <h3 className="font-bold text-gray-800 m-0">{name}</h3>
              {area && <p className="text-sm text-gray-500 m-0">{area}</p>}
            </div>
          </div>
          {price_per_night && (
            <div className="text-right">
              <p className="text-lg font-bold text-indigo-600 m-0">£{price_per_night}</p>
              <p className="text-xs text-gray-400 m-0">/night</p>
            </div>
          )}
        </div>

        {rating && (
          <div className="flex items-center gap-2 mb-3">
            <span className="text-amber-400 text-sm">{stars}</span>
            <span className="text-sm text-gray-500">{rating}/5</span>
          </div>
        )}

        {vibe && (
          <span className="inline-block bg-indigo-50 text-indigo-600 text-xs font-medium px-3 py-1 rounded-full mb-3">
            {vibe}
          </span>
        )}

        {amenities.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {amenities.map((a, i) => (
              <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-lg">{a}</span>
            ))}
          </div>
        )}

        {booking_url && (
          <a href={booking_url} target="_blank" rel="noopener noreferrer"
            className="block w-full text-center bg-indigo-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-indigo-700 transition no-underline">
            Book Now
          </a>
        )}
      </div>
    </div>
  );
}
