import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRecommendations, getAllDestinations, saveProfile } from "../services/api";
import DESTINATION_IMAGES, { CATEGORY_IMAGES } from "../data/destinationImages";

const FLAG_MAP = {
  Thailand: "🇹🇭", Vietnam: "🇻🇳", Morocco: "🇲🇦", Hungary: "🇭🇺",
  Portugal: "🇵🇹", Indonesia: "🇮🇩", Mexico: "🇲🇽", Poland: "🇵🇱",
  "Sri Lanka": "🇱🇰", Greece: "🇬🇷", Spain: "🇪🇸", Italy: "🇮🇹",
  "Czech Republic": "🇨🇿", Turkey: "🇹🇷", "Costa Rica": "🇨🇷",
  Japan: "🇯🇵", USA: "🇺🇸", Netherlands: "🇳🇱", Iceland: "🇮🇸",
  "South Africa": "🇿🇦", UAE: "🇦🇪", Maldives: "🇲🇻", France: "🇫🇷",
  Switzerland: "🇨🇭", Australia: "🇦🇺", "New Zealand": "🇳🇿", Tanzania: "🇹🇿",
  "United Kingdom": "🇬🇧",
};

const IMG_KEYWORDS = {
  bangkok: "bangkok+temple", bali: "bali+rice+terrace", barcelona: "barcelona+sagrada",
  paris: "paris+eiffel", tokyo: "tokyo+shibuya", rome: "rome+colosseum",
  dubai: "dubai+skyline", "new-york": "newyork+skyline", istanbul: "istanbul+mosque",
  lisbon: "lisbon+tram", maldives: "maldives+overwater", "cape-town": "capetown+mountain",
  santorini: "santorini+greece", amsterdam: "amsterdam+canal", prague: "prague+bridge",
  budapest: "budapest+parliament", marrakech: "marrakech+market", hanoi: "hanoi+vietnam",
  cancun: "cancun+beach", reykjavik: "iceland+aurora",
};

const TRENDING = ["bangkok", "lisbon", "bali", "barcelona", "tokyo", "dubai", "santorini", "cape-town"];

const BUDGET_OPTIONS = [
  { value: "low", label: "Budget", desc: "Under £80/day" },
  { value: "medium", label: "Mid-Range", desc: "£80–£200/day" },
  { value: "high", label: "Luxury", desc: "£200+/day" },
];

const STYLE_OPTIONS = [
  { value: "beach", label: "Beach" }, { value: "adventure", label: "Adventure" },
  { value: "culture", label: "Culture" }, { value: "city", label: "City" },
  { value: "nature", label: "Nature" }, { value: "nightlife", label: "Nightlife" },
  { value: "food", label: "Food & Drink" }, { value: "wellness", label: "Wellness" },
  { value: "history", label: "History" }, { value: "family", label: "Family Fun" },
];

const GROUP_OPTIONS = [
  { value: "solo", label: "Solo" }, { value: "couple", label: "Couple" },
  { value: "family", label: "Family" }, { value: "friends", label: "Friends" },
];

