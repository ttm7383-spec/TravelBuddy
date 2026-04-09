import { useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getItinerary, saveItinerary } from "../services/api";
import DESTINATION_IMAGES from "../data/destinationImages";

const getDestImage = (id) =>
  DESTINATION_IMAGES[id] || "/images/destinations/bangkok.jpg";

const WEATHER_ICONS = {
  "01d": "\u2600\uFE0F", "01n": "\uD83C\uDF19", "02d": "\u26C5", "02n": "\u2601\uFE0F",
  "03d": "\u2601\uFE0F", "03n": "\u2601\uFE0F", "04d": "\u2601\uFE0F", "04n": "\u2601\uFE0F",
  "09d": "\uD83C\uDF27\uFE0F", "09n": "\uD83C\uDF27\uFE0F", "10d": "\uD83C\uDF26\uFE0F", "10n": "\uD83C\uDF27\uFE0F",
  "11d": "\u26C8\uFE0F", "11n": "\u26C8\uFE0F", "13d": "\uD83C\uDF28\uFE0F", "13n": "\uD83C\uDF28\uFE0F",
  "50d": "\uD83C\uDF2B\uFE0F", "50n": "\uD83C\uDF2B\uFE0F",
};

const CATEGORY_ICONS = {
  "Arts & Culture": "\uD83C\uDFDB\uFE0F",
  "Outdoors & Nature": "\uD83C\uDF3F",
  "Food & Drink": "\uD83C\uDF7D\uFE0F",
  "Landmarks & Sightseeing": "\uD83C\uDFF0",
  "Outdoors & Adventure": "\uD83E\uDDD7",
};

