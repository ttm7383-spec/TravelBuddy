import { useEffect, useMemo, useRef, useState } from "react";
import { WORLD_COUNTRIES, WORLD_CITIES } from "../data/worldPlaces";

// Free-form place input with spelling-based suggestions from a bundled list
// of world countries and major cities. Extra cities can be passed via the
// `extraCities` prop (e.g., destinations from the backend DB). The user can
// always submit any free-form text — suggestions are assistive only.
export default function PlaceAutocomplete({
  value, onChange, placeholder = "City or country", extraCities = [],
  inputStyle, maxSuggestions = 8,
}) {
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const wrapperRef = useRef(null);

  const allCities = useMemo(() => {
    const seen = new Set();
    const merged = [];
    const push = (name, country) => {
      const key = name.toLowerCase();
      if (!name || seen.has(key)) return;
      seen.add(key);
      merged.push({ name, country: country || "" });
    };
    for (const c of WORLD_CITIES) push(c.city, c.country);
    for (const d of extraCities) push(d.name, d.country);
    return merged;
  }, [extraCities]);

  const suggestions = useMemo(() => {
    const q = (value || "").trim().toLowerCase();
    if (!q) return [];
    const prefixCountries = [];
    const containsCountries = [];
    for (const c of WORLD_COUNTRIES) {
      const lc = c.toLowerCase();
      if (lc.startsWith(q)) prefixCountries.push({ name: c, kind: "country" });
      else if (lc.includes(q)) containsCountries.push({ name: c, kind: "country" });
    }
    const prefixCities = [];
    const containsCities = [];
    for (const c of allCities) {
      const lc = c.name.toLowerCase();
      if (lc.startsWith(q)) prefixCities.push({ name: c.name, kind: "city", sub: c.country });
      else if (lc.includes(q)) containsCities.push({ name: c.name, kind: "city", sub: c.country });
    }
    // Prefix-matches first (cities then countries — cities are more specific),
    // then contains-matches (for typo/mid-word matches).
    return [...prefixCities, ...prefixCountries, ...containsCities, ...containsCountries]
      .slice(0, maxSuggestions);
  }, [value, allCities, maxSuggestions]);

  useEffect(() => {
    const handler = e => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const pick = s => { onChange(s.name); setOpen(false); setActiveIdx(-1); };

  const handleKeyDown = e => {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx(i => Math.min(suggestions.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx(i => Math.max(-1, i - 1));
    } else if (e.key === "Enter" && activeIdx >= 0) {
      e.preventDefault();
      pick(suggestions[activeIdx]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const baseInputStyle = {
    width: "100%", border: 0, padding: 0, fontSize: 15, fontWeight: 600,
    color: "var(--dark)", fontFamily: "'DM Sans', sans-serif", background: "transparent",
    outline: "none",
  };

  return (
    <div ref={wrapperRef} style={{ position: "relative" }}>
      <input
        type="text"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); setActiveIdx(-1); }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        style={{ ...baseInputStyle, ...(inputStyle || {}) }}
      />
      {open && suggestions.length > 0 && (
        <div
          style={{
            position: "absolute", top: "calc(100% + 6px)", left: -12, right: -12,
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, boxShadow: "var(--shadow-float)", zIndex: 30,
            maxHeight: 280, overflowY: "auto", fontFamily: "'DM Sans', sans-serif",
          }}
        >
          {suggestions.map((s, i) => (
            <div
              key={`${s.kind}-${s.name}-${i}`}
              onMouseDown={() => pick(s)}
              onMouseEnter={() => setActiveIdx(i)}
              style={{
                padding: "10px 14px", cursor: "pointer", fontSize: 14,
                display: "flex", justifyContent: "space-between", alignItems: "center",
                gap: 12, borderBottom: "1px solid var(--border)",
                background: activeIdx === i ? "var(--bg)" : "transparent",
              }}
            >
              <span style={{ color: "var(--dark)", fontWeight: 500 }}>{s.name}</span>
              <span
                style={{
                  fontSize: 11, color: "var(--muted)", textTransform: "uppercase",
                  letterSpacing: "0.04em", flexShrink: 0,
                }}
              >
                {s.kind === "city" ? (s.sub || "City") : "Country"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
