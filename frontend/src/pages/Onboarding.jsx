import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { saveProfile } from "../services/api";
import { CATEGORY_IMAGES } from "../data/destinationImages";

const PASSPORT_COUNTRIES = [
  { code: "GB", name: "United Kingdom", flag: "\u{1F1EC}\u{1F1E7}", tier: 1, visa_free: 191 },
  { code: "US", name: "United States", flag: "\u{1F1FA}\u{1F1F8}", tier: 1, visa_free: 186 },
  { code: "DE", name: "Germany", flag: "\u{1F1E9}\u{1F1EA}", tier: 1, visa_free: 193 },
  { code: "JP", name: "Japan", flag: "\u{1F1EF}\u{1F1F5}", tier: 1, visa_free: 193 },
  { code: "FR", name: "France", flag: "\u{1F1EB}\u{1F1F7}", tier: 1, visa_free: 190 },
  { code: "IT", name: "Italy", flag: "\u{1F1EE}\u{1F1F9}", tier: 1, visa_free: 190 },
  { code: "ES", name: "Spain", flag: "\u{1F1EA}\u{1F1F8}", tier: 1, visa_free: 190 },
  { code: "KR", name: "South Korea", flag: "\u{1F1F0}\u{1F1F7}", tier: 1, visa_free: 189 },
  { code: "AU", name: "Australia", flag: "\u{1F1E6}\u{1F1FA}", tier: 1, visa_free: 185 },
  { code: "CA", name: "Canada", flag: "\u{1F1E8}\u{1F1E6}", tier: 1, visa_free: 185 },
  { code: "NL", name: "Netherlands", flag: "\u{1F1F3}\u{1F1F1}", tier: 1, visa_free: 190 },
  { code: "SE", name: "Sweden", flag: "\u{1F1F8}\u{1F1EA}", tier: 1, visa_free: 190 },
  { code: "NZ", name: "New Zealand", flag: "\u{1F1F3}\u{1F1FF}", tier: 1, visa_free: 185 },
  { code: "BR", name: "Brazil", flag: "\u{1F1E7}\u{1F1F7}", tier: 2, visa_free: 170 },
  { code: "MX", name: "Mexico", flag: "\u{1F1F2}\u{1F1FD}", tier: 2, visa_free: 159 },
  { code: "AE", name: "UAE", flag: "\u{1F1E6}\u{1F1EA}", tier: 2, visa_free: 179 },
  { code: "AR", name: "Argentina", flag: "\u{1F1E6}\u{1F1F7}", tier: 2, visa_free: 170 },
  { code: "MY", name: "Malaysia", flag: "\u{1F1F2}\u{1F1FE}", tier: 2, visa_free: 177 },
  { code: "TR", name: "Turkey", flag: "\u{1F1F9}\u{1F1F7}", tier: 2, visa_free: 118 },
  { code: "ZA", name: "South Africa", flag: "\u{1F1FF}\u{1F1E6}", tier: 3, visa_free: 106 },
  { code: "IN", name: "India", flag: "\u{1F1EE}\u{1F1F3}", tier: 3, visa_free: 62 },
  { code: "CN", name: "China", flag: "\u{1F1E8}\u{1F1F3}", tier: 3, visa_free: 85 },
  { code: "PH", name: "Philippines", flag: "\u{1F1F5}\u{1F1ED}", tier: 3, visa_free: 67 },
  { code: "NG", name: "Nigeria", flag: "\u{1F1F3}\u{1F1EC}", tier: 4, visa_free: 46 },
  { code: "BD", name: "Bangladesh", flag: "\u{1F1E7}\u{1F1E9}", tier: 4, visa_free: 42 },
  { code: "PK", name: "Pakistan", flag: "\u{1F1F5}\u{1F1F0}", tier: 4, visa_free: 33 },
  { code: "EG", name: "Egypt", flag: "\u{1F1EA}\u{1F1EC}", tier: 3, visa_free: 53 },
  { code: "GH", name: "Ghana", flag: "\u{1F1EC}\u{1F1ED}", tier: 3, visa_free: 65 },
  { code: "KE", name: "Kenya", flag: "\u{1F1F0}\u{1F1EA}", tier: 3, visa_free: 73 },
  { code: "LK", name: "Sri Lanka", flag: "\u{1F1F1}\u{1F1F0}", tier: 3, visa_free: 42 },
];

