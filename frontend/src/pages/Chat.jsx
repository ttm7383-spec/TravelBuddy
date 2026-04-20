import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useSearchParams, useNavigate } from "react-router-dom";
import { sendChatMessage } from "../services/api";
import {
  OverviewCard, ItineraryCard, HotelCard, FoodCard,
  FlightCard, VisaCard, BudgetCard, TipsCard, WeatherCard,
  TextCard, ListCard, ComparisonCard, ItineraryUpdateCard, PlaceInfoCard,
} from "../components/chat-cards";
import SkeletonCard from "../components/chat-cards/SkeletonCard";

const CARD_MAP = {
  overview: OverviewCard, itinerary: ItineraryCard, hotel: HotelCard, food: FoodCard,
  flight: FlightCard, visa: VisaCard, budget: BudgetCard, tips: TipsCard, weather: WeatherCard,
  text: TextCard, list: ListCard, comparison: ComparisonCard,
  itinerary_update: ItineraryUpdateCard, place_info: PlaceInfoCard,
};

const PLACEHOLDERS = [
  "Plan 5 days in Tokyo\u2026", "Day trip from London this weekend?", "Best street food in Bangkok?",
  "Hotels in Paris under \u00a3100\u2026", "Weekend in Edinburgh?", "Where should I go in December?",
  "Visa info for India\u2026", "Tips for solo travel in Colombia\u2026", "Hidden gems in the Cotswolds?",
];

const WELCOME_CATEGORIES = [
  { label: "\u{1F1EC}\u{1F1E7} UK BREAKS", pills: ["Weekend in Edinburgh", "Day trip from London", "Bath & Bristol", "Cornwall coast"] },
  { label: "\u{1F30D} EUROPE", pills: ["3 days in Prague", "Lisbon on a budget", "Greek islands", "Hidden gems in Portugal"] },
  { label: "\u{1F4B7} BUDGET EUROPE", pills: ["Cheapest European cities", "Eastern Europe on \u00a350/day", "Free things in Amsterdam", "Budget Barcelona"] },
  { label: "\u{1F37D}\u{FE0F} FOOD & CULTURE", pills: ["Best food city in Europe", "Wine regions in France", "Street food in Istanbul", "Hidden restaurants in Rome"] },
];

/* ═══ SVG compass icon ═══ */
function CompassIcon({ size = 20, bg = true }) {
  const inner = (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/>
    </svg>
  );
  if (!bg) return inner;
  return (
    <div style={{ width: size + 14, height: size + 14, borderRadius: "50%", background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      {inner}
    </div>
  );
}

/* ═══ Sub-components ═══ */

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "end", gap: 8 }}>
      <CompassIcon size={16} />
      <div style={{ padding: "12px 16px", borderRadius: "16px 16px 16px 4px", background: "var(--surface)", boxShadow: "var(--shadow-card)", display: "flex", alignItems: "center", gap: 5 }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--muted)", display: "inline-block", animation: "bounce 1.2s infinite", animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  );
}

function UserBubble({ content, time }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "end", gap: 8 }}>
      <div style={{ maxWidth: 380 }}>
        <div style={{ padding: "12px 18px", borderRadius: "16px 16px 4px 16px", background: "var(--primary)", color: "white", fontSize: 14, lineHeight: 1.6, fontFamily: "'DM Sans', sans-serif" }}>
          {content}
        </div>
        {time && <p style={{ fontSize: 10, color: "var(--muted)", textAlign: "right", margin: "4px 0 0" }}>{time}</p>}
      </div>
    </div>
  );
}

function AssistantMessage({ reply, cards, suggestions, onSend, time }) {
  const renderCards = (cards) => cards.map((card, i) => { const C = CARD_MAP[card.type]; return C ? <C key={i} data={card.data} /> : null; });
  return (
    <div style={{ display: "flex", alignItems: "start", gap: 8 }}>
      <div style={{ marginTop: 4 }}><CompassIcon size={16} /></div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, maxWidth: 640 }}>
        {reply && (
          <div style={{
            padding: "12px 16px", borderRadius: "16px 16px 16px 4px",
            background: "var(--surface)", boxShadow: "var(--shadow-card)",
            fontSize: 14, lineHeight: 1.6, color: "var(--dark)",
            fontFamily: "'DM Sans', sans-serif", whiteSpace: "pre-wrap",
          }}>
            {reply}
          </div>
        )}
        {cards && renderCards(cards)}
        {suggestions && suggestions.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, paddingLeft: 4, paddingTop: 4 }}>
            {suggestions.map((s, j) => (
              <button key={j} onClick={() => onSend(s)} style={{
                padding: "6px 14px", borderRadius: 6, fontSize: 12, fontWeight: 500,
                fontFamily: "'DM Sans', sans-serif", border: "1.5px solid var(--border)",
                background: "var(--surface)", color: "var(--body)", cursor: "pointer",
                transition: "all 150ms",
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--primary)"; e.currentTarget.style.color = "var(--primary)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--body)"; }}>
                {s}
              </button>
            ))}
          </div>
        )}
        {time && <p style={{ fontSize: 10, color: "var(--muted)", paddingLeft: 4, margin: 0 }}>{time}</p>}
      </div>
    </div>
  );
}

