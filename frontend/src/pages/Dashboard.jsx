import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRecommendations, getAllDestinations, saveProfile, getTrendingDestinations, sendFeedback, sendChatMessage } from "../services/api";
import DESTINATION_IMAGES, { CATEGORY_IMAGES } from "../data/destinationImages";
import CalendarConnect from "../components/CalendarConnect";
import {
  OverviewCard, ItineraryCard, HotelCard, FoodCard,
  FlightCard, VisaCard, BudgetCard, TipsCard, WeatherCard,
} from "../components/chat-cards";
import PlaceAutocomplete from "../components/PlaceAutocomplete";

const CHAT_CARD_MAP = {
  overview: OverviewCard, itinerary: ItineraryCard, hotel: HotelCard, food: FoodCard,
  flight: FlightCard, visa: VisaCard, budget: BudgetCard, tips: TipsCard, weather: WeatherCard,
};

/* ═══════════════════════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════════════════════ */

const FLAG_MAP = {
  Thailand: "\u{1F1F9}\u{1F1ED}", Vietnam: "\u{1F1FB}\u{1F1F3}", Morocco: "\u{1F1F2}\u{1F1E6}", Hungary: "\u{1F1ED}\u{1F1FA}",
  Portugal: "\u{1F1F5}\u{1F1F9}", Indonesia: "\u{1F1EE}\u{1F1E9}", Mexico: "\u{1F1F2}\u{1F1FD}", Poland: "\u{1F1F5}\u{1F1F1}",
  "Sri Lanka": "\u{1F1F1}\u{1F1F0}", Greece: "\u{1F1EC}\u{1F1F7}", Spain: "\u{1F1EA}\u{1F1F8}", Italy: "\u{1F1EE}\u{1F1F9}",
  "Czech Republic": "\u{1F1E8}\u{1F1FF}", Turkey: "\u{1F1F9}\u{1F1F7}", "Costa Rica": "\u{1F1E8}\u{1F1F7}",
  Japan: "\u{1F1EF}\u{1F1F5}", USA: "\u{1F1FA}\u{1F1F8}", Netherlands: "\u{1F1F3}\u{1F1F1}", Iceland: "\u{1F1EE}\u{1F1F8}",
  "South Africa": "\u{1F1FF}\u{1F1E6}", UAE: "\u{1F1E6}\u{1F1EA}", Maldives: "\u{1F1F2}\u{1F1FB}", France: "\u{1F1EB}\u{1F1F7}",
  Switzerland: "\u{1F1E8}\u{1F1ED}", Australia: "\u{1F1E6}\u{1F1FA}", "New Zealand": "\u{1F1F3}\u{1F1FF}", Tanzania: "\u{1F1F9}\u{1F1FF}",
  Germany: "\u{1F1E9}\u{1F1EA}", Austria: "\u{1F1E6}\u{1F1F9}", Croatia: "\u{1F1ED}\u{1F1F7}", UK: "\u{1F1EC}\u{1F1E7}",
  Denmark: "\u{1F1E9}\u{1F1F0}", Sweden: "\u{1F1F8}\u{1F1EA}", Belgium: "\u{1F1E7}\u{1F1EA}", Estonia: "\u{1F1EA}\u{1F1EA}",
  Romania: "\u{1F1F7}\u{1F1F4}", Bulgaria: "\u{1F1E7}\u{1F1EC}", Malta: "\u{1F1F2}\u{1F1F9}", "South Korea": "\u{1F1F0}\u{1F1F7}",
  Malaysia: "\u{1F1F2}\u{1F1FE}", Cambodia: "\u{1F1F0}\u{1F1ED}", Nepal: "\u{1F1F3}\u{1F1F5}", India: "\u{1F1EE}\u{1F1F3}",
  Taiwan: "\u{1F1F9}\u{1F1FC}", Laos: "\u{1F1F1}\u{1F1E6}", Peru: "\u{1F1F5}\u{1F1EA}", Colombia: "\u{1F1E8}\u{1F1F4}",
  Argentina: "\u{1F1E6}\u{1F1F7}", Cuba: "\u{1F1E8}\u{1F1FA}", Brazil: "\u{1F1E7}\u{1F1F7}", Canada: "\u{1F1E8}\u{1F1E6}",
  Kenya: "\u{1F1F0}\u{1F1EA}", Egypt: "\u{1F1EA}\u{1F1EC}", Georgia: "\u{1F1EC}\u{1F1EA}", Azerbaijan: "\u{1F1E6}\u{1F1FF}",
  Jordan: "\u{1F1EF}\u{1F1F4}", Oman: "\u{1F1F4}\u{1F1F2}", Qatar: "\u{1F1F6}\u{1F1E6}", Fiji: "\u{1F1EB}\u{1F1EF}",
  Philippines: "\u{1F1F5}\u{1F1ED}", Singapore: "\u{1F1F8}\u{1F1EC}", China: "\u{1F1E8}\u{1F1F3}", "Hong Kong": "\u{1F1ED}\u{1F1F0}",
  Slovenia: "\u{1F1F8}\u{1F1EE}", Montenegro: "\u{1F1F2}\u{1F1EA}", Chile: "\u{1F1E8}\u{1F1F1}",
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

const BUDGET_OPTIONS = [
  { value: "low", label: "Budget", desc: "Under \u00a380/day" },
  { value: "medium", label: "Mid-Range", desc: "\u00a380\u2013\u00a3200/day" },
  { value: "high", label: "Luxury", desc: "\u00a3200+/day" },
];

const STYLE_OPTIONS = [
  { value: "beach", label: "Beach" }, { value: "adventure", label: "Adventure" },
  { value: "culture", label: "Culture" }, { value: "city", label: "City" },
  { value: "nature", label: "Nature" }, { value: "nightlife", label: "Nightlife" },
  { value: "food", label: "Food" }, { value: "history", label: "History" },
  { value: "wellness", label: "Wellness" }, { value: "hiking", label: "Hiking" },
  { value: "romance", label: "Romance" }, { value: "wildlife", label: "Wildlife" },
];

const GROUP_OPTIONS = [
  { value: "solo", label: "Solo" }, { value: "couple", label: "Couple" },
  { value: "family", label: "Family" }, { value: "friends", label: "Friends" },
];

const UK_DESTINATIONS = [
  { id: "cotswolds", name: "The Cotswolds", region: "England", type: "weekend", distance: "1.5h from London", cost: "\u00a380\u2013\u00a3120/day", tags: ["Villages", "Nature", "Food"], img: "cotswolds+village+england", highlight: "Honey-stone villages & rolling hills" },
  { id: "edinburgh", name: "Edinburgh", region: "Scotland", type: "weekend", distance: "1h flight", cost: "\u00a370\u2013\u00a3130/day", tags: ["History", "Culture", "Nightlife"], img: "edinburgh+castle+scotland", highlight: "Castle, whisky & the Royal Mile" },
  { id: "lake-district", name: "Lake District", region: "England", type: "weekend", distance: "3h from London", cost: "\u00a360\u2013\u00a3100/day", tags: ["Hiking", "Nature", "Lakes"], img: "lake+district+england", highlight: "Breathtaking fells & lakes" },
  { id: "bath", name: "Bath", region: "England", type: "daytrip", distance: "1.5h from London", cost: "\u00a350\u2013\u00a390/day", tags: ["History", "Architecture", "Food"], img: "bath+england+roman", highlight: "Roman baths & Georgian elegance" },
  { id: "brighton", name: "Brighton", region: "England", type: "daytrip", distance: "1h from London", cost: "\u00a340\u2013\u00a380/day", tags: ["Beach", "Nightlife", "Food"], img: "brighton+pier+beach", highlight: "Pebble beach, quirky Lanes & pubs" },
  { id: "oxford", name: "Oxford", region: "England", type: "daytrip", distance: "1h from London", cost: "\u00a340\u2013\u00a370/day", tags: ["History", "Culture"], img: "oxford+university+england", highlight: "Dreaming spires & centuries of history" },
  { id: "cornwall", name: "Cornwall", region: "England", type: "weekend", distance: "4.5h from London", cost: "\u00a370\u2013\u00a3130/day", tags: ["Beach", "Food", "Nature"], img: "cornwall+coast+england", highlight: "Atlantic coast, cliffs & pasties" },
  { id: "york", name: "York", region: "England", type: "weekend", distance: "2h from London", cost: "\u00a355\u2013\u00a390/day", tags: ["History", "Food"], img: "york+minster+england", highlight: "Medieval walls, Shambles & great food" },
  { id: "cambridge", name: "Cambridge", region: "England", type: "daytrip", distance: "1h from London", cost: "\u00a340\u2013\u00a370/day", tags: ["History", "Culture"], img: "cambridge+river+punting", highlight: "Punting, colleges & riverside pubs" },
  { id: "snowdonia", name: "Snowdonia", region: "Wales", type: "weekend", distance: "3h from London", cost: "\u00a355\u2013\u00a395/day", tags: ["Hiking", "Adventure"], img: "snowdonia+wales+mountain", highlight: "Mount Snowdon & wild Welsh landscapes" },
];

const QUICK_PROMPTS = [
  { emoji: "\u{1F950}", text: "Weekend in Paris under \u00a3300" },
  { emoji: "\u{1F3F0}", text: "3 days in Prague on a budget" },
  { emoji: "\u{1F30A}", text: "Beach holiday in Greece" },
  { emoji: "\u{1F355}", text: "Best food cities in Italy" },
  { emoji: "\u{1F305}", text: "Day trip from London this weekend" },
  { emoji: "\u{1F3AD}", text: "Culture trip to Vienna or Budapest" },
];

/* ═══════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════ */

function SkeletonCard() {
  return (
    <div style={{ borderRadius: 16, overflow: "hidden", background: "var(--surface)", boxShadow: "var(--shadow-card)" }}>
      <div style={{ height: 200, background: "#E8E8EC" }} className="animate-pulse" />
      <div style={{ padding: 20 }}>
        <div style={{ height: 18, background: "#E8E8EC", borderRadius: 6, width: "70%", marginBottom: 12 }} className="animate-pulse" />
        <div style={{ height: 12, background: "#F0F0F3", borderRadius: 6, width: "100%", marginBottom: 12 }} className="animate-pulse" />
        <div style={{ display: "flex", gap: 8 }}>
          {[0, 1, 2].map(i => <div key={i} style={{ height: 24, background: "#F0F0F3", borderRadius: 6, width: 56 }} className="animate-pulse" />)}
        </div>
      </div>
    </div>
  );
}

function UKCard({ dest, onSelect }) {
  return (
    <div onClick={() => onSelect(dest)} className="card-hover" style={{
      borderRadius: 16, overflow: "hidden", cursor: "pointer",
      background: "var(--surface)", boxShadow: "var(--shadow-card)",
    }}>
      <div style={{
        height: 150, position: "relative", overflow: "hidden",
        backgroundImage: `url(https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&q=80)`,
        backgroundSize: "cover", backgroundPosition: "center",
      }}>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 30%, rgba(26,26,46,0.7))" }} />
        <div style={{ position: "absolute", top: 12, left: 12 }}>
          <span style={{
            fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 6,
            background: dest.type === "daytrip" ? "var(--success)" : "var(--primary)",
            color: "white", fontFamily: "'DM Sans', sans-serif",
          }}>
            {dest.type === "daytrip" ? "Day Trip" : "Weekend"}
          </span>
        </div>
        <div style={{ position: "absolute", bottom: 12, left: 12, right: 12 }}>
          <p style={{ color: "white", fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 16, margin: 0 }}>{dest.name}</p>
          <p style={{ color: "rgba(255,255,255,0.65)", fontSize: 12, margin: 0, fontFamily: "'DM Sans', sans-serif" }}>{dest.region} &middot; {dest.distance}</p>
        </div>
      </div>
      <div style={{ padding: 16 }}>
        <p style={{ color: "var(--body)", fontSize: 13, margin: "0 0 10px 0" }}>{dest.highlight}</p>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
          {dest.tags.map(t => (
            <span key={t} style={{
              fontSize: 11, padding: "3px 8px", borderRadius: 6,
              background: "var(--primary-light)", color: "var(--primary-dark)",
              fontWeight: 500, fontFamily: "'DM Sans', sans-serif",
            }}>{t}</span>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 13, color: "var(--primary)" }}>{dest.cost}</span>
          <button onClick={e => { e.stopPropagation(); onSelect(dest); }} style={{
            fontSize: 13, fontWeight: 600, padding: "6px 16px", borderRadius: 8,
            background: "var(--accent)", color: "white", border: 0, cursor: "pointer",
            fontFamily: "'DM Sans', sans-serif",
          }}>Plan</button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════ */

export default function Dashboard() {
  const { user, profile, setProfile } = useAuth();
  const navigate = useNavigate();

  const [tripMode, setTripMode] = useState("international");
  const [searchMode, setSearchMode] = useState("recommend");
  const [departure, setDeparture] = useState("London");
  const [destination, setDestination] = useState("");
  const [destinationResult, setDestinationResult] = useState(null);
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
  const [trendingDests, setTrendingDests] = useState([]);
  const [ukFilter, setUkFilter] = useState("all");
  const [calendarToast, setCalendarToast] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    getAllDestinations().then(d => setAllDestinations(d.destinations || [])).catch(() => {});
    getTrendingDestinations(new Date().getMonth() + 1, 10)
      .then(d => setTrendingDests(d.trending || []))
      .catch(() => {});
    // Check for calendar connection callback
    if (searchParams.get("calendar") === "connected") {
      setCalendarToast(true);
      searchParams.delete("calendar");
      setSearchParams(searchParams, { replace: true });
      setTimeout(() => setCalendarToast(false), 4000);
    }
  }, []);

  const toggleStyle = v => setStyles(p => p.includes(v) ? p.filter(s => s !== v) : [...p, v]);
  const addCity = dest => { if (!selected.find(s => s.id === dest.id)) setSelected(p => [...p, dest]); setCitySearch(""); };
  const addCustomCity = () => {
    const name = citySearch.trim(); if (!name) return;
    const id = "custom-" + name.toLowerCase().replace(/\s+/g, "-");
    if (selected.find(s => s.id === id)) return;
    setSelected(p => [...p, { id, name, country: "", avg_daily_cost_gbp: 100, tags: [], custom: true }]);
    setCitySearch("");
  };
  const removeCity = id => setSelected(p => p.filter(s => s.id !== id));
  const moveCity = (i, dir) => { const a = [...selected], t = i + dir; if (t < 0 || t >= a.length) return; [a[i], a[t]] = [a[t], a[i]]; setSelected(a); };

  const filteredCities = citySearch.trim()
    ? allDestinations.filter(d =>
        (d.name.toLowerCase().includes(citySearch.toLowerCase()) ||
         d.country.toLowerCase().includes(citySearch.toLowerCase())) &&
        !selected.find(s => s.id === d.id)
      ) : [];

  const computeTripDays = () => {
    if (!startDate || !endDate) return 7;
    const ms = new Date(endDate) - new Date(startDate);
    const days = Math.round(ms / 86400000);
    return Math.max(1, days || 7);
  };

  const handleSearch = async () => {
    setLoading(true); setError(""); setResults(null); setDestinationResult(null);
    const pd = {
      name: profile?.name || "", email: profile?.email || user?.email || "",
      budget_level: budget, travel_style: styles, group_type: group,
      preferred_duration: profile?.preferred_duration || "one_week",
      passport_country: profile?.passport_country || "GB",
    };
    saveProfile(user, pd).then(() => setProfile({ ...pd, onboarding_complete: true })).catch(() => {});

    // If user specified a destination, fetch itinerary, hotels, restaurants,
    // and flight details in parallel so the dashboard renders a full booking-
    // ready view. Each request hits a different intent on the concierge so
    // the backend returns the right card types for each section.
    const destRaw = destination.trim();
    if (destRaw) {
      const dest = destRaw.replace(/\b\w/g, c => c.toUpperCase());
      const origin = (departure.trim() || "London").replace(/\b\w/g, c => c.toUpperCase());
      const days = computeTripDays();
      const budgetLabel = budget === "low" ? "budget" : budget === "high" ? "luxury" : "mid-range";
      const stylesLabel = styles && styles.length ? ` focused on ${styles.join(", ")}` : "";

      const prompts = [
        `Plan ${days} days in ${dest} from ${origin}, ${budgetLabel} budget, travelling ${group}${stylesLabel}.`,
        `Hotels in ${dest} for ${days} nights, ${budgetLabel} budget.`,
        `Restaurants and food in ${dest}.`,
        `Flights from ${origin} to ${dest} on ${startDate}.`,
      ];

      try {
        const settled = await Promise.allSettled(
          prompts.map(p => sendChatMessage(user, p))
        );

        const allCards = [];
        const suggestionSet = new Set();
        const errors = [];
        for (const r of settled) {
          if (r.status === "fulfilled" && r.value) {
            (r.value.cards || []).forEach(c => allCards.push(c));
            (r.value.suggestions || []).forEach(s => suggestionSet.add(s));
          } else if (r.status === "rejected") {
            errors.push(r.reason?.message || "Request failed");
          }
        }

        // Dedupe tips cards that repeat across calls (e.g. the offline-estimate
        // notice would otherwise appear up to 4 times). Also dedupe overview
        // cards by city so any force-corrected blanks don't stack.
        const seenTipKeys = new Set();
        const seenOverviewCities = new Set();
        const deduped = allCards.filter(c => {
          if (c.type === "tips") {
            const cats = ((c.data || {}).categories) || [];
            const key = cats.map(x => (x.name || "") + "|" + ((x.tips || [])[0] || "")).join("~");
            if (seenTipKeys.has(key)) return false;
            seenTipKeys.add(key);
            return true;
          }
          if (c.type === "overview") {
            const cityKey = ((c.data || {}).city || "").toLowerCase();
            if (cityKey && seenOverviewCities.has(cityKey)) return false;
            seenOverviewCities.add(cityKey);
            return true;
          }
          return true;
        });

        // Section order on screen: flight → itinerary → hotel → food → budget
        // → weather/visa → tips → overview. Keeps the booking-flow intuitive.
        const typeOrder = {
          flight: 0, itinerary: 1, hotel: 2, food: 3, budget: 4,
          weather: 5, visa: 6, tips: 7, overview: 8,
        };
        deduped.sort((a, b) => (typeOrder[a.type] ?? 99) - (typeOrder[b.type] ?? 99));

        if (deduped.length === 0) {
          setError(errors[0] || "Could not fetch AI suggestions");
        } else {
          setDestinationResult({
            destination: dest, origin,
            cards: deduped,
            suggestions: Array.from(suggestionSet).slice(0, 6),
          });
        }
      } catch (err) {
        setError(err.message || "Could not fetch AI suggestions");
      } finally { setLoading(false); }
      return;
    }

    try {
      const travelMonth = startDate ? new Date(startDate).getMonth() + 1 : null;
      const data = await getRecommendations(user, {
        departure_city: departure, travel_dates: { start: startDate, end: endDate },
        budget_level: budget, style_preferences: styles, group_type: group,
        passport_country: profile?.passport_country || "GB", travel_month: travelMonth,
      });
      setResults(data.recommendations);
    } catch (err) { setError(err.message || "Something went wrong"); }
    finally { setLoading(false); }
  };

  const handlePlanTrip = dest => {
    const p = new URLSearchParams({ departure, start: startDate, end: endDate, budget, nationality: profile?.passport_country || "GB" });
    if (dest.custom || dest.region) { p.set("custom_city", dest.name); navigate(`/itinerary/custom?${p}`); }
    else navigate(`/itinerary/${dest.id}?${p}`);
  };
  const handlePlanMultiCity = () => {
    const ids = selected.map(s => s.custom ? `custom:${s.name}` : s.id);
    const p = new URLSearchParams({ destinations: ids.join(","), departure, start: startDate, end: endDate, budget, nationality: profile?.passport_country || "GB" });
    navigate(`/itinerary/multi?${p}`);
  };
  const handleQuickPrompt = text => navigate(`/chat?q=${encodeURIComponent(text)}`);

  const getImageUrl = dest => {
    if (DESTINATION_IMAGES[dest.id]) return DESTINATION_IMAGES[dest.id];
    return `https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80`;
  };

  const filteredUK = ukFilter === "all" ? UK_DESTINATIONS : UK_DESTINATIONS.filter(d => d.type === ukFilter);

  /* ── visa badge helper ── */
  const visaBadge = (info) => {
    if (!info) return null;
    const dotColor = info.requirement === "visa-free" ? "var(--success)"
      : (info.requirement === "e-visa" || info.requirement === "visa-on-arrival") ? "var(--primary)" : "var(--warning)";
    const label = info.requirement === "visa-free" ? "Visa free"
      : info.requirement === "visa-on-arrival" ? `On arrival${info.cost_gbp > 0 ? ` \u00a3${info.cost_gbp}` : ""}`
      : info.requirement === "e-visa" ? `E-visa \u00a3${info.cost_gbp}`
      : `Visa req. \u00a3${info.cost_gbp}`;
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11, fontWeight: 500, color: "white", fontFamily: "'DM Sans', sans-serif" }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: dotColor, display: "inline-block" }} />
        {label}
      </span>
    );
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>

      {/* Calendar connected toast */}
      {calendarToast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 9999,
          background: "#00B4D8", color: "white", padding: "12px 20px",
          borderRadius: 10, fontSize: 14, fontWeight: 600,
          fontFamily: "'DM Sans', sans-serif", boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          ✓ Google Calendar connected!
        </div>
      )}

      {/* ═══ HERO ═══ */}
      <div style={{ background: "var(--dark)", position: "relative", overflow: "hidden" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "64px 24px 130px", display: "flex", gap: 40, alignItems: "center" }}>

          {/* Left: Text */}
          <div style={{ flex: "0 0 55%", position: "relative", zIndex: 2 }}>
            <p className="label-uppercase" style={{ color: "var(--primary)", marginBottom: 16 }}>Your personal travel concierge</p>
            <h1 style={{ fontSize: 52, color: "white", margin: "0 0 8px 0", fontFamily: "'Playfair Display', serif" }}>
              The world is waiting.
            </h1>
            <h1 style={{ fontSize: 52, color: "var(--primary)", margin: "0 0 20px 0", fontFamily: "'Playfair Display', serif" }}>
              Where will you go?
            </h1>
            <p style={{ fontSize: 18, color: "rgba(255,255,255,0.6)", margin: "0 0 28px 0", maxWidth: 440, lineHeight: 1.65 }}>
              From a day trip to Brighton to a month across Southeast Asia &mdash; AI-powered recommendations tailored to you.
            </p>
            <p style={{ fontSize: 13, fontWeight: 500, color: "var(--primary)", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: 12 }}>
              <span>150+ Destinations</span>
              <span style={{ color: "rgba(255,255,255,0.25)" }}>&middot;</span>
              <span>15 Passport Countries</span>
              <span style={{ color: "rgba(255,255,255,0.25)" }}>&middot;</span>
              <span>Real-time prices</span>
            </p>
            {/* Trust bar */}
            <div style={{ display: "flex", gap: 20, fontSize: 12, color: "rgba(255,255,255,0.45)" }}>
              <span>{"✓"} Free cancellation on most bookings</span>
              <span>{"✓"} Best price guarantee</span>
              <span>{"✓"} 24/7 AI travel support</span>
            </div>
          </div>

          {/* Right: Image mosaic */}
          <div style={{ flex: "0 0 42%", display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: 10, height: 340, position: "relative", zIndex: 2 }}>
            <div style={{ gridRow: "1/2", gridColumn: "1/2", borderRadius: 12, overflow: "hidden", backgroundImage: "url(https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=400&q=80)", backgroundSize: "cover", backgroundPosition: "center" }} />
            <div style={{ gridRow: "2/3", gridColumn: "1/2", borderRadius: 12, overflow: "hidden", backgroundImage: "url(https://images.unsplash.com/photo-1541849546-216549ae216d?w=400&q=80)", backgroundSize: "cover", backgroundPosition: "center" }} />
            <div style={{ gridRow: "1/3", gridColumn: "2/3", borderRadius: 12, overflow: "hidden", backgroundImage: "url(https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&q=80)", backgroundSize: "cover", backgroundPosition: "center" }} />
          </div>
        </div>

        {/* Mode tabs on hero */}
        <div style={{ position: "absolute", bottom: 80, left: "50%", transform: "translateX(-50%)", display: "flex", gap: 4, zIndex: 10 }}>
          {[
            { id: "international", label: "International" },
            { id: "uk", label: "UK & Local" },
            { id: "daytrip", label: "Day Trips" },
          ].map(tab => (
            <button key={tab.id} onClick={() => { setTripMode(tab.id); setResults(null); setDestinationResult(null); }}
              style={{
                padding: "10px 24px", borderRadius: 8, border: 0, cursor: "pointer",
                fontSize: 14, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                transition: "all 200ms",
                background: tripMode === tab.id ? "white" : "transparent",
                color: tripMode === tab.id ? "var(--dark)" : "rgba(255,255,255,0.55)",
                boxShadow: tripMode === tab.id ? "0 4px 16px rgba(0,0,0,0.2)" : "none",
              }}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ═══ SEARCH CARD ═══ */}
      <div style={{ maxWidth: 900, margin: "-70px auto 0", padding: "0 24px", position: "relative", zIndex: 10 }}>
        <div style={{ background: "var(--surface)", borderRadius: 20, padding: 32, boxShadow: "var(--shadow-float)" }}>

          {/* ── International mode ── */}
          {tripMode === "international" && (
            <>
              {/* Recommend / Build sub-tabs */}
              <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
                {[{ id: "recommend", label: "Get Recommendations" }, { id: "build", label: "Build Your Own" }].map(t => (
                  <button key={t.id} onClick={() => setSearchMode(t.id)} style={{
                    padding: "8px 20px", borderRadius: 8, border: searchMode === t.id ? 0 : "1.5px solid var(--border)",
                    cursor: "pointer", fontSize: 14, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                    background: searchMode === t.id ? "var(--primary)" : "var(--surface)",
                    color: searchMode === t.id ? "white" : "var(--body)",
                    transition: "all 200ms",
                  }}>{t.label}</button>
                ))}
              </div>

              {/* Input row + search button */}
              <div style={{ display: "flex", gap: 0, marginBottom: 20, border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
                {/* Fields */}
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr" }}>
                  <div style={{ padding: "14px 16px", borderRight: "1px solid var(--border)" }}>
                    <div className="label-uppercase" style={{ marginBottom: 4 }}>FLYING FROM</div>
                    <PlaceAutocomplete value={departure} onChange={setDeparture}
                      placeholder="City or country" extraCities={allDestinations} />
                  </div>
                  <div style={{ padding: "14px 16px", borderRight: "1px solid var(--border)" }}>
                    <div className="label-uppercase" style={{ marginBottom: 4 }}>FLYING TO</div>
                    <PlaceAutocomplete value={destination} onChange={setDestination}
                      placeholder="City or country" extraCities={allDestinations} />
                  </div>
                  <div style={{ padding: "14px 16px", borderRight: "1px solid var(--border)" }}>
                    <div className="label-uppercase" style={{ marginBottom: 4 }}>DEPARTURE</div>
                    <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                      style={{ width: "100%", border: 0, padding: 0, fontSize: 15, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif", background: "transparent" }} />
                  </div>
                  <div style={{ padding: "14px 16px", borderRight: "1px solid var(--border)" }}>
                    <div className="label-uppercase" style={{ marginBottom: 4 }}>RETURN</div>
                    <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                      style={{ width: "100%", border: 0, padding: 0, fontSize: 15, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif", background: "transparent" }} />
                  </div>
                  <div style={{ padding: "14px 16px" }}>
                    <div className="label-uppercase" style={{ marginBottom: 4 }}>TRAVELLING AS</div>
                    <select value={group} onChange={e => setGroup(e.target.value)}
                      style={{ width: "100%", border: 0, padding: 0, fontSize: 15, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif", background: "transparent", cursor: "pointer" }}>
                      {GROUP_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                </div>
                {/* Search button */}
                {searchMode === "recommend" && (
                  <button onClick={handleSearch} disabled={loading || (styles.length === 0 && !destination.trim())} style={{
                    width: 120, background: "var(--accent)", color: "white", border: 0, cursor: "pointer",
                    fontSize: 15, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                    opacity: (loading || (styles.length === 0 && !destination.trim())) ? 0.5 : 1,
                  }}>
                    {loading ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : (
                      <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        Search
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Google Calendar integration */}
              <CalendarConnect
                user={user}
                onWindowSelect={(start, end) => {
                  setStartDate(start);
                  setEndDate(end);
                }}
              />

              {searchMode === "recommend" && (
                <>
                  {/* Budget chips */}
                  <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                    {BUDGET_OPTIONS.map(o => (
                      <button key={o.value} onClick={() => setBudget(o.value)} style={{
                        padding: "8px 18px", borderRadius: 8, cursor: "pointer",
                        fontSize: 13, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                        border: budget === o.value ? 0 : "1px solid var(--border)",
                        background: budget === o.value ? "var(--primary)" : "var(--bg)",
                        color: budget === o.value ? "white" : "var(--body)",
                        transition: "all 200ms",
                      }}>{o.label} <span style={{ fontWeight: 400, opacity: 0.7, marginLeft: 4 }}>{o.desc}</span></button>
                    ))}
                  </div>
                  {/* Style chips */}
                  <div style={{ marginBottom: 4 }}>
                    <span className="label-uppercase" style={{ marginRight: 12 }}>I want:</span>
                    <div style={{ display: "inline-flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                      {STYLE_OPTIONS.map(o => (
                        <button key={o.value} onClick={() => toggleStyle(o.value)} style={{
                          padding: "6px 14px", borderRadius: 6, cursor: "pointer",
                          fontSize: 13, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                          border: styles.includes(o.value) ? 0 : "1px solid var(--border)",
                          background: styles.includes(o.value) ? "var(--primary)" : "var(--bg)",
                          color: styles.includes(o.value) ? "white" : "var(--body)",
                          transition: "all 150ms",
                        }}>{o.label}</button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {searchMode === "build" && (
                <>
                  <div style={{ position: "relative", marginBottom: 16 }}>
                    <div className="label-uppercase" style={{ marginBottom: 6 }}>Add cities to your trip</div>
                    <input type="text" value={citySearch} onChange={e => setCitySearch(e.target.value)}
                      onKeyDown={e => { if (e.key === "Enter" && citySearch.trim()) { filteredCities.length > 0 ? addCity(filteredCities[0]) : addCustomCity(); } }}
                      placeholder="Type any city\u2026 (e.g. Madrid, Bali)"
                      style={{ width: "100%", padding: "12px 16px", border: "1.5px solid var(--border)", borderRadius: 10, fontSize: 14, fontFamily: "'DM Sans', sans-serif", color: "var(--dark)", background: "var(--surface)" }} />
                    {filteredCities.length > 0 && (
                      <div style={{ position: "absolute", top: "100%", left: 0, right: 0, marginTop: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, boxShadow: "var(--shadow-lifted)", zIndex: 20, maxHeight: 260, overflowY: "auto" }}>
                        {filteredCities.slice(0, 8).map(d => (
                          <button key={d.id} onClick={() => addCity(d)} style={{
                            width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                            textAlign: "left", cursor: "pointer", border: 0, borderBottom: "1px solid var(--border)",
                            background: "transparent", fontFamily: "'DM Sans', sans-serif",
                          }}
                            onMouseEnter={e => e.currentTarget.style.background = "var(--primary-light)"}
                            onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                            <span style={{ fontSize: 18 }}>{FLAG_MAP[d.country] || "\u{1F30D}"}</span>
                            <div style={{ flex: 1 }}>
                              <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark)", margin: 0 }}>{d.name}</p>
                              <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{d.country}</p>
                            </div>
                            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: "var(--muted)" }}>\u00a3{d.avg_daily_cost_gbp}/day</span>
                            <span style={{ color: "var(--primary)", fontWeight: 700 }}>+</span>
                          </button>
                        ))}
                      </div>
                    )}
                    {citySearch.trim() && filteredCities.length === 0 && (
                      <div style={{ position: "absolute", top: "100%", left: 0, right: 0, marginTop: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, boxShadow: "var(--shadow-lifted)", zIndex: 20 }}>
                        <button onClick={addCustomCity} style={{
                          width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                          cursor: "pointer", border: 0, background: "transparent", fontFamily: "'DM Sans', sans-serif",
                        }}
                          onMouseEnter={e => e.currentTarget.style.background = "var(--primary-light)"}
                          onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                          <span style={{ width: 32, height: 32, borderRadius: 8, background: "var(--primary-light)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 16 }}>+</span>
                          <div>
                            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark)", margin: 0 }}>Add &quot;{citySearch.trim()}&quot;</p>
                            <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>Custom destination</p>
                          </div>
                        </button>
                      </div>
                    )}
                  </div>
                  {selected.length > 0 && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
                      {selected.map((dest, i) => (
                        <div key={dest.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: 12, borderRadius: 10, background: "var(--bg)" }}>
                          <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--primary)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700 }}>{i + 1}</div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <span style={{ fontSize: 14, fontWeight: 600, color: "var(--dark)" }}>{FLAG_MAP[dest.country] || "\u{1F30D}"} {dest.name}</span>
                            {dest.custom && <span style={{ marginLeft: 8, fontSize: 10, background: "var(--accent-light)", color: "var(--accent)", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>Custom</span>}
                          </div>
                          <button onClick={() => moveCity(i, -1)} disabled={i === 0} style={{ border: 0, background: "transparent", cursor: "pointer", color: "var(--muted)", fontSize: 12, opacity: i === 0 ? 0.3 : 1 }}>\u25B2</button>
                          <button onClick={() => moveCity(i, 1)} disabled={i === selected.length - 1} style={{ border: 0, background: "transparent", cursor: "pointer", color: "var(--muted)", fontSize: 12, opacity: i === selected.length - 1 ? 0.3 : 1 }}>\u25BC</button>
                          <button onClick={() => removeCity(dest.id)} style={{ border: 0, background: "transparent", cursor: "pointer", color: "var(--muted)", fontSize: 18, lineHeight: 1 }}>\u00d7</button>
                        </div>
                      ))}
                    </div>
                  )}
                  {selected.length >= 1 ? (
                    <div style={{ display: "flex", gap: 12 }}>
                      <button onClick={selected.length === 1 ? () => handlePlanTrip(selected[0]) : handlePlanMultiCity} style={{
                        flex: 1, padding: "14px 28px", borderRadius: 8, border: 0, cursor: "pointer",
                        background: "var(--accent)", color: "white", fontSize: 15, fontWeight: 600,
                        fontFamily: "'DM Sans', sans-serif",
                      }}>
                        {selected.length === 1 ? `Plan Trip to ${selected[0].name}` : `Plan Multi-City Trip (${selected.length} cities)`}
                      </button>
                      <button onClick={() => setSelected([])} style={{
                        padding: "14px 20px", borderRadius: 8, border: "1.5px solid var(--border)", cursor: "pointer",
                        background: "var(--surface)", color: "var(--body)", fontSize: 14, fontWeight: 500,
                        fontFamily: "'DM Sans', sans-serif",
                      }}>Clear</button>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "32px 0", border: "2px dashed var(--border)", borderRadius: 12 }}>
                      <p style={{ color: "var(--muted)", fontSize: 14, margin: 0 }}>Search above to add destinations</p>
                    </div>
                  )}
                </>
              )}
            </>
          )}

          {/* ── UK & Day Trip mode ── */}
          {(tripMode === "uk" || tripMode === "daytrip") && (
            <div>
              <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
                <div style={{ flex: 1 }}>
                  <div className="label-uppercase" style={{ marginBottom: 6 }}>TRAVELLING FROM</div>
                  <input type="text" value={departure} onChange={e => setDeparture(e.target.value)} placeholder="London"
                    style={{ width: "100%", padding: "12px 16px", border: "1.5px solid var(--border)", borderRadius: 10, fontSize: 14, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif" }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="label-uppercase" style={{ marginBottom: 6 }}>DATE</div>
                  <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                    style={{ width: "100%", padding: "12px 16px", border: "1.5px solid var(--border)", borderRadius: 10, fontSize: 14, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif" }} />
                </div>
                {tripMode === "uk" && (
                  <div style={{ flex: 1 }}>
                    <div className="label-uppercase" style={{ marginBottom: 6 }}>RETURN</div>
                    <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                      style={{ width: "100%", padding: "12px 16px", border: "1.5px solid var(--border)", borderRadius: 10, fontSize: 14, fontWeight: 600, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif" }} />
                  </div>
                )}
              </div>
              {tripMode === "uk" && (
                <div style={{ display: "flex", gap: 8 }}>
                  {[{ id: "all", label: "All" }, { id: "weekend", label: "Weekend Breaks" }, { id: "daytrip", label: "Day Trips" }].map(f => (
                    <button key={f.id} onClick={() => setUkFilter(f.id)} style={{
                      padding: "8px 18px", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 600,
                      fontFamily: "'DM Sans', sans-serif", border: ukFilter === f.id ? 0 : "1px solid var(--border)",
                      background: ukFilter === f.id ? "var(--primary)" : "var(--bg)",
                      color: ukFilter === f.id ? "white" : "var(--body)", transition: "all 200ms",
                    }}>{f.label}</button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ═══ LIVE DEALS ═══ */}
      {tripMode === "international" && !results && !destinationResult && !loading && (
        <div style={{ maxWidth: 1120, margin: "24px auto 0", padding: "0 24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <h2 style={{ fontSize: 22, margin: 0, fontFamily: "'Playfair Display', serif" }}>Flight deals from London</h2>
            <a href="https://www.skyscanner.net/transport/flights/lond/" target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 13, color: "var(--primary)", textDecoration: "none", fontWeight: 600 }}>View all deals</a>
          </div>
          <div className="overflow-x-auto" style={{ display: "flex", gap: 14, paddingBottom: 8 }}>
            {[
              { to: "Lisbon", price: 39, airline: "easyJet", date: "May 2026", img: "https://images.unsplash.com/photo-1585208798174-6cedd4454a2d?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/lis/" },
              { to: "Barcelona", price: 49, airline: "Ryanair", date: "May 2026", img: "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/bcn/" },
              { to: "Prague", price: 44, airline: "Wizz Air", date: "June 2026", img: "https://images.unsplash.com/photo-1541849546-216549ae216d?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/prg/" },
              { to: "Rome", price: 52, airline: "Ryanair", date: "May 2026", img: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/rom/" },
              { to: "Athens", price: 89, airline: "easyJet", date: "June 2026", img: "https://images.unsplash.com/photo-1555993539-1732b0258235?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/ath/" },
              { to: "Amsterdam", price: 45, airline: "KLM", date: "May 2026", img: "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/ams/" },
              { to: "Budapest", price: 41, airline: "Wizz Air", date: "June 2026", img: "https://images.unsplash.com/photo-1565426873118-a17ed65d74b9?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/bud/" },
              { to: "Reykjavik", price: 129, airline: "Icelandair", date: "July 2026", img: "https://images.unsplash.com/photo-1474690870753-1b92efa1f2d8?w=400&q=80", url: "https://www.skyscanner.net/transport/flights/lond/rek/" },
            ].map(deal => (
              <a key={deal.to} href={deal.url}
                target="_blank" rel="noopener noreferrer"
                className="card-hover"
                style={{
                  flexShrink: 0, width: 170, borderRadius: 14, overflow: "hidden",
                  background: "var(--surface)", boxShadow: "var(--shadow-card)",
                  textDecoration: "none", display: "block",
                }}>
                <div style={{
                  height: 100, position: "relative",
                  backgroundImage: `url(${deal.img})`,
                  backgroundSize: "cover", backgroundPosition: "center",
                }}>
                  <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 40%, rgba(26,26,46,0.6))" }} />
                  <div style={{ position: "absolute", bottom: 8, left: 10 }}>
                    <p style={{ color: "white", fontWeight: 700, fontSize: 14, margin: 0, fontFamily: "'DM Sans', sans-serif" }}>{deal.to}</p>
                  </div>
                </div>
                <div style={{ padding: "10px 12px" }}>
                  <p style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 18, color: "var(--primary)", margin: "0 0 2px" }}>{"\u00a3"}{deal.price}</p>
                  <p style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>{deal.airline} &middot; {deal.date}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* ═══ CONTENT ═══ */}
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "40px 24px 60px" }}>

        {error && <div style={{ background: "#FFF5F5", color: "#E53E3E", fontSize: 14, borderRadius: 10, padding: 16, marginBottom: 24, borderLeft: "4px solid #E53E3E" }}>{error}</div>}

        {/* ── International Results ── */}
        {tripMode === "international" && (
          <>
            {loading && (
              <div>
                <h2 style={{ fontSize: 28, marginBottom: 20 }}>Finding your perfect destinations...</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
                  {[0, 1, 2, 3, 4, 5].map(i => <SkeletonCard key={i} />)}
                </div>
              </div>
            )}

            {destinationResult && !loading && (
              <div style={{ marginBottom: 40 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
                  <h2 style={{ fontSize: 32, margin: 0 }}>
                    {destinationResult.origin || departure} &rarr; {destinationResult.destination}
                  </h2>
                  <span style={{ fontSize: 14, color: "var(--muted)" }}>
                    AI-curated itinerary, hotels, food &amp; local tips
                  </span>
                </div>
                <p style={{ fontSize: 14, color: "var(--muted)", margin: "0 0 20px 0" }}>
                  {computeTripDays()} days &middot; {budget === "low" ? "Budget" : budget === "high" ? "Luxury" : "Mid-range"} &middot; Travelling {group}
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 760 }}>
                  {destinationResult.cards.map((card, i) => {
                    const C = CHAT_CARD_MAP[card.type];
                    return C ? <C key={i} data={card.data} /> : null;
                  })}
                </div>
                {destinationResult.suggestions && destinationResult.suggestions.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 20 }}>
                    {destinationResult.suggestions.map((s, j) => (
                      <button key={j} onClick={() => navigate(`/chat?q=${encodeURIComponent(s)}`)} style={{
                        padding: "8px 16px", borderRadius: 8, fontSize: 13, fontWeight: 500,
                        fontFamily: "'DM Sans', sans-serif", border: "1.5px solid var(--border)",
                        background: "var(--surface)", color: "var(--body)", cursor: "pointer",
                      }}>{s}</button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {results && !loading && (
              <div>
                <h2 style={{ fontSize: 32, marginBottom: 24 }}>Recommended for you</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
                  {results.map(dest => (
                    <div key={dest.id} className="card-hover" onClick={() => { sendFeedback(user?.uid, dest.id, "viewed"); handlePlanTrip(dest); }}
                      style={{ borderRadius: 16, overflow: "hidden", background: "var(--surface)", boxShadow: "var(--shadow-card)", cursor: "pointer" }}>
                      {/* Image */}
                      <div style={{ height: 200, position: "relative", backgroundImage: `url(${getImageUrl(dest)})`, backgroundSize: "cover", backgroundPosition: "center" }}>
                        {/* Country badge */}
                        <div style={{ position: "absolute", top: 12, left: 12, background: "rgba(255,255,255,0.85)", backdropFilter: "blur(4px)", padding: "5px 12px", borderRadius: 6, fontSize: 12, fontWeight: 500, color: "var(--dark)" }}>
                          {FLAG_MAP[dest.country] || "\u{1F30D}"} {dest.country}
                        </div>
                        {/* Visa dot */}
                        {dest.visa_info && (
                          <div style={{ position: "absolute", bottom: 12, left: 12 }}>
                            {visaBadge(dest.visa_info)}
                          </div>
                        )}
                        {/* Match bar */}
                        <div className="match-bar" style={{ width: `${Math.round(dest.match_score * 100)}%` }} />
                      </div>
                      {/* Body */}
                      <div style={{ padding: 20 }}>
                        <div style={{ display: "flex", alignItems: "start", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
                          <div>
                            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 18, fontWeight: 700, color: "var(--dark)", margin: "0 0 2px 0" }}>{dest.name.charAt(0).toUpperCase() + dest.name.slice(1)}</h3>
                            <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>{dest.country}</p>
                          </div>
                          {/* Booking.com-style score badge */}
                          <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
                            <div style={{ textAlign: "right" }}>
                              <p style={{ fontSize: 12, fontWeight: 600, color: "var(--dark)", margin: 0 }}>
                                {dest.match_score >= 0.5 ? "Excellent" : dest.match_score >= 0.3 ? "Great" : "Good"} match
                              </p>
                            </div>
                            <div style={{ width: 36, height: 36, borderRadius: "8px 8px 8px 0", background: "var(--primary)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Mono', monospace", fontWeight: 700, fontSize: 14 }}>
                              {Math.round(dest.match_score * 100)}
                            </div>
                          </div>
                        </div>
                        <p style={{ fontSize: 12, color: "var(--body)", margin: "0 0 10px 0", fontStyle: "italic" }}>{dest.match_reason}</p>
                        {dest.highlights && (
                          <p style={{ fontSize: 12, color: "var(--muted)", margin: "0 0 10px 0", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{dest.highlights}</p>
                        )}
                        <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 12 }}>
                          {dest.tags.slice(0, 4).map(t => (
                            <span key={t} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 6, background: "var(--bg)", color: "var(--body)", fontWeight: 500 }}>{t}</span>
                          ))}
                        </div>
                        {/* Trust signals */}
                        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, marginBottom: 14 }}>
                          <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700, color: "var(--primary)", fontSize: 16 }}>{"£"}{dest.avg_daily_cost_gbp}<span style={{ fontWeight: 400, fontSize: 12, color: "var(--muted)" }}>/day</span></span>
                          {dest.visa_info?.requirement === "visa-free" && <span style={{ color: "var(--success)", fontWeight: 600 }}>{"✓"} Visa free</span>}
                          {dest.visa_info?.requirement === "e-visa" && <span style={{ color: "var(--primary)", fontWeight: 600 }}>E-visa</span>}
                        </div>
                        <button onClick={e => { e.stopPropagation(); sendFeedback(user?.uid, dest.id, "saved"); handlePlanTrip(dest); }} style={{
                          width: "100%", padding: "12px 0", borderRadius: 8, border: 0, cursor: "pointer",
                          background: "var(--accent)", color: "white", fontSize: 14, fontWeight: 600,
                          fontFamily: "'DM Sans', sans-serif", transition: "opacity 200ms",
                        }}
                          onMouseEnter={e => e.currentTarget.style.opacity = "0.9"}
                          onMouseLeave={e => e.currentTarget.style.opacity = "1"}>
                          Plan This Trip
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!results && !destinationResult && !loading && !error && (
              <>
                {/* Quick AI prompts */}
                <div style={{ marginBottom: 48 }}>
                  <h2 style={{ fontSize: 28, marginBottom: 4 }}>Ask your travel concierge</h2>
                  <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 20 }}>Not sure where to start? Try one of these</p>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                    {QUICK_PROMPTS.map(p => (
                      <button key={p.text} onClick={() => handleQuickPrompt(p.text)} className="card-hover" style={{
                        display: "flex", alignItems: "center", gap: 12, padding: "16px 20px",
                        borderRadius: 12, border: "1.5px solid var(--border)", cursor: "pointer",
                        background: "var(--surface)", textAlign: "left", fontFamily: "'DM Sans', sans-serif",
                        boxShadow: "var(--shadow-card)",
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--primary)"; e.currentTarget.style.color = "var(--primary-dark)"; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--body)"; }}>
                        <span style={{ fontSize: 14, fontWeight: 500, color: "inherit" }}>{p.text}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Trending */}
                {trendingDests.length > 0 && (
                  <div>
                    <h2 style={{ fontSize: 28, marginBottom: 4 }}>Trending in {new Date().toLocaleString("default", { month: "long" })}</h2>
                    <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 20 }}>Top destinations for this month based on seasonality and popularity</p>
                    <div className="overflow-x-auto" style={{ display: "flex", gap: 16, paddingBottom: 16 }}>
                      {trendingDests.map(dest => (
                        <div key={dest.id} onClick={() => { sendFeedback(user?.uid, dest.id, "viewed"); handlePlanTrip(dest); }} className="card-hover" style={{
                          flexShrink: 0, width: 180, height: 240, borderRadius: 16,
                          overflow: "hidden", cursor: "pointer", position: "relative",
                        }}>
                          <div style={{ position: "absolute", inset: 0, backgroundImage: `url(${getImageUrl(dest)})`, backgroundSize: "cover", backgroundPosition: "center" }} />
                          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(transparent 35%, rgba(26,26,46,0.8))" }} />
                          <div style={{ position: "absolute", bottom: 14, left: 14, right: 14 }}>
                            <p style={{ color: "white", fontFamily: "'Playfair Display', serif", fontStyle: "italic", fontWeight: 600, fontSize: 16, margin: 0 }}>{dest.name.charAt(0).toUpperCase() + dest.name.slice(1)}</p>
                            <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 12, margin: "2px 0 0 0", fontFamily: "'DM Mono', monospace" }}>{"£"}{dest.avg_daily_cost_gbp}/day</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* ── UK & Day Trips ── */}
        {(tripMode === "uk" || tripMode === "daytrip") && (
          <div>
            <h2 style={{ fontSize: 28, marginBottom: 4 }}>
              {tripMode === "daytrip" ? `Day Trips from ${departure}` : "UK & Ireland Breaks"}
            </h2>
            <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 24 }}>
              {tripMode === "daytrip" ? "Back home the same night" : "No passport needed"}
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
              {(tripMode === "daytrip" ? UK_DESTINATIONS.filter(d => d.type === "daytrip") : filteredUK).map(dest => (
                <UKCard key={dest.id} dest={dest} onSelect={handlePlanTrip} />
              ))}
            </div>

            {/* Ask AI CTA */}
            <div style={{ marginTop: 48, borderRadius: 16, padding: "32px 40px", display: "flex", alignItems: "center", gap: 24, background: "var(--dark)" }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/></svg>
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ color: "white", fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 18, margin: "0 0 4px 0" }}>Want something more specific?</p>
                <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 14, margin: 0 }}>Ask your travel concierge &mdash; &ldquo;a quiet coastal walk from Bristol&rdquo;</p>
              </div>
              <button onClick={() => navigate("/chat")} style={{
                padding: "12px 24px", borderRadius: 8, border: 0, cursor: "pointer",
                background: "var(--accent)", color: "white", fontSize: 14, fontWeight: 600,
                fontFamily: "'DM Sans', sans-serif", whiteSpace: "nowrap",
              }}>Chat with AI</button>
            </div>
          </div>
        )}
      </div>

      {/* ═══ Floating multi-city bar ═══ */}
      {selected.length >= 2 && tripMode === "international" && searchMode === "recommend" && (
        <div style={{
          position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", zIndex: 50,
          background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 16,
          padding: "16px 24px", display: "flex", alignItems: "center", gap: 16, maxWidth: 640,
          boxShadow: "var(--shadow-float)",
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 14, fontWeight: 700, color: "var(--dark)", margin: 0 }}>Multi-City Trip ({selected.length} cities)</p>
            <p style={{ fontSize: 12, color: "var(--muted)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {departure} \u2192 {selected.map(s => s.name).join(" \u2192 ")} \u2192 {departure}
            </p>
          </div>
          <button onClick={handlePlanMultiCity} style={{
            padding: "10px 20px", borderRadius: 8, border: 0, cursor: "pointer",
            background: "var(--accent)", color: "white", fontSize: 14, fontWeight: 600,
            fontFamily: "'DM Sans', sans-serif", whiteSpace: "nowrap",
          }}>Plan Trip</button>
          <button onClick={() => setSelected([])} style={{ border: 0, background: "transparent", cursor: "pointer", color: "var(--muted)", fontSize: 20, lineHeight: 1 }}>\u00d7</button>
        </div>
      )}
    </div>
  );
}