export default function Itinerary() {
  const { destinationId } = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const customCity = searchParams.get("custom_city");
        const params = {
          departure_city: searchParams.get("departure") || "London",
          travel_dates: {
            start: searchParams.get("start") || "2026-04-15",
            end: searchParams.get("end") || "2026-04-22",
          },
          budget_level: searchParams.get("budget") || "medium",
          nationality: searchParams.get("nationality") || "GB",
        };
        if (customCity) {
          params.custom_city = customCity;
        } else {
          params.destination_id = destinationId;
        }
        const data = await getItinerary(user, params);
        setItinerary(data);
      } catch (err) {
        setError(err.message || "Failed to load itinerary");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [destinationId, searchParams, user]);

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
          <p className="text-slate-500 text-sm">Building your itinerary...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-red-50 text-red-600 rounded-lg p-6 text-center">
          <p className="font-medium">{error}</p>
          <button onClick={() => navigate("/dashboard")} className="mt-4 text-sm text-indigo-600 hover:underline cursor-pointer">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { destination, dates, weather, flights, hotels, activities, restaurants, estimated_total_cost_gbp, visa_info, cost_breakdown, is_live_prices } = itinerary;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="rounded-2xl p-8 text-white mb-8 relative overflow-hidden"
        style={{ backgroundImage: `linear-gradient(135deg, rgba(26,26,94,0.82) 0%, rgba(0,102,255,0.72) 50%, rgba(0,191,255,0.68) 100%), url(${getDestImage(destination.id)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
        <button onClick={() => navigate("/dashboard")}
          className="text-white/60 hover:text-white text-sm mb-4 cursor-pointer border-0 bg-transparent flex items-center gap-1">
          {"←"} Back to dashboard
        </button>
        <h1 style={{ fontSize: 36, fontWeight: 800, lineHeight: 1.2, margin: 0 }}>
          {destination.name}{destination.country ? `, ${destination.country}` : ""}
        </h1>
        <div className="flex gap-4 mt-3 text-white/70 text-sm flex-wrap">
          <span>📅 {dates.start} to {dates.end}</span>
          <span>⏱ {dates.duration_days} days</span>
          <span>💷 £{destination.avg_daily_cost_gbp}/day avg</span>
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          {destination.tags.map((tag) => (
            <span key={tag} className="text-xs bg-white/15 backdrop-blur px-2.5 py-1 rounded-full">{tag}</span>
          ))}
        </div>
        {is_live_prices && (
          <div className="mt-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-green-200 font-medium">Live prices</span>
          </div>
        )}
        {/* Decorative circles */}
        <div className="absolute -right-16 -top-16 w-48 h-48 rounded-full bg-white/5" />
        <div className="absolute -right-8 -bottom-20 w-36 h-36 rounded-full bg-white/5" />
      </div>

      {/* Visa & Entry Requirements */}
      {visa_info && (
        <div className={`rounded-xl border p-5 mb-6 ${
          visa_info.visa_required ? "bg-amber-50 border-amber-200" : "bg-green-50 border-green-200"
        }`}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">{visa_info.visa_required ? "\uD83D\uDCCB" : "\u2705"}</span>
            <div className="flex-1">
              <h2 className="font-bold text-slate-800 mb-1">Visa & Entry Requirements</h2>
              <p className={`text-sm font-medium ${visa_info.visa_required ? "text-amber-700" : "text-green-700"}`}>
                {visa_info.requirement === "visa-free" ? "No visa required" :
                 visa_info.requirement === "visa-on-arrival" ? "Visa on arrival" :
                 visa_info.requirement === "e-visa" ? "E-Visa required" : "Visa required"}
                {visa_info.duration_days > 0 && ` \u2014 up to ${visa_info.duration_days} days`}
              </p>
              {visa_info.recommendation && (
                <p className="text-sm text-slate-600 mt-1">{visa_info.recommendation}</p>
              )}
              {visa_info.cost_gbp > 0 && (
                <p className="text-xs text-slate-500 mt-2">Visa cost: &pound;{visa_info.cost_gbp} (included in total below)</p>
              )}
              {visa_info.processing_days > 0 && (
                <p className="text-xs font-medium text-amber-600 mt-1">
                  &#128161; Apply at least {visa_info.processing_days} days before departure
                </p>
              )}
              {visa_info.notes && (
                <p className="text-xs text-slate-400 mt-1">{visa_info.notes}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Weather Strip */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-bold text-slate-800 mb-3">Weather Forecast</h2>
        <p className="text-sm text-slate-500 mb-4">{weather.summary}</p>
        <div className="grid grid-cols-3 sm:grid-cols-7 gap-2">
          {weather.daily_forecast.map((day) => (
            <div key={day.date} className="text-center p-2 rounded-lg bg-slate-50">
              <div className="text-xs text-slate-500 font-medium">{day.day?.slice(0, 3)}</div>
              <div className="text-2xl my-1">{WEATHER_ICONS[day.icon] || "\uD83C\uDF24\uFE0F"}</div>
              <div className="text-xs font-semibold text-slate-700">{day.temp_high_c}&deg;</div>
              <div className="text-[10px] text-slate-400">{day.temp_low_c}&deg;</div>
            </div>
          ))}
        </div>
      </div>

      {/* Flights */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-slate-800">Flights</h2>
          {!is_live_prices && (
            <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">Estimated prices</span>
          )}
        </div>
        <div className="space-y-3">
          {flights.map((f, i) => (
            <div key={i} className={`border rounded-lg p-4 transition ${
              f.badge === "cheapest" ? "border-green-300 bg-green-50/50" : "border-slate-200"
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  {/* Airline circle */}
                  <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600">
                    {(f.airline_code || f.airline?.slice(0, 2) || "??").toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{f.airline}</p>
                    <p className="text-xs text-slate-400">{f.flight_number}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-slate-800">&pound;{f.price_gbp}</p>
                  {f.price_per_person_gbp && f.price_per_person_gbp !== f.price_gbp && (
                    <p className="text-xs text-slate-400">&pound;{f.price_per_person_gbp}/person</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="text-center">
                  <p className="font-semibold text-slate-700">{f.departure?.time}</p>
                  <p className="text-xs text-slate-400">{f.departure?.airport}</p>
                </div>
                <div className="flex-1 flex items-center gap-1">
                  <div className="h-px flex-1 bg-slate-300" />
                  <span className="text-xs text-slate-400 px-1">
                    {f.duration} &middot; {f.stops_label || (f.stops === 0 ? "Direct" : `${f.stops} stop`)}
                  </span>
                  <div className="h-px flex-1 bg-slate-300" />
                </div>
                <div className="text-center">
                  <p className="font-semibold text-slate-700">{f.arrival?.time}</p>
                  <p className="text-xs text-slate-400">{f.arrival?.airport}</p>
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                {f.badge === "cheapest" && (
                  <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">Cheapest</span>
                )}
                {f.badge === "fastest" && (
                  <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">Fastest</span>
                )}
                <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{f.cabin_class || "Economy"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hotels */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-bold text-slate-800 mb-3">Hotels</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {hotels.map((h, i) => (
            <div key={i} className="border border-slate-200 rounded-lg overflow-hidden">
              <div className="bg-gradient-to-r from-slate-100 to-slate-50 p-3 text-center">
                <span className="text-3xl">{h.stars >= 5 ? "\uD83C\uDFE8" : h.stars >= 4 ? "\uD83C\uDFE8" : "\uD83C\uDFE0"}</span>
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-slate-800 text-sm leading-tight">{h.name}</h3>
                <div className="flex items-center gap-1 mt-1">
                  {Array.from({ length: h.stars || 3 }).map((_, j) => (
                    <span key={j} className="text-amber-400 text-xs">&starf;</span>
                  ))}
                  <span className="text-xs text-slate-400 ml-1">{h.rating}/5</span>
                </div>
                {h.room_type && <p className="text-xs text-slate-500 mt-1">{h.room_type}</p>}
                <div className="flex flex-wrap gap-1 mt-2">
                  {h.cancellation && (
                    <span className="text-[10px] bg-green-50 text-green-600 px-1.5 py-0.5 rounded">
                      {h.cancellation === "Free cancellation" ? "\u2713 " : ""}{h.cancellation}
                    </span>
                  )}
                  {h.board_type && h.board_type !== "Room Only" && (
                    <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{h.board_type}</span>
                  )}
                </div>
                {h.amenities && h.amenities.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {h.amenities.slice(0, 3).map((a) => (
                      <span key={a} className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{a}</span>
                    ))}
                  </div>
                )}
                <div className="mt-3 pt-2 border-t border-slate-100">
                  <span className="text-lg font-bold text-indigo-600">&pound;{h.price_per_night_gbp}</span>
                  <span className="text-xs text-slate-400">/night</span>
                  {h.total_price_gbp && (
                    <p className="text-xs text-slate-400">Total: &pound;{h.total_price_gbp.toLocaleString()}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Activities */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-bold text-slate-800 mb-3">Things to Do</h2>
        <div className="space-y-3">
          {activities.map((a, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50">
              <span className="text-xl mt-0.5">{CATEGORY_ICONS[a.category] || "\uD83D\uDCCD"}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-slate-800 text-sm">{a.name}</h3>
                  <span className="text-xs text-amber-500">&starf; {a.rating}</span>
                </div>
                <p className="text-xs text-slate-500">{a.category}</p>
                <p className="text-xs text-slate-400">{a.address}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Restaurants & Food */}
      {restaurants && restaurants.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
          <h2 className="font-bold text-slate-800 mb-3">Where to Eat</h2>
          <div className="space-y-3">
            {restaurants.map((r, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100">
                <span className="text-xl mt-0.5">🍽️</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-medium text-slate-800 text-sm">{r.name}</h3>
                    <span className="text-xs text-amber-500">★ {r.rating}</span>
                    <span className="text-xs text-slate-400">{r.price_level}</span>
                  </div>
                  <p className="text-xs text-slate-500">{r.cuisine}</p>
                  {r.must_try && (
                    <p className="text-xs text-indigo-600 mt-0.5">Must try: {r.must_try}</p>
                  )}
                  <p className="text-xs text-slate-400 mt-0.5">{r.address}</p>
                  {r.dietary && r.dietary.length > 0 && (
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {r.dietary.map((d) => (
                        <span key={d} className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          d === "halal" ? "bg-green-50 text-green-600" :
                          d === "vegan" || d === "vegan-options" ? "bg-emerald-50 text-emerald-600" :
                          d === "vegetarian" || d === "vegetarian-options" ? "bg-lime-50 text-lime-600" :
                          d === "gluten-free" || d === "gluten-free-options" ? "bg-amber-50 text-amber-600" :
                          d === "kosher" ? "bg-blue-50 text-blue-600" :
                          "bg-slate-100 text-slate-500"
                        }`}>{d.replace("-options", " friendly").replace("-", " ")}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-bold text-slate-800 mb-4">Estimated Total Cost</h2>
        <div className="space-y-3">
          {cost_breakdown && (
            <>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-lg">&#9992;&#65039;</span>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Return Flights</p>
                    <p className="text-xs text-slate-400">Cheapest option &times; 2</p>
                  </div>
                </div>
                <span className="font-semibold text-slate-800">&pound;{cost_breakdown.flights?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-lg">&#127976;</span>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Accommodation</p>
                    <p className="text-xs text-slate-400">Cheapest hotel &times; {dates.duration_days} nights</p>
                  </div>
                </div>
                <span className="font-semibold text-slate-800">&pound;{cost_breakdown.accommodation?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-lg">&#127869;&#65039;</span>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Food & Dining</p>
                    <p className="text-xs text-slate-400">Estimated &times; {dates.duration_days} days</p>
                  </div>
                </div>
                <span className="font-semibold text-slate-800">&pound;{cost_breakdown.food?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-lg">&#127919;</span>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Activities & Sightseeing</p>
                    <p className="text-xs text-slate-400">Estimated &times; {dates.duration_days} days</p>
                  </div>
                </div>
                <span className="font-semibold text-slate-800">&pound;{cost_breakdown.activities?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{visa_info?.visa_required ? "\uD83D\uDCCB" : "\u2705"}</span>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Visa & Entry</p>
                    <p className="text-xs text-slate-400">{visa_info?.requirement || "N/A"}</p>
                  </div>
                </div>
                <span className={`font-semibold ${cost_breakdown.visa > 0 ? "text-slate-800" : "text-green-600"}`}>
                  {cost_breakdown.visa > 0 ? `\u00a3${cost_breakdown.visa}` : "Free"}
                </span>
              </div>
              {cost_breakdown.insurance > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">&#128737;&#65039;</span>
                    <div>
                      <p className="text-sm font-medium text-slate-700">Travel Insurance (est.)</p>
                      <p className="text-xs text-slate-400">~3% of flights + hotel</p>
                    </div>
                  </div>
                  <span className="font-semibold text-slate-800">&pound;{cost_breakdown.insurance?.toLocaleString()}</span>
                </div>
              )}
            </>
          )}
          <div className="flex justify-between items-center pt-3">
            <p className="text-lg font-bold text-slate-800">Total</p>
            <p className="text-3xl font-bold text-indigo-600">&pound;{estimated_total_cost_gbp?.toLocaleString()}</p>
          </div>
          <p className="text-xs text-slate-400">Approximate cost for 1 person. Based on cheapest available flights and hotels.</p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={`px-6 py-3 rounded-lg font-medium text-sm transition cursor-pointer ${
            saved ? "bg-green-100 text-green-700" : "bg-indigo-600 text-white hover:bg-indigo-700"
          } disabled:opacity-70`}
        >
          {saved ? "\u2713 Saved!" : saving ? "Saving..." : "Save Itinerary"}
        </button>
      </div>
    </div>
  );
}