const TIER_INFO = {
  1: { label: "Strong passport", desc: "Most destinations visa-free", color: "text-green-600", bg: "bg-green-50 border-green-200" },
  2: { label: "Good passport", desc: "Some visas required", color: "text-blue-600", bg: "bg-blue-50 border-blue-200" },
  3: { label: "Moderate passport", desc: "Many visas required", color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
  4: { label: "Limited passport", desc: "Plan ahead for visas", color: "text-red-600", bg: "bg-red-50 border-red-200" },
};

const BUDGET_OPTIONS = [
  { value: "low", label: "Budget", desc: "Under \u00a380/day", icon: "\u{1F4B0}" },
  { value: "medium", label: "Mid-Range", desc: "\u00a380\u2013\u00a3200/day", icon: "\u{1F48E}" },
  { value: "high", label: "Luxury", desc: "\u00a3200+/day", icon: "\u{1F451}" },
];

const STYLE_OPTIONS = [
  { value: "beach", label: "Beach", icon: "\u{1F3D6}" },
  { value: "adventure", label: "Adventure", icon: "\u{1F9D7}" },
  { value: "culture", label: "Culture", icon: "\u{1F3DB}" },
  { value: "city", label: "City", icon: "\u{1F3D9}" },
  { value: "nature", label: "Nature", icon: "\u{1F33F}" },
  { value: "nightlife", label: "Nightlife", icon: "\u{1F389}" },
  { value: "food", label: "Food & Drink", icon: "\u{1F37D}" },
  { value: "wellness", label: "Wellness", icon: "\u{1F9D8}" },
  { value: "history", label: "History", icon: "\u{1F3F0}" },
  { value: "family", label: "Family Fun", icon: "\u{1F3A0}" },
];

const GROUP_OPTIONS = [
  { value: "solo", label: "Solo", icon: "\u{1F9D1}" },
  { value: "couple", label: "Couple", icon: "\u2764" },
  { value: "family", label: "Family", icon: "\u{1F468}\u200D\u{1F469}\u200D\u{1F467}\u200D\u{1F466}" },
  { value: "friends", label: "Friends", icon: "\u{1F46F}" },
];

const DURATION_OPTIONS = [
  { value: "weekend", label: "Weekend", desc: "2\u20133 days" },
  { value: "one_week", label: "One Week", desc: "7 days" },
  { value: "two_weeks", label: "Two Weeks", desc: "14 days" },
  { value: "flexible", label: "Flexible", desc: "No fixed dates" },
];

const DIETARY_OPTIONS = [
  { value: "halal", label: "Halal", icon: "\u{1F54C}" },
  { value: "vegetarian", label: "Vegetarian", icon: "\u{1F966}" },
  { value: "vegan", label: "Vegan", icon: "\u{1F331}" },
  { value: "gluten-free", label: "Gluten-Free", icon: "\u{1F33E}" },
  { value: "kosher", label: "Kosher", icon: "\u{2721}" },
  { value: "none", label: "No Preference", icon: "\u{1F37D}" },
];

export default function Onboarding() {
  const { user, setProfile } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [passport, setPassport] = useState("");
  const [passportSearch, setPassportSearch] = useState("");
  const [budget, setBudget] = useState("");
  const [styles, setStyles] = useState([]);
  const [group, setGroup] = useState("");
  const [duration, setDuration] = useState("");
  const [dietary, setDietary] = useState([]);
  const [saving, setSaving] = useState(false);

  const selectedPassport = PASSPORT_COUNTRIES.find((p) => p.code === passport);
  const filteredPassports = passportSearch
    ? PASSPORT_COUNTRIES.filter((p) =>
        p.name.toLowerCase().includes(passportSearch.toLowerCase())
      )
    : PASSPORT_COUNTRIES;

  const toggleStyle = (val) => {
    setStyles((prev) =>
      prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val]
    );
  };

  const toggleDietary = (val) => {
    if (val === "none") {
      setDietary(["none"]);
      return;
    }
    setDietary((prev) => {
      const without_none = prev.filter((d) => d !== "none");
      return without_none.includes(val)
        ? without_none.filter((d) => d !== val)
        : [...without_none, val];
    });
  };

  const canNext = () => {
    if (step === 0) return !!passport;
    if (step === 1) return !!budget;
    if (step === 2) return styles.length > 0;
    if (step === 3) return !!group;
    if (step === 4) return !!duration;
    if (step === 5) return dietary.length > 0;
    return false;
  };

  const handleFinish = async () => {
    setSaving(true);
    const profileData = {
      name: sessionStorage.getItem("reg_name") || "",
      email: sessionStorage.getItem("reg_email") || user?.email || "",
      passport_country: passport,
      passport_tier: selectedPassport?.tier || 1,
      budget_level: budget,
      travel_style: styles,
      group_type: group,
      preferred_duration: duration,
      dietary_preferences: dietary.includes("none") ? [] : dietary,
    };
    try {
      await saveProfile(user, profileData);
      setProfile({ ...profileData, onboarding_complete: true });
      sessionStorage.removeItem("reg_name");
      sessionStorage.removeItem("reg_email");
      navigate("/dashboard");
    } catch (err) {
      console.error("Failed to save profile:", err);
      navigate("/dashboard");
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    // Step 0: Passport
    <div key="passport">
      <h2 className="text-xl font-bold text-slate-800 mb-2">Let&apos;s start with your passport</h2>
      <p className="text-slate-500 text-sm mb-6">We&apos;ll automatically check visa requirements and costs for every destination</p>

      <input
        type="text"
        placeholder="Search your country..."
        value={passportSearch}
        onChange={(e) => setPassportSearch(e.target.value)}
        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />

      <div className="max-h-48 overflow-y-auto space-y-1.5 mb-4">
        {filteredPassports.map((p) => (
          <button
            key={p.code}
            onClick={() => { setPassport(p.code); setPassportSearch(""); }}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition cursor-pointer ${
              passport === p.code
                ? "bg-indigo-50 border-2 border-indigo-500"
                : "border border-slate-200 hover:border-slate-300"
            }`}
          >
            <span className="text-xl">{p.flag}</span>
            <span className="text-sm font-medium text-slate-800">{p.name}</span>
            <span className="ml-auto text-xs text-slate-400">{p.visa_free} visa-free</span>
          </button>
        ))}
      </div>

      {selectedPassport && (
        <div className={`rounded-xl border p-4 ${TIER_INFO[selectedPassport.tier].bg}`}>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{selectedPassport.flag}</span>
            <div>
              <p className={`font-semibold text-sm ${TIER_INFO[selectedPassport.tier].color}`}>
                {TIER_INFO[selectedPassport.tier].label}
              </p>
              <p className="text-xs text-slate-600">
                {selectedPassport.visa_free} countries visa-free &middot; {TIER_INFO[selectedPassport.tier].desc}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>,
    // Step 1: Budget
    <div key="budget">
      <h2 className="text-xl font-bold text-slate-800 mb-2">What&apos;s your budget style?</h2>
      <p className="text-slate-500 text-sm mb-6">This helps us find destinations that fit your wallet</p>
      <div className="grid grid-cols-3 gap-3">
        {BUDGET_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setBudget(opt.value)}
            className={`p-4 rounded-xl border-2 text-center transition cursor-pointer ${
              budget === opt.value
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="text-2xl mb-1">{opt.icon}</div>
            <div className="font-semibold text-slate-800 text-sm">{opt.label}</div>
            <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
          </button>
        ))}
      </div>
    </div>,
    // Step 2: Style
    <div key="style">
      <h2 className="text-xl font-bold text-slate-800 mb-2">What do you love about travel?</h2>
      <p className="text-slate-500 text-sm mb-6">Pick as many as you like</p>
      <div className="grid grid-cols-3 gap-3">
        {STYLE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => toggleStyle(opt.value)}
            className={`rounded-xl border-2 text-center transition cursor-pointer overflow-hidden relative ${
              styles.includes(opt.value)
                ? "border-indigo-500"
                : "border-slate-200 hover:border-slate-300"
            }`}
            style={{ height: 100 }}
          >
            <div className="absolute inset-0" style={{ backgroundImage: `url(${CATEGORY_IMAGES[opt.value]})`, backgroundSize: "cover", backgroundPosition: "center" }} />
            <div className="absolute inset-0" style={{ background: styles.includes(opt.value) ? "rgba(79,70,229,0.5)" : "rgba(0,0,0,0.4)" }} />
            <div className="relative z-10 flex flex-col items-center justify-center h-full">
              <div className="text-2xl mb-1">{opt.icon}</div>
              <div className="font-semibold text-white text-sm">{opt.label}</div>
            </div>
          </button>
        ))}
      </div>
    </div>,
    // Step 3: Group
    <div key="group">
      <h2 className="text-xl font-bold text-slate-800 mb-2">Who are you travelling with?</h2>
      <p className="text-slate-500 text-sm mb-6">We&apos;ll tailor recommendations to your group</p>
      <div className="grid grid-cols-2 gap-3">
        {GROUP_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setGroup(opt.value)}
            className={`p-4 rounded-xl border-2 text-center transition cursor-pointer ${
              group === opt.value
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="text-2xl mb-1">{opt.icon}</div>
            <div className="font-semibold text-slate-800 text-sm">{opt.label}</div>
          </button>
        ))}
      </div>
    </div>,
    // Step 4: Duration
    <div key="duration">
      <h2 className="text-xl font-bold text-slate-800 mb-2">How long do you like to travel?</h2>
      <p className="text-slate-500 text-sm mb-6">Your ideal trip length</p>
      <div className="grid grid-cols-2 gap-3">
        {DURATION_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setDuration(opt.value)}
            className={`p-4 rounded-xl border-2 text-center transition cursor-pointer ${
              duration === opt.value
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="font-semibold text-slate-800 text-sm">{opt.label}</div>
            <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
          </button>
        ))}
      </div>
    </div>,
    // Step 5: Dietary
    <div key="dietary">
      <h2 className="text-xl font-bold text-slate-800 mb-2">Any dietary needs?</h2>
      <p className="text-slate-500 text-sm mb-6">We&apos;ll find restaurants that match your diet at every destination</p>
      <div className="grid grid-cols-3 gap-3">
        {DIETARY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => toggleDietary(opt.value)}
            className={`p-4 rounded-xl border-2 text-center transition cursor-pointer ${
              dietary.includes(opt.value)
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="text-2xl mb-1">{opt.icon}</div>
            <div className="font-semibold text-slate-800 text-sm">{opt.label}</div>
          </button>
        ))}
      </div>
    </div>,
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-sky-50 px-4">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-lg p-8">
        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full ${
                i <= step ? "bg-indigo-500" : "bg-slate-200"
              }`}
            />
          ))}
        </div>

        {steps[step]}

        <div className="flex justify-between mt-8">
          <button
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 0}
            className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 disabled:invisible cursor-pointer"
          >
            Back
          </button>
          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canNext()}
              className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-40 cursor-pointer"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleFinish}
              disabled={!canNext() || saving}
              className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-40 cursor-pointer"
            >
              {saving ? "Saving..." : "Let's Go!"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
