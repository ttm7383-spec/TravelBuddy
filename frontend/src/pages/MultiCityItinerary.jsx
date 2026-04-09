import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getMultiCityItinerary, saveItinerary } from "../services/api";
import DESTINATION_IMAGES from "../data/destinationImages";

const getDestImage = (id) =>
  DESTINATION_IMAGES[id] || "/images/destinations/bangkok.jpg";

const WEATHER_ICONS = {
  "01d": "☀️", "01n": "🌙", "02d": "⛅", "02n": "☁️",
  "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️",
  "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️",
  "11d": "⛈️", "11n": "⛈️", "13d": "🌨️", "13n": "🌨️",
  "50d": "🌫️", "50n": "🌫️",
};

const CATEGORY_ICONS = {
  "Arts & Culture": "🏛️",
  "Outdoors & Nature": "🌿",
  "Food & Drink": "🍽️",
  "Landmarks & Sightseeing": "🏰",
  "Outdoors & Adventure": "🧗",
};

export default function MultiCityItinerary() {
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeCity, setActiveCity] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const destinations = searchParams.get("destinations")?.split(",") || [];
        const data = await getMultiCityItinerary(user, {
          destination_ids: destinations,
          departure_city: searchParams.get("departure") || "London",
          travel_dates: {
            start: searchParams.get("start") || "2026-04-15",
            end: searchParams.get("end") || "2026-04-22",
          },
          budget_level: searchParams.get("budget") || "medium",
          nationality: searchParams.get("nationality") || "GB",
        });
        setItinerary(data);
      } catch (err) {
        setError(err.message || "Failed to load itinerary");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [searchParams, user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveItinerary(user, itinerary);
      setSaved(true);
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">Building your multi-city itinerary...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-red-50 text-red-600 rounded-lg p-6 text-center">
          <p className="font-medium">{error}</p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-4 text-sm text-indigo-600 hover:underline cursor-pointer"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { route, total_dates, cities, cost_breakdown, estimated_total_cost_gbp } = itinerary;
  const city = cities[activeCity];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="rounded-2xl p-8 text-white mb-8"
        style={{ backgroundImage: `linear-gradient(135deg, rgba(79,70,229,0.85), rgba(147,51,234,0.8)), url(${getDestImage(cities[0]?.destination?.id)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
        <button
          onClick={() => navigate("/dashboard")}
          className="text-indigo-200 hover:text-white text-sm mb-4 cursor-pointer"
        >
          ← Back to results
        </button>
        <h1 className="text-3xl font-bold mb-2">Multi-City Trip</h1>
        <div className="flex gap-4 mt-2 text-indigo-200 text-sm">
          <span>📅 {total_dates.start} to {total_dates.end}</span>
          <span>⏱ {total_dates.duration_days} days total</span>
          <span>🏙 {cities.length} cities</span>
        </div>
      </div>

      {/* Route Overview */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-bold text-slate-800 mb-4">Your Route</h2>
        <div className="flex items-center gap-1 flex-wrap">
          {route.map((stop, i) => (
            <div key={i} className="flex items-center gap-1">
              <span className={`text-sm px-3 py-1.5 rounded-full font-medium ${
                i === 0 || i === route.length - 1
                  ? "bg-slate-100 text-slate-600"
                  : "bg-indigo-100 text-indigo-700"
              }`}>
                {stop}
              </span>
              {i < route.length - 1 && (
                <span className="text-slate-300 text-lg">→</span>
              )}
            </div>
          ))}
        </div>
        <div className="flex gap-3 mt-4">
          {cities.map((c, i) => (
            <div key={i} className="text-xs text-slate-500">
              <span className="font-medium text-slate-700">{c.destination.name}:</span>{" "}
              {c.dates.duration_days} days ({c.dates.start} — {c.dates.end})
            </div>
          ))}
        </div>
      </div>

      {/* City Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {cities.map((c, i) => (
          <button
            key={i}
            onClick={() => setActiveCity(i)}
            className={`px-4 py-2.5 rounded-xl text-sm font-medium transition cursor-pointer whitespace-nowrap ${
              activeCity === i
                ? "bg-indigo-600 text-white shadow-md"
                : "bg-white border border-slate-200 text-slate-600 hover:border-indigo-300"
            }`}
          >
            <span className="inline-block w-6 h-6 rounded-full mr-2 flex-shrink-0" style={{ backgroundImage: `url(${getDestImage(c.destination.id)})`, backgroundSize: "cover", backgroundPosition: "center", verticalAlign: "middle" }} />
            {c.destination.name}, {c.destination.country}
            <span className="ml-2 text-xs opacity-75">{c.dates.duration_days}d</span>
          </button>
        ))}
      </div>

      {/* Active City Detail */}
      <div className="space-y-6">
        {/* City Header */}
        <div className="rounded-xl p-6 text-white relative overflow-hidden"
          style={{ backgroundImage: `linear-gradient(135deg, rgba(99,102,241,0.82), rgba(168,85,247,0.78)), url(${getDestImage(city.destination.id)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-indigo-200 text-xs mb-1">City {activeCity + 1} of {cities.length}</p>
              <h2 className="text-2xl font-bold">{city.destination.name}, {city.destination.country}</h2>
              <div className="flex gap-3 mt-2 text-indigo-200 text-sm">
                <span>📅 {city.dates.start} — {city.dates.end}</span>
                <span>⏱ {city.dates.duration_days} days</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-indigo-200 text-xs">Flying from</p>
              <p className="font-semibold">{city.flight_from}</p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            {city.destination.tags.map((tag) => (
              <span key={tag} className="text-xs bg-white/20 px-2 py-0.5 rounded-full">{tag}</span>
            ))}
          </div>
        </div>

        {/* Visa */}
        {city.visa_info && (
          <div className={`rounded-xl border p-5 ${
            city.visa_info.visa_required
              ? "bg-amber-50 border-amber-200"
              : "bg-green-50 border-green-200"
          }`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl">{city.visa_info.visa_required ? "📋" : "✅"}</span>
              <div>
                <h3 className="font-bold text-slate-800 mb-1">Visa for {city.destination.country}</h3>
                <p className={`text-sm font-medium ${
                  city.visa_info.visa_required ? "text-amber-700" : "text-green-700"
                }`}>
                  {city.visa_info.requirement}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Weather */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-800 mb-3">Weather in {city.destination.name}</h3>
          <div className="grid grid-cols-7 gap-2">
            {city.weather.daily_forecast.map((day) => (
              <div key={day.date} className="text-center p-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500 font-medium">{day.day?.slice(0, 3)}</div>
                <div className="text-2xl my-1">{WEATHER_ICONS[day.icon] || "🌤️"}</div>
                <div className="text-xs font-semibold text-slate-700">{day.temp_high_c}°</div>
                <div className="text-[10px] text-slate-400">{day.temp_low_c}°</div>
              </div>
            ))}
          </div>
        </div>

        {/* Flights */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-800 mb-1">
            Flights: {city.flight_from} → {city.destination.name}
          </h3>
          <p className="text-xs text-slate-400 mb-3">Leg {activeCity + 1} of your trip</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-100">
                  <th className="pb-2 font-medium">Airline</th>
                  <th className="pb-2 font-medium">Route</th>
                  <th className="pb-2 font-medium">Time</th>
                  <th className="pb-2 font-medium">Duration</th>
                  <th className="pb-2 font-medium text-right">Price</th>
                </tr>
              </thead>
              <tbody>
                {city.flights.map((f, i) => (
                  <tr key={i} className="border-b border-slate-50">
                    <td className="py-3">
                      <div className="font-medium text-slate-700">{f.airline}</div>
                      <div className="text-xs text-slate-400">{f.flight_number}</div>
                    </td>
                    <td className="py-3 text-slate-600">
                      {f.departure.airport} → {f.arrival.airport}
                    </td>
                    <td className="py-3 text-slate-600">
                      {f.departure.time} → {f.arrival.time}
                    </td>
                    <td className="py-3 text-slate-600">{f.duration}</td>
                    <td className="py-3 text-right font-semibold text-slate-800">£{f.price_gbp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Hotels */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-800 mb-3">Hotels in {city.destination.name}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {city.hotels.map((h, i) => (
              <div key={i} className="border border-slate-200 rounded-lg p-4">
                <h4 className="font-semibold text-slate-800 text-sm">{h.name}</h4>
                <div className="flex items-center gap-1 mt-1">
                  {Array.from({ length: h.stars }).map((_, j) => (
                    <span key={j} className="text-amber-400 text-xs">★</span>
                  ))}
                  <span className="text-xs text-slate-400 ml-1">{h.rating}/5</span>
                </div>
                <div className="text-lg font-bold text-indigo-600 mt-2">
                  £{h.price_per_night_gbp}<span className="text-xs font-normal text-slate-400">/night</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {h.amenities.slice(0, 4).map((a) => (
                    <span key={a} className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{a}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activities */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-800 mb-3">Things to Do in {city.destination.name}</h3>
          <div className="space-y-3">
            {city.activities.map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50">
                <span className="text-xl mt-0.5">{CATEGORY_ICONS[a.category] || "📍"}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-slate-800 text-sm">{a.name}</h4>
                    <span className="text-xs text-amber-500">★ {a.rating}</span>
                  </div>
                  <p className="text-xs text-slate-500">{a.category}</p>
                  <p className="text-xs text-slate-400">{a.address}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Per-city cost */}
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-700 mb-2">
            Cost for {city.destination.name} ({city.dates.duration_days} days)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
            <div>
              <p className="text-xs text-slate-500">Flight</p>
              <p className="font-semibold text-slate-800">£{city.cost_breakdown.flights}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Hotel</p>
              <p className="font-semibold text-slate-800">£{city.cost_breakdown.accommodation}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Food</p>
              <p className="font-semibold text-slate-800">£{city.cost_breakdown.food}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Activities</p>
              <p className="font-semibold text-slate-800">£{city.cost_breakdown.activities}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Subtotal</p>
              <p className="font-bold text-indigo-600">£{city.cost_breakdown.total}</p>
            </div>
          </div>
        </div>

        {/* Nav between cities */}
        <div className="flex justify-between">
          <button
            onClick={() => setActiveCity((c) => c - 1)}
            disabled={activeCity === 0}
            className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 disabled:invisible cursor-pointer"
          >
            ← Previous City
          </button>
          <button
            onClick={() => setActiveCity((c) => c + 1)}
            disabled={activeCity === cities.length - 1}
            className="px-4 py-2 text-sm text-indigo-600 hover:text-indigo-700 disabled:invisible cursor-pointer"
          >
            Next City →
          </button>
        </div>
      </div>

      {/* Grand Total Cost Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mt-8 mb-6">
        <h2 className="font-bold text-slate-800 mb-4">Total Trip Cost (All Cities)</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-lg">✈️</span>
              <div>
                <p className="text-sm font-medium text-slate-700">All Flights</p>
                <p className="text-xs text-slate-400">{cities.length} legs + return</p>
              </div>
            </div>
            <span className="font-semibold text-slate-800">£{cost_breakdown.flights.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-lg">🏨</span>
              <div>
                <p className="text-sm font-medium text-slate-700">All Accommodation</p>
                <p className="text-xs text-slate-400">{total_dates.duration_days} nights total</p>
              </div>
            </div>
            <span className="font-semibold text-slate-800">£{cost_breakdown.accommodation.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-lg">🍽️</span>
              <p className="text-sm font-medium text-slate-700">Food & Dining</p>
            </div>
            <span className="font-semibold text-slate-800">£{cost_breakdown.food.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-lg">🎯</span>
              <p className="text-sm font-medium text-slate-700">Activities & Sightseeing</p>
            </div>
            <span className="font-semibold text-slate-800">£{cost_breakdown.activities.toLocaleString()}</span>
          </div>
          {cost_breakdown.visa > 0 && (
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="text-lg">📋</span>
                <p className="text-sm font-medium text-slate-700">Visa / Entry Fees</p>
              </div>
              <span className="font-semibold text-slate-800">£{cost_breakdown.visa}</span>
            </div>
          )}
          <div className="flex justify-between items-center pt-3">
            <p className="text-lg font-bold text-slate-800">Grand Total</p>
            <p className="text-3xl font-bold text-indigo-600">
              £{estimated_total_cost_gbp.toLocaleString()}
            </p>
          </div>
          <p className="text-xs text-slate-400">
            Approximate cost for 1 person across all {cities.length} cities.
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end mb-8">
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={`px-6 py-3 rounded-lg font-medium text-sm transition cursor-pointer ${
            saved
              ? "bg-green-100 text-green-700"
              : "bg-indigo-600 text-white hover:bg-indigo-700"
          } disabled:opacity-70`}
        >
          {saved ? "✓ Saved!" : saving ? "Saving..." : "Save Multi-City Itinerary"}
        </button>
      </div>
    </div>
  );
}