function WelcomeScreen({ onSend }) {
  return (
    <div style={{ padding: "48px 8px" }}>
      <div style={{ textAlign: "center", marginBottom: 40 }}>
        <div style={{ width: 64, height: 64, borderRadius: 16, background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/></svg>
        </div>
        <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--dark)", margin: "0 0 8px" }}>
          Your personal travel concierge
        </h2>
        <p style={{ fontSize: 15, color: "var(--muted)", margin: 0, maxWidth: 400, marginLeft: "auto", marginRight: "auto", lineHeight: 1.65 }}>
          Ask me anything &mdash; from a day trip to Brighton to a month across Southeast Asia.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 520, margin: "0 auto" }}>
        {WELCOME_CATEGORIES.map((cat, ci) => (
          <div key={ci}>
            <p className="label-uppercase" style={{ marginBottom: 8 }}>{cat.label}</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {cat.pills.map((pill, pi) => (
                <button key={pi} onClick={() => onSend(pill)} className="card-hover" style={{
                  padding: "10px 18px", borderRadius: 8, border: 0, cursor: "pointer",
                  background: "var(--surface)", color: "var(--body)",
                  boxShadow: "var(--shadow-card)", fontSize: 14, fontWeight: 500,
                  fontFamily: "'DM Sans', sans-serif", transition: "all 200ms",
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderLeft = "3px solid var(--primary)"; e.currentTarget.style.color = "var(--primary-dark)"; e.currentTarget.style.paddingLeft = "15px"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderLeft = "0"; e.currentTarget.style.color = "var(--body)"; e.currentTarget.style.paddingLeft = "18px"; }}>
                  {pill}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p style={{ textAlign: "center", fontSize: 12, color: "var(--muted)", marginTop: 40, margin: "40px 0 0" }}>
        Try asking in plain English &mdash; &ldquo;what should I do in Lisbon for 3 days with \u00a3500?&rdquo;
      </p>
    </div>
  );
}

/* ═══ Main Component ═══ */

export default function Chat() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [hasSentQueryParam, setHasSentQueryParam] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [tripContext, setTripContext] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { const t = setInterval(() => setPlaceholderIdx(i => (i + 1) % PLACEHOLDERS.length), 3000); return () => clearInterval(t); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !hasSentQueryParam) { setHasSentQueryParam(true); setTimeout(() => { handleSend(q); navigate("/chat", { replace: true }); }, 300); }
  }, [searchParams]); // eslint-disable-line

  const getTime = () => new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });

  const handleSend = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    const time = getTime();
    setMessages(prev => [...prev, { role: "user", content: msg, time }]);
    setLoading(true);
    try {
      const res = await sendChatMessage(user, msg, sessionId, conversationHistory, tripContext);
      if (res.session_id) setSessionId(res.session_id);
      if (res.trip_context) setTripContext(res.trip_context);
      setConversationHistory(prev => [
        ...prev,
        { role: "user", content: msg },
        { role: "assistant", content: res.reply || "" },
      ].slice(-20));
      setMessages(prev => [...prev, { role: "assistant", reply: res.reply || "", cards: res.cards || [], suggestions: res.suggestions || [], time: getTime() }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        reply: err.message || "I had trouble with that one. Could you rephrase?",
        cards: [],
        suggestions: ["Try again", "Plan a trip to Tokyo", "Weekend in Edinburgh"],
        time: getTime(),
      }]);
    } finally { setLoading(false); inputRef.current?.focus(); }
  }, [input, loading, user, sessionId, conversationHistory, tripContext]);

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } };
  const showWelcome = messages.length === 0 && !loading;

  return (
    <>
      <style>{`@keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }`}</style>

      <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>

        {/* Trip context banner */}
        {tripContext?.destination && (
          <div style={{
            background: "#F0FDFA", borderBottom: "1px solid #CCFBF1",
            padding: "10px 16px", display: "flex", alignItems: "center", gap: 10, justifyContent: "center",
          }}>
            <span style={{ fontSize: 13, color: "#0F766E", fontWeight: 600 }}>
              Current trip: {tripContext.destination}
              {tripContext.days ? ` \u00b7 ${tripContext.days} days` : ""}
              {tripContext.budget ? ` \u00b7 \u00a3${tripContext.budget}` : ""}
              {tripContext.group ? ` \u00b7 ${tripContext.group}` : ""}
            </span>
            <button onClick={() => { setTripContext(null); setConversationHistory([]); }} style={{
              border: 0, background: "transparent", cursor: "pointer",
              color: "#0F766E", fontSize: 13, fontWeight: 600,
            }}>Clear</button>
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px", display: "flex", flexDirection: "column", gap: 24 }}>
            {showWelcome && <WelcomeScreen onSend={handleSend} />}
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.role === "user"
                  ? <UserBubble content={msg.content} time={msg.time} />
                  : <AssistantMessage reply={msg.reply} cards={msg.cards} suggestions={msg.suggestions} onSend={handleSend} time={msg.time} />}
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <TypingIndicator />
                <div style={{ paddingLeft: 42, display: "flex", flexDirection: "column", gap: 12 }}>
                  <SkeletonCard /><SkeletonCard />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input bar */}
        <div style={{ borderTop: "1px solid var(--border)", background: "var(--surface)", padding: "16px 16px", boxShadow: "0 -2px 12px rgba(0,0,0,0.04)" }}>
          <div style={{ maxWidth: 720, margin: "0 auto" }}>
            {/* Quick chips */}
            {messages.length > 0 && (
              <div className="overflow-x-auto" style={{ display: "flex", gap: 6, paddingBottom: 10 }}>
                {["Day trip ideas", "Change budget", "Where to eat", "Hotel options", "Visa info", "What to pack"].map((chip, i) => (
                  <button key={i} onClick={() => handleSend(chip)} style={{
                    flexShrink: 0, padding: "5px 12px", borderRadius: 6, fontSize: 12, fontWeight: 500,
                    fontFamily: "'DM Sans', sans-serif", border: "1px solid var(--border)",
                    background: "var(--bg)", color: "var(--muted)", cursor: "pointer", transition: "all 150ms",
                  }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--primary)"; e.currentTarget.style.color = "var(--primary)"; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--muted)"; }}>
                    {chip}
                  </button>
                ))}
              </div>
            )}

            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button onClick={() => navigate("/dashboard")} style={{
                width: 40, height: 40, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
                border: "1.5px solid var(--border)", background: "var(--surface)", cursor: "pointer", flexShrink: 0,
              }} title="Back to Dashboard">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--body)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              </button>

              <div style={{
                flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "10px 16px",
                borderRadius: 10, border: "1.5px solid var(--border)", background: "var(--surface)",
                transition: "border-color 200ms",
              }}
                onFocus={e => e.currentTarget.style.borderColor = "var(--primary)"}
                onBlur={e => e.currentTarget.style.borderColor = "var(--border)"}>
                <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                  placeholder={PLACEHOLDERS[placeholderIdx]}
                  style={{ flex: 1, border: 0, fontSize: 14, color: "var(--dark)", fontFamily: "'DM Sans', sans-serif", background: "transparent", minWidth: 0 }} />
                {input && (
                  <button onClick={() => setInput("")} style={{ border: 0, background: "transparent", cursor: "pointer", color: "var(--muted)", fontSize: 18, lineHeight: 1, flexShrink: 0 }}>\u00d7</button>
                )}
              </div>

              <button onClick={() => handleSend()} disabled={loading || !input.trim()} style={{
                width: 44, height: 44, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                border: 0, cursor: "pointer", background: "var(--primary)", color: "white", flexShrink: 0,
                opacity: (loading || !input.trim()) ? 0.4 : 1, transition: "opacity 200ms",
              }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              </button>
            </div>

            <p style={{ textAlign: "center", fontSize: 10, color: "var(--muted)", margin: "8px 0 0" }}>Your personal travel concierge &middot; Ask anything</p>
          </div>
        </div>
      </div>
    </>
  );
}
