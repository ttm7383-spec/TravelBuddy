import { decodeText } from "../../utils/helpers";

export default function ListCard({ data }) {
  const { title, items = [] } = data || {};
  if (!items.length) return null;
  return (
    <div style={{
      background: "#FFFFFF", border: "1px solid #E5E7EB",
      borderRadius: 12, padding: 16,
      boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
    }}>
      {title && (
        <h3 style={{
          margin: "0 0 12px", fontFamily: "'Playfair Display', serif",
          fontSize: 17, fontWeight: 700, color: "#1A1A2E",
        }}>{decodeText(title)}</h3>
      )}
      <ol style={{ margin: 0, padding: 0, listStyle: "none" }}>
        {items.map((item, i) => (
          <li key={i} style={{
            display: "flex", gap: 12, padding: "10px 0",
            borderTop: i === 0 ? "none" : "1px solid #F3F4F6",
          }}>
            <div style={{
              flexShrink: 0, width: 24, height: 24, borderRadius: 6,
              background: "#00A3A3", color: "white",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 12, fontWeight: 700, fontFamily: "'DM Sans', sans-serif",
            }}>{i + 1}</div>
            <div style={{ flex: 1 }}>
              {item.name && (
                <p style={{ margin: 0, fontWeight: 700, color: "#1A1A2E", fontSize: 14 }}>
                  {decodeText(item.name)}
                </p>
              )}
              {item.description && (
                <p style={{ margin: "2px 0 0", fontSize: 13, color: "#4B5563", lineHeight: 1.5 }}>
                  {decodeText(item.description)}
                </p>
              )}
              {item.best_for && (
                <p style={{ margin: "4px 0 0", fontSize: 12, color: "#6B7280" }}>
                  Best for: {decodeText(item.best_for)}
                </p>
              )}
              {item.tip && (
                <p style={{
                  margin: "6px 0 0", fontSize: 12, color: "#D97706",
                  fontStyle: "italic",
                }}>{decodeText(item.tip)}</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
