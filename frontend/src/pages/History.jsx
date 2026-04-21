import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getItineraries } from "../services/api";
import DESTINATION_IMAGES from "../data/destinationImages";
import { toTitleCase, FALLBACK_IMG } from "../utils/helpers";

const getDestImage = (id) => DESTINATION_IMAGES[id] || FALLBACK_IMG;

export default function History() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrip, setSelectedTrip] = useState(null);

  useEffect(() => {
    // Load from Firebase or localStorage
    async function load() {
      try {
        const data = await getItineraries(user);
        setTrips(data.itineraries || []);
      } catch {
        // Fallback: load from localStorage
        const stored = JSON.parse(localStorage.getItem("saved_itineraries") || "[]");
        setTrips(stored);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (selectedTrip) {
    const t = selectedTrip;
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={() => setSelectedTrip(null)}
          className="text-indigo-600 text-sm hover:underline mb-4 cursor-pointer"
        >
          ← Back to trips
        </button>
        <div className="rounded-2xl p-8 text-white mb-6"
          style={{ backgroundImage: `linear-gradient(135deg, rgba(79,70,229,0.85), rgba(147,51,234,0.8)), url(${getDestImage(t.destination?.id)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
          <h1 className="text-2xl font-bold">
            {toTitleCase(t.destination?.name)}, {t.destination?.country}
          </h1>
          <p className="text-indigo-200 text-sm mt-2">
            📅 {t.dates?.start} to {t.dates?.end} · {t.dates?.duration_days} days
          </p>
          <p className="text-indigo-200 text-sm">
            💰 Estimated: £{t.estimated_total_cost_gbp?.toLocaleString()}
          </p>
        </div>

        {/* Flights */}
        {t.flights && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
            <h2 className="font-bold text-slate-800 mb-3">Flights</h2>
            {t.flights.map((f, i) => (
              <div key={i} className="flex justify-between py-2 text-sm border-b border-slate-50">
                <span className="text-slate-700">{f.airline} {f.flight_number}</span>
                <span className="text-slate-500">{f.departure?.time} → {f.arrival?.time}</span>
                <span className="font-semibold">£{f.price_gbp}</span>
              </div>
            ))}
          </div>
        )}

        {/* Hotels */}
        {t.hotels && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
            <h2 className="font-bold text-slate-800 mb-3">Hotels</h2>
            {t.hotels.map((h, i) => (
              <div key={i} className="flex justify-between py-2 text-sm border-b border-slate-50">
                <span className="text-slate-700">{h.name}</span>
                <span className="text-slate-500">{"★".repeat(h.stars)} {h.rating}/5</span>
                <span className="font-semibold">£{h.price_per_night_gbp}/night</span>
              </div>
            ))}
          </div>
        )}

        {/* Activities */}
        {t.activities && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="font-bold text-slate-800 mb-3">Activities</h2>
            {t.activities.map((a, i) => (
              <div key={i} className="py-2 text-sm border-b border-slate-50">
                <span className="text-slate-700 font-medium">{a.name}</span>
                <span className="text-slate-400 ml-2">— {a.category}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">My Trips</h1>
      <p className="text-slate-500 text-sm mb-6">Your saved itineraries</p>

      {trips.length === 0 ? (
        <div className="text-center py-16">
          <span className="text-5xl">🗺</span>
          <h3 className="text-lg font-medium text-slate-700 mt-4">No trips saved yet</h3>
          <p className="text-slate-500 text-sm mt-1">
            Plan a trip from the dashboard and save it here
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-4 px-6 py-2 bg-indigo-600 text-white text-sm rounded-lg font-medium hover:bg-indigo-700 cursor-pointer"
          >
            Plan a Trip
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trips.map((trip, i) => (
            <button
              key={trip.id || i}
              onClick={() => setSelectedTrip(trip)}
              className="bg-white rounded-xl border border-slate-200 p-0 text-left hover:shadow-md transition cursor-pointer overflow-hidden"
            >
              <div className="h-32 w-full" style={{ backgroundImage: `linear-gradient(transparent 40%, rgba(0,0,0,0.45)), url(${getDestImage(trip.destination?.id)})`, backgroundSize: "cover", backgroundPosition: "center" }} />
              <div className="p-5">
                <h3 className="font-bold text-slate-800">
                  {toTitleCase(trip.destination?.name)}, {trip.destination?.country}
                </h3>
                <p className="text-sm text-slate-500 mt-1">
                  📅 {trip.dates?.start} to {trip.dates?.end}
                </p>
                <p className="text-sm text-slate-500">
                  ⏱ {trip.dates?.duration_days} days
                </p>
                <p className="text-lg font-semibold text-indigo-600 mt-2">
                  £{trip.estimated_total_cost_gbp?.toLocaleString()}
                </p>
                {trip.saved_at && (
                  <p className="text-xs text-slate-400 mt-2">
                    Saved {new Date(trip.saved_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