function SkeletonCard() {
  return (
    <div className="rounded-2xl overflow-hidden bg-white" style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.08)" }}>
      <div className="h-52 bg-gray-200 animate-pulse" />
      <div className="p-5 space-y-3">
        <div className="h-5 bg-gray-200 rounded-lg w-3/4 animate-pulse" style={{ animationDelay: "0.1s" }} />
        <div className="h-3 bg-gray-100 rounded-lg w-full animate-pulse" style={{ animationDelay: "0.2s" }} />
        <div className="flex gap-2">
          <div className="h-6 bg-gray-100 rounded-full w-16 animate-pulse" style={{ animationDelay: "0.3s" }} />
          <div className="h-6 bg-gray-100 rounded-full w-16 animate-pulse" style={{ animationDelay: "0.35s" }} />
          <div className="h-6 bg-gray-100 rounded-full w-16 animate-pulse" style={{ animationDelay: "0.4s" }} />
        </div>
        <div className="h-11 bg-gray-200 rounded-xl animate-pulse" style={{ animationDelay: "0.5s" }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, profile, setProfile } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState("recommend");
  const [departure, setDeparture] = useState("London");
  const [startDate, setStartDate] = useState("2026-04-15");
  const [endDate, setEndDate] = useState("2026-04-22");
  const [budget, setBudget] = useState(profile?.budget_level || "medium");
  const [styles, setStyles] = useState(profile?.travel_style || ["beach", "culture"]);
  const [group, setGroup] = useState(profile?.group_type || "solo");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [allDestinations, setAllDestinations] = useState([]);
  const [citySearch, setCitySearch] = useState("");
  const [selected, setSelected] = useState([]);

  useEffect(() => {
    getAllDestinations().then((d) => setAllDestinations(d.destinations || [])).catch(() => {});
  }, []);

  const toggleStyle = (v) => setStyles((p) => p.includes(v) ? p.filter((s) => s !== v) : [...p, v]);

  const addCity = (dest) => {
    if (!selected.find((s) => s.id === dest.id)) setSelected((p) => [...p, dest]);
    setCitySearch("");
  };
  const addCustomCity = () => {
    const name = citySearch.trim();
    if (!name) return;
    const id = "custom-" + name.toLowerCase().replace(/\s+/g, "-");
    if (selected.find((s) => s.id === id)) return;
    setSelected((p) => [...p, { id, name, country: "", avg_daily_cost_gbp: 100, tags: [], custom: true }]);
    setCitySearch("");
  };
  const removeCity = (id) => setSelected((p) => p.filter((s) => s.id !== id));
  const moveCity = (i, dir) => {
    const a = [...selected]; const t = i + dir;
    if (t < 0 || t >= a.length) return;
    [a[i], a[t]] = [a[t], a[i]]; setSelected(a);
  };

  const filteredCities = citySearch.trim()
    ? allDestinations.filter((d) =>
        (d.name.toLowerCase().includes(citySearch.toLowerCase()) ||
         d.country.toLowerCase().includes(citySearch.toLowerCase())) &&
        !selected.find((s) => s.id === d.id)
      ) : [];

  const handleSearch = async () => {
    setLoading(true); setError(""); setResults(null);
    const pd = {
      name: profile?.name || "", email: profile?.email || user?.email || "",
      budget_level: budget, travel_style: styles, group_type: group,
      preferred_duration: profile?.preferred_duration || "one_week",
      passport_country: profile?.passport_country || "GB",
    };
    saveProfile(user, pd).then(() => setProfile({ ...pd, onboarding_complete: true })).catch(() => {});
    try {
      const data = await getRecommendations(user, {
        departure_city: departure, travel_dates: { start: startDate, end: endDate },
        budget_level: budget, style_preferences: styles, group_type: group,
        passport_country: profile?.passport_country || "GB",
      });
      setResults(data.recommendations);
    } catch (err) { setError(err.message || "Something went wrong"); }
    finally { setLoading(false); }
  };

  const handlePlanTrip = (dest) => {
    const p = new URLSearchParams({ departure, start: startDate, end: endDate, budget, nationality: profile?.passport_country || "GB" });
    if (dest.custom) { p.set("custom_city", dest.name); navigate(`/itinerary/custom?${p}`); }
    else navigate(`/itinerary/${dest.id}?${p}`);
  };
  const handlePlanMultiCity = () => {
    const ids = selected.map((s) => s.custom ? `custom:${s.name}` : s.id);
    const p = new URLSearchParams({ destinations: ids.join(","), departure, start: startDate, end: endDate, budget, nationality: profile?.passport_country || "GB" });
    navigate(`/itinerary/multi?${p}`);
  };

  const getImageUrl = (dest) => {
    if (DESTINATION_IMAGES[dest.id]) return DESTINATION_IMAGES[dest.id];
    const kw = IMG_KEYWORDS[dest.id] || dest.name.toLowerCase().replace(/\s+/g, "+");
    return `https://source.unsplash.com/400x300/?${kw},travel`;
  };

  // Trending destinations from our data
  const trendingDests = allDestinations.filter((d) => TRENDING.includes(d.id));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* === HERO === */}
      <div className="relative overflow-hidden" style={{
        background: "linear-gradient(135deg, #1a1a5e 0%, #0066FF 50%, #00BFFF 100%)",
        padding: "80px 40px 100px",
      }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-8">
          <div className="flex-1">
            <h1 className="text-white mb-3" style={{ fontSize: 56, fontWeight: 800, lineHeight: 1.1 }}>
              Where to next?
            </h1>
            <p className="text-white mb-0" style={{ fontSize: 20, opacity: 0.85 }}>
              Personalised trips built around you — your budget, passport, and travel style
            </p>
          </div>
          <div className="flex gap-3">
            {[["✈️", "80+ Destinations"], ["🛂", "Visa checks included"], ["💷", "Real-time prices"]].map(([icon, text]) => (
              <div key={text} className="bg-white/15 backdrop-blur-sm rounded-2xl px-4 py-4 text-center text-white" style={{ minWidth: 130 }}>
                <div className="text-2xl mb-1">{icon}</div>
                <div className="text-xs font-semibold">{text}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* === SEARCH CARD (overlaps hero) === */}
      <div className="max-w-5xl mx-auto px-4" style={{ marginTop: -50, position: "relative", zIndex: 10 }}>
        <div className="bg-white rounded-2xl p-8" style={{ boxShadow: "0 20px 60px rgba(0,0,0,0.15)" }}>
          {/* Mode tabs */}
          <div className="flex gap-2 mb-6">
            <button onClick={() => setMode("recommend")}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition cursor-pointer border-0 ${
                mode === "recommend" ? "text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`} style={mode === "recommend" ? { background: "linear-gradient(90deg, #0066FF, #00BFFF)" } : {}}>
              🌟 Get Recommendations
            </button>
            <button onClick={() => setMode("build")}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition cursor-pointer border-0 ${
                mode === "build" ? "text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`} style={mode === "build" ? { background: "linear-gradient(90deg, #0066FF, #00BFFF)" } : {}}>
              🗺️ Build Your Own Trip
            </button>
          </div>

          {/* Row 1: Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-0 md:divide-x divide-gray-200 border border-gray-200 rounded-xl mb-5 overflow-hidden">
            <div className="p-4">
              <div className="text-xs text-gray-400 font-medium mb-1">🛫 Flying From</div>
              <input type="text" value={departure} onChange={(e) => setDeparture(e.target.value)}
                className="w-full text-base font-semibold text-gray-800 border-0 p-0 focus:outline-none bg-transparent" placeholder="London" />
            </div>
            <div className="p-4">
              <div className="text-xs text-gray-400 font-medium mb-1">📅 Departure</div>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                className="w-full text-sm font-semibold text-gray-800 border-0 p-0 focus:outline-none bg-transparent" />
            </div>
            <div className="p-4">
              <div className="text-xs text-gray-400 font-medium mb-1">📅 Return</div>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
                className="w-full text-sm font-semibold text-gray-800 border-0 p-0 focus:outline-none bg-transparent" />
            </div>
            <div className="p-4">
              <div className="text-xs text-gray-400 font-medium mb-1">👥 Travelling as</div>
              <select value={group} onChange={(e) => setGroup(e.target.value)}
                className="w-full text-sm font-semibold text-gray-800 border-0 p-0 focus:outline-none bg-transparent cursor-pointer">
                {GROUP_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {mode === "recommend" && (
            <>
              {/* Budget pills */}
              <div className="flex gap-2 mb-4">
                {BUDGET_OPTIONS.map((o) => (
                  <button key={o.value} onClick={() => setBudget(o.value)}
                    className={`px-5 py-2 rounded-full text-sm font-semibold transition cursor-pointer border-0 ${
                      budget === o.value ? "text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`} style={budget === o.value ? { background: "#0066FF" } : {}}>
                    {o.label} <span className="text-xs font-normal opacity-75 ml-1">{o.desc}</span>
                  </button>
                ))}
              </div>

              {/* Style chips - always visible */}
              <div className="flex flex-wrap gap-2 mb-5">
                {STYLE_OPTIONS.map((o) => (
                  <button key={o.value} onClick={() => toggleStyle(o.value)}
                    className="px-4 py-2 rounded-full text-sm font-semibold transition cursor-pointer border-0"
                    style={styles.includes(o.value)
                      ? { background: "#0066FF", color: "white" }
                      : { background: "#F3F4F6", color: "#374151" }
                    }>
                    <span className="inline-block w-4 h-4 rounded-full mr-1.5" style={{ backgroundImage: `url(${CATEGORY_IMAGES[o.value]})`, backgroundSize: "cover", backgroundPosition: "center", verticalAlign: "middle" }} />
                    {o.label}
                  </button>
                ))}
              </div>

              {/* Search button */}
              <button onClick={handleSearch} disabled={loading || styles.length === 0}
                className="w-full text-white py-4 rounded-xl text-lg font-bold border-0 cursor-pointer disabled:opacity-50 transition"
                style={{ background: "linear-gradient(90deg, #0066FF, #00BFFF)", height: 56 }}>
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Searching...
                  </span>
                ) : "Find My Perfect Trip ✈️"}
              </button>
            </>
          )}

          {mode === "build" && (
            <>
              <div className="relative mb-4">
                <div className="text-xs text-gray-400 font-medium mb-1">Add cities to your trip</div>
                <input type="text" value={citySearch}
                  onChange={(e) => setCitySearch(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && citySearch.trim()) { filteredCities.length > 0 ? addCity(filteredCities[0]) : addCustomCity(); } }}
                  placeholder="Type any city... (e.g. Madrid, Valencia, Bali)"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                {filteredCities.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-20 max-h-64 overflow-y-auto">
                    {filteredCities.slice(0, 8).map((d) => (
                      <button key={d.id} onClick={() => addCity(d)}
                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-blue-50 transition cursor-pointer border-0 bg-transparent border-b border-gray-100">
                        <span className="text-lg">{FLAG_MAP[d.country] || "🌍"}</span>
                        <div className="flex-1"><p className="text-sm font-medium text-gray-800 m-0">{d.name}</p><p className="text-xs text-gray-500 m-0">{d.country}</p></div>
                        <span className="text-xs text-gray-400">{"£"}{d.avg_daily_cost_gbp}/day</span>
                        <span className="text-blue-500 font-bold">+</span>
                      </button>
                    ))}
                  </div>
                )}
                {citySearch.trim() && filteredCities.length === 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-20 overflow-hidden">
                    <button onClick={addCustomCity} className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-blue-50 transition cursor-pointer border-0 bg-transparent">
                      <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">+</span>
                      <div><p className="text-sm font-medium text-gray-800 m-0">Add &quot;{citySearch.trim()}&quot;</p><p className="text-xs text-gray-500 m-0">Custom destination</p></div>
                    </button>
                  </div>
                )}
              </div>
              {selected.length > 0 && (
                <div className="space-y-2 mb-4">
                  {selected.map((dest, i) => (
                    <div key={dest.id} className="flex items-center gap-3 bg-gray-50 rounded-xl p-3">
                      <div className="w-7 h-7 rounded-full text-white flex items-center justify-center text-xs font-bold shrink-0" style={{ background: "#0066FF" }}>{i + 1}</div>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-semibold text-gray-800">{FLAG_MAP[dest.country] || "🌍"} {dest.name}</span>
                        {dest.custom && <span className="ml-2 text-[10px] bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded font-medium">Custom</span>}
                      </div>
                      <button onClick={() => moveCity(i, -1)} disabled={i === 0} className="text-gray-400 hover:text-gray-600 disabled:opacity-30 cursor-pointer border-0 bg-transparent text-xs">▲</button>
                      <button onClick={() => moveCity(i, 1)} disabled={i === selected.length - 1} className="text-gray-400 hover:text-gray-600 disabled:opacity-30 cursor-pointer border-0 bg-transparent text-xs">▼</button>
                      <button onClick={() => removeCity(dest.id)} className="text-gray-400 hover:text-red-500 cursor-pointer border-0 bg-transparent text-lg">×</button>
                    </div>
                  ))}
                  <div className="flex items-center gap-1.5 flex-wrap mt-2 px-1">
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{departure}</span>
                    {selected.map((d) => (<span key={d.id} className="flex items-center gap-1.5"><span className="text-gray-300">→</span><span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{d.name}</span></span>))}
                    <span className="text-gray-300">→</span>
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{departure}</span>
                  </div>
                </div>
              )}
              {selected.length >= 1 && (
                <div className="flex gap-3">
                  <button onClick={selected.length === 1 ? () => handlePlanTrip(selected[0]) : handlePlanMultiCity}
                    className="flex-1 text-white py-3 rounded-xl text-sm font-bold border-0 cursor-pointer"
                    style={{ background: "linear-gradient(90deg, #0066FF, #00BFFF)" }}>
                    {selected.length === 1 ? `Plan Trip to ${selected[0].name}` : `Plan Multi-City Trip (${selected.length} cities)`}
                  </button>
                  <button onClick={() => setSelected([])} className="px-4 py-3 border border-gray-200 text-gray-500 rounded-xl text-sm cursor-pointer bg-transparent hover:bg-gray-50">Clear</button>
                </div>
              )}
              {selected.length === 0 && (
                <div className="text-center py-6 border-2 border-dashed border-gray-200 rounded-xl">
                  <span className="text-3xl">🗺️</span>
                  <p className="text-gray-500 text-sm mt-2 mb-0">Search above to add destinations</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* === CONTENT === */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Error */}
        {error && <div className="bg-red-50 text-red-600 text-sm rounded-xl p-4 mb-6">{error}</div>}

        {/* Skeleton loading */}
        {loading && (
          <div>
            <h2 className="text-lg font-bold text-gray-800 mb-4">Finding your perfect destinations...</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[0, 1, 2, 3, 4, 5].map((i) => <SkeletonCard key={i} />)}
            </div>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <div>
            <h2 className="mb-4" style={{ fontSize: 28, fontWeight: 800, color: "#1A1A2E" }}>
              Recommended for you
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.map((dest) => (
                <div key={dest.id} className="rounded-2xl overflow-hidden bg-white cursor-pointer transition-all duration-300 hover:-translate-y-2"
                  style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.12)" }}
                  onClick={() => handlePlanTrip(dest)}>
                  {/* Image */}
                  <div className="relative h-52 bg-gray-200" style={{
                    backgroundImage: `url(${getImageUrl(dest)})`,
                    backgroundSize: "cover", backgroundPosition: "center",
                  }}>
                    {/* Country badge */}
                    <div className="absolute top-3 left-3 text-white text-xs font-medium px-3 py-1.5 rounded-full"
                      style={{ background: "rgba(0,0,0,0.4)", backdropFilter: "blur(4px)" }}>
                      {FLAG_MAP[dest.country] || "🌍"} {dest.country}
                    </div>
                    {/* Match score */}
                    <div className="absolute top-3 right-3 text-white text-xs font-bold px-3 py-1.5 rounded-full"
                      style={{ background: "linear-gradient(135deg, #FF6B35, #FF8E53)" }}>
                      {Math.round(dest.match_score * 100)}% match
                    </div>
                    {/* Visa badge */}
                    {dest.visa_info && (
                      <div className="absolute bottom-3 left-3 text-white text-xs font-medium px-2.5 py-1 rounded-xl"
                        style={{ background: dest.visa_info.requirement === "visa-free" ? "#10B981" :
                          dest.visa_info.requirement === "e-visa" || dest.visa_info.requirement === "visa-on-arrival" ? "#3B82F6" : "#F59E0B" }}>
                        {dest.visa_info.requirement === "visa-free" ? "✓ Visa Free" :
                         dest.visa_info.requirement === "visa-on-arrival" ? `Visa on Arrival${dest.visa_info.cost_gbp > 0 ? ` £${dest.visa_info.cost_gbp}` : ""}` :
                         dest.visa_info.requirement === "e-visa" ? `💻 E-Visa £${dest.visa_info.cost_gbp}` :
                         `⚠ Visa Required £${dest.visa_info.cost_gbp}`}
                      </div>
                    )}
                  </div>
                  {/* Info */}
                  <div className="p-5">
                    <h3 className="m-0 mb-1" style={{ fontSize: 22, fontWeight: 800, color: "#1A1A2E" }}>{dest.name}</h3>
                    <p className="text-gray-500 text-xs mb-3 truncate">{dest.match_reason}</p>
                    <div className="flex gap-1.5 mb-3 flex-wrap">
                      {dest.tags.slice(0, 3).map((t) => (
                        <span key={t} className="text-xs px-2.5 py-1 rounded-full font-medium"
                          style={{ background: "#EEF2FF", color: "#4F46E5" }}>{t}</span>
                      ))}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-600 mb-4">
                      <span>⭐ {dest.avg_rating}</span>
                      <span>💷 £{dest.avg_daily_cost_gbp}/day</span>
                    </div>
                    <button className="w-full py-2.5 rounded-xl text-white text-sm font-semibold border-0 cursor-pointer transition hover:opacity-90"
                      style={{ background: "#0066FF" }}
                      onClick={(e) => { e.stopPropagation(); handlePlanTrip(dest); }}>
                      Plan This Trip →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!results && !loading && !error && mode === "recommend" && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">✈️</div>
            <h3 className="text-xl font-bold text-gray-700 m-0 mb-2">Ready to explore?</h3>
            <p className="text-gray-400 text-sm m-0">Enter your details above and find your perfect trip</p>
          </div>
        )}

        {/* Trending section */}
        {!results && !loading && trendingDests.length > 0 && mode === "recommend" && (
          <div className="mt-4">
            <h2 className="mb-1" style={{ fontSize: 28, fontWeight: 800, color: "#1A1A2E" }}>
              Trending Right Now 🔥
            </h2>
            <p className="text-gray-500 text-sm mb-5">Most searched destinations this week</p>
            <div className="flex gap-4 overflow-x-auto pb-4" style={{ scrollbarWidth: "none" }}>
              {trendingDests.map((dest) => (
                <div key={dest.id} onClick={() => handlePlanTrip(dest)}
                  className="shrink-0 rounded-2xl overflow-hidden cursor-pointer transition-transform hover:scale-105"
                  style={{ width: 160, height: 200, position: "relative" }}>
                  <div className="absolute inset-0 bg-gray-300" style={{
                    backgroundImage: `url(${getImageUrl(dest)})`,
                    backgroundSize: "cover", backgroundPosition: "center",
                  }} />
                  <div className="absolute inset-0" style={{ background: "linear-gradient(transparent 40%, rgba(0,0,0,0.7))" }} />
                  <div className="absolute bottom-3 left-3 right-3">
                    <p className="text-white font-bold text-sm m-0">{FLAG_MAP[dest.country] || ""} {dest.name}</p>
                    <p className="text-white/70 text-xs m-0">£{dest.avg_daily_cost_gbp}/day</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Floating multi-city bar */}
      {selected.length >= 2 && mode === "recommend" && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-white border border-gray-200 rounded-2xl px-6 py-4 flex items-center gap-4 max-w-2xl"
          style={{ boxShadow: "0 20px 60px rgba(0,0,0,0.2)" }}>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-gray-800 m-0">Multi-City Trip ({selected.length} cities)</p>
            <p className="text-xs text-gray-500 truncate m-0">{departure} → {selected.map((s) => s.name).join(" → ")} → {departure}</p>
          </div>
          <button onClick={handlePlanMultiCity} className="text-white px-5 py-2.5 rounded-xl text-sm font-bold border-0 cursor-pointer whitespace-nowrap"
            style={{ background: "#0066FF" }}>Plan Trip</button>
          <button onClick={() => setSelected([])} className="text-gray-400 hover:text-gray-600 cursor-pointer text-lg border-0 bg-transparent">×</button>
        </div>
      )}
    </div>
  );
}
