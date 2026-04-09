import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { saveProfile, getProfile, checkVisa } from "../services/api";

const BUDGET_OPTIONS = [
  { value: "low", label: "Budget", desc: "Under \u00a380/day" },
  { value: "medium", label: "Mid-Range", desc: "\u00a380\u2013\u00a3200/day" },
  { value: "high", label: "Luxury", desc: "\u00a3200+/day" },
];

const STYLE_OPTIONS = ["beach", "adventure", "culture", "city", "nature", "nightlife"];
const GROUP_OPTIONS = ["solo", "couple", "family", "friends"];
const DURATION_OPTIONS = [
  { value: "weekend", label: "Weekend (2-3 days)" },
  { value: "one_week", label: "One Week" },
  { value: "two_weeks", label: "Two Weeks" },
  { value: "flexible", label: "Flexible" },
];

const PASSPORT_COUNTRIES = [
  { code: "GB", name: "United Kingdom", flag: "\uD83C\uDDEC\uD83C\uDDE7", tier: 1, visa_free: 191 },
  { code: "US", name: "United States", flag: "\uD83C\uDDFA\uD83C\uDDF8", tier: 1, visa_free: 186 },
  { code: "DE", name: "Germany", flag: "\uD83C\uDDE9\uD83C\uDDEA", tier: 1, visa_free: 193 },
  { code: "JP", name: "Japan", flag: "\uD83C\uDDEF\uD83C\uDDF5", tier: 1, visa_free: 193 },
  { code: "FR", name: "France", flag: "\uD83C\uDDEB\uD83C\uDDF7", tier: 1, visa_free: 190 },
  { code: "IN", name: "India", flag: "\uD83C\uDDEE\uD83C\uDDF3", tier: 3, visa_free: 62 },
  { code: "CN", name: "China", flag: "\uD83C\uDDE8\uD83C\uDDF3", tier: 3, visa_free: 85 },
  { code: "NG", name: "Nigeria", flag: "\uD83C\uDDF3\uD83C\uDDEC", tier: 4, visa_free: 46 },
  { code: "PK", name: "Pakistan", flag: "\uD83C\uDDF5\uD83C\uDDF0", tier: 4, visa_free: 33 },
  { code: "BR", name: "Brazil", flag: "\uD83C\uDDE7\uD83C\uDDF7", tier: 2, visa_free: 170 },
  { code: "ZA", name: "South Africa", flag: "\uD83C\uDDFF\uD83C\uDDE6", tier: 3, visa_free: 106 },
  { code: "AU", name: "Australia", flag: "\uD83C\uDDE6\uD83C\uDDFA", tier: 1, visa_free: 185 },
  { code: "PH", name: "Philippines", flag: "\uD83C\uDDF5\uD83C\uDDED", tier: 3, visa_free: 67 },
  { code: "BD", name: "Bangladesh", flag: "\uD83C\uDDE7\uD83C\uDDE9", tier: 4, visa_free: 42 },
];

const TIER_LABELS = {
  1: { label: "Strong", color: "bg-green-100 text-green-700" },
  2: { label: "Good", color: "bg-blue-100 text-blue-700" },
  3: { label: "Moderate", color: "bg-amber-100 text-amber-700" },
  4: { label: "Limited", color: "bg-red-100 text-red-700" },
};

