import { decodeText } from "../../utils/helpers";

export default function ItineraryUpdateCard({ data }) {
  const { summary, activities = [] } = data || {};
  return (
    <div style={{
      background: "#FFFFFF", border: "1px solid #E5E7EB",
      borderRadius: 12, overflow: "hidden",
      boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
    }}>
      <div style={{
        padding: "14px 18px",
        background: "linear-gradient(135deg, #00A3A3 0%, #1A1A2E 100%)",
        color: "white",
      }}>
        <p style={{
          margin: 0, fontFamily: "'Playfair Display', serif",
          fontWeight: 700, fontSize: 16,
        }}>Itinerary Updated</p>
        {summary && (
          <p style={{ margin: "4px 0 0", fontSize: 13, opacity: 0.85 }}>
            {decodeText(summary)}
          </p>
        )}
      </div>
      <div style={{ padding: "12px 16px" }}>
        {activities.map((a, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, padding: "10px 0",
            borderTop: i === 0 ? "none" : "1px solid #F3F4F6",
          }}>
            <div style={{
              flexShrink: 0, minWidth: 56,
              fontFamily: "'DM Mono', monospace", fontWeight: 700,
              fontSize: 13, color: "#00A3A3",
            }}>{decodeText(a.time || "")}</div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1A1A2E" }}>
                {decodeText(a.activity || a.name || "")}
              </p>
              {a.transport && (
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "#4B5563" }}>
                  {decodeText(a.transport)}
                </p>
              )}
              {a.cost && (
                <p style={{
                  margin: "2px 0 0", fontSize: 12,
                  fontFamily: "'DM Mono', monospace", color: "#0F766E", fontWeight: 600,
                }}>{decodeText(a.cost)}</p>
              )}
              {a.tip && (
                <p style={{
                  margin: "4px 0 0", fontSize: 12, color: "#D97706",
                  fontStyle: "italic",
                }}>{decodeText(a.tip)}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
