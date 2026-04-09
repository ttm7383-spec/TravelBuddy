import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { sendChatMessage } from "../services/api";
import {
  OverviewCard, ItineraryCard, HotelCard, FoodCard,
  FlightCard, VisaCard, BudgetCard, TipsCard, WeatherCard,
} from "../components/chat-cards";
import SkeletonCard from "../components/chat-cards/SkeletonCard";

/* ── Card renderer map ── */
const CARD_MAP = {
  overview: OverviewCard,
  itinerary: ItineraryCard,
  hotel: HotelCard,
  food: FoodCard,
  flight: FlightCard,
  visa: VisaCard,
  budget: BudgetCard,
  tips: TipsCard,
  weather: WeatherCard,
};

/* ── Rotating placeholders ── */
const PLACEHOLDERS = [
  "Plan 5 days in Tokyo...",
  "Best street food in Bangkok?",
  "Hotels in Paris under £100...",
  "Flights to Bali from London...",
  "Budget for 7 days in Morocco...",
  "Tell me about Istanbul...",
  "Where should I go in December?",
  "Visa info for India...",
  "Tips for solo travel in Colombia...",
  "What's the weather like in Iceland?",
];

/* ── Welcome suggestions ── */
const WELCOME_PILLS = [
  "Plan 3 days in Tokyo",
  "Tell me about Marrakech",
  "Hotels in Barcelona",
  "Best food in Bangkok",
  "Where should I go?",
  "Budget for Bali",
];

export default function Chat() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Rotate placeholder text
  useEffect(() => {
    const timer = setInterval(() => {
      setPlaceholderIdx(i => (i + 1) % PLACEHOLDERS.length);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(user, msg);
      setMessages(prev => [...prev, {
        role: "assistant",
        cards: res.cards || [],
        suggestions: res.suggestions || [],
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        cards: [{
          type: "overview",
          data: {
            city: "Oops",
            country: "",
            description: err.message || "Something went wrong. Please try again.",
            vibes: [],
            highlights: [],
          },
        }],
        suggestions: ["Try again", "Plan a trip to Paris"],
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading, user]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderCards = (cards) =>
    cards.map((card, i) => {
      const Component = CARD_MAP[card.type];
      if (!Component) return null;
      return <Component key={i} data={card.data} />;
    });

  const showWelcome = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 64px)" }}>
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">

          {/* Welcome screen */}
          {showWelcome && (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">✈️</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Where do you want to go?
              </h2>
              <p className="text-gray-500 mb-8 max-w-md mx-auto">
                Ask me about any city on Earth — I'll give you hotels, food spots,
                itineraries, budgets, visa info, and more.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {WELCOME_PILLS.map((pill, i) => (
                  <button key={i} onClick={() => handleSend(pill)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-400 hover:text-blue-600 transition cursor-pointer">
                    {pill}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message list */}
          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === "user" ? (
                /* User bubble */
                <div className="flex justify-end">
                  <div className="max-w-md px-4 py-3 rounded-2xl rounded-br-md text-white text-sm"
                    style={{ background: "linear-gradient(135deg, #0066FF 0%, #4F46E5 100%)" }}>
                    {msg.content}
                  </div>
                </div>
              ) : (
                /* Assistant cards */
                <div className="space-y-3">
                  {msg.cards && renderCards(msg.cards)}
                  {/* Follow-up pills */}
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {msg.suggestions.map((s, j) => (
                        <button key={j} onClick={() => handleSend(s)}
                          className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs text-gray-600 hover:border-blue-400 hover:text-blue-600 transition cursor-pointer">
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Loading skeletons */}
          {loading && (
            <div className="space-y-3">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={PLACEHOLDERS[placeholderIdx]}
            className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl text-white text-sm font-semibold transition disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed border-0"
            style={{ background: "linear-gradient(135deg, #0066FF 0%, #4F46E5 100%)" }}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