export default function Profile() {
  const { user, profile, setProfile } = useAuth();
  const [budget, setBudget] = useState("medium");
  const [styles, setStyles] = useState([]);
  const [group, setGroup] = useState("solo");
  const [duration, setDuration] = useState("one_week");
  const [passportCode, setPassportCode] = useState("GB");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  // Quick visa checker
  const [visaDest, setVisaDest] = useState("");
  const [visaResult, setVisaResult] = useState(null);
  const [visaChecking, setVisaChecking] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getProfile(user);
        if (data.profile) {
          setBudget(data.profile.budget_level || "medium");
          setStyles(data.profile.travel_style || []);
          setGroup(data.profile.group_type || "solo");
          setDuration(data.profile.preferred_duration || "one_week");
          setPassportCode(data.profile.passport_country || "GB");
          setProfile(data.profile);
        }
      } catch {
        // Use defaults
      } finally {
        setLoading(false);
      }
    }
    if (profile) {
      setBudget(profile.budget_level || "medium");
      setStyles(profile.travel_style || []);
      setGroup(profile.group_type || "solo");
      setDuration(profile.preferred_duration || "one_week");
      setPassportCode(profile.passport_country || "GB");
      setLoading(false);
    } else {
      load();
    }
  }, []);

  const selectedPassport = PASSPORT_COUNTRIES.find((p) => p.code === passportCode);

  const toggleStyle = (val) => {
    setStyles((prev) =>
      prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    try {
      const profileData = {
        email: user?.email || "",
        budget_level: budget,
        travel_style: styles,
        group_type: group,
        preferred_duration: duration,
        passport_country: passportCode,
        passport_tier: selectedPassport?.tier || 1,
      };
      await saveProfile(user, profileData);
      setProfile({ ...profileData, onboarding_complete: true });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleVisaCheck = async () => {
    if (!visaDest.trim()) return;
    setVisaChecking(true);
    setVisaResult(null);
    try {
      const result = await checkVisa(passportCode, visaDest.trim());
      setVisaResult(result);
    } catch {
      setVisaResult({ requirement: "unknown", recommendation: "Could not check. Try a different country name." });
    } finally {
      setVisaChecking(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Your Profile</h1>
      <p className="text-slate-500 text-sm mb-8">Update your travel preferences and passport</p>

      {/* Travel Documents Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-8">
        <h2 className="font-bold text-slate-800 mb-4">Travel Documents</h2>
        <div className="flex items-center gap-4 mb-4">
          {selectedPassport && (
            <div className="flex items-center gap-3">
              <span className="text-3xl">{selectedPassport.flag}</span>
              <div>
                <p className="font-medium text-slate-800">{selectedPassport.name} Passport</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TIER_LABELS[selectedPassport.tier]?.color}`}>
                    {TIER_LABELS[selectedPassport.tier]?.label}
                  </span>
                  <span className="text-xs text-slate-500">{selectedPassport.visa_free} countries visa-free</span>
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="mb-4">
          <label className="block text-xs font-medium text-slate-500 mb-1">Change passport</label>
          <select
            value={passportCode}
            onChange={(e) => setPassportCode(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {PASSPORT_COUNTRIES.map((p) => (
              <option key={p.code} value={p.code}>{p.flag} {p.name}</option>
            ))}
          </select>
        </div>

        {/* Quick Visa Checker */}
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs font-medium text-slate-600 mb-2">Quick Visa Checker</p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter a country (e.g. France)"
              value={visaDest}
              onChange={(e) => setVisaDest(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleVisaCheck()}
              className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleVisaCheck}
              disabled={visaChecking}
              className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
            >
              {visaChecking ? "..." : "Check"}
            </button>
          </div>
          {visaResult && (
            <div className="mt-2 text-sm">
              <span className={`font-medium ${
                visaResult.requirement === "visa-free" ? "text-green-600" :
                visaResult.requirement === "visa-on-arrival" ? "text-blue-600" :
                visaResult.requirement === "e-visa" ? "text-blue-600" : "text-amber-600"
              }`}>
                {visaResult.requirement}
              </span>
              {visaResult.cost_gbp > 0 && <span className="text-slate-500"> &middot; &pound;{visaResult.cost_gbp}</span>}
              {visaResult.recommendation && (
                <p className="text-xs text-slate-500 mt-1">{visaResult.recommendation}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Budget */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">Budget Level</label>
        <div className="grid grid-cols-3 gap-3">
          {BUDGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setBudget(opt.value)}
              className={`p-3 rounded-lg border-2 text-center text-sm transition cursor-pointer ${
                budget === opt.value
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="font-semibold text-slate-800">{opt.label}</div>
              <div className="text-xs text-slate-500">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Travel Styles */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">Travel Styles</label>
        <div className="flex flex-wrap gap-2">
          {STYLE_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => toggleStyle(s)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition cursor-pointer ${
                styles.includes(s)
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Group Type */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">Usually travel as</label>
        <div className="flex gap-2">
          {GROUP_OPTIONS.map((g) => (
            <button
              key={g}
              onClick={() => setGroup(g)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition cursor-pointer ${
                group === g
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* Duration */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-slate-700 mb-2">Preferred trip length</label>
        <div className="grid grid-cols-2 gap-2">
          {DURATION_OPTIONS.map((d) => (
            <button
              key={d.value}
              onClick={() => setDuration(d.value)}
              className={`px-4 py-2 rounded-lg border-2 text-sm transition cursor-pointer ${
                duration === d.value
                  ? "border-indigo-500 bg-indigo-50 font-medium"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition disabled:opacity-50 cursor-pointer"
      >
        {saving ? "Saving..." : "Save Changes"}
      </button>

      {success && (
        <div className="mt-4 bg-green-50 text-green-600 text-sm rounded-lg p-3 text-center">
          Preferences saved successfully!
        </div>
      )}
    </div>
  );
}
