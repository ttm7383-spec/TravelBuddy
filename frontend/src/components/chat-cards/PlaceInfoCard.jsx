import { decodeText, unsplashImage, onImgError, toTitleCase } from "../../utils/helpers";

export default function PlaceInfoCard({ data }) {
  const {
    name, category, about, image_keyword,
    quick_facts = [], best_time, local_tip,
    nearby = [], cost, map_url, book_url,
  } = data || {};

  const heroSrc = unsplashImage(image_keyword || name, 800);

  return (
    <div style={{
      background: "#FFFFFF", border: "1px solid #E5E7EB",
      borderRadius: 12, overflow: "hidden",
      boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
    }}>
      {/* Hero */}
      <div style={{ position: "relative", height: 180 }}>
        <img src={heroSrc} onError={onImgError} alt={name}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
        <div style={{
          position: "absolute", inset: 0,
          background: "linear-gradient(transparent 40%, rgba(0,0,0,0.75))",
        }} />
        <div style={{ position: "absolute", bottom: 12, left: 14, right: 14, color: "white" }}>
          <p style={{
            margin: 0, fontFamily: "'Playfair Display', serif",
            fontWeight: 700, fontSize: 20,
          }}>{decodeText(toTitleCase(name || ""))}</p>
          {category && (
            <p style={{ margin: "2px 0 0", fontSize: 12, opacity: 0.85 }}>
              {decodeText(category)}
            </p>
          )}
        </div>
      </div>

      <div style={{ padding: "14px 18px" }}>
        {about && (
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: "#1F2937" }}>
            {decodeText(about)}
          </p>
        )}

        {quick_facts.length > 0 && (
          <div style={{
            marginTop: 12,
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8,
          }}>
            {quick_facts.map((f, i) => (
              <div key={i} style={{
                background: "#F9FAFB", borderRadius: 8, padding: "8px 10px",
              }}>
                <p style={{ margin: 0, fontSize: 11, color: "#6B7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.3px" }}>
                  {decodeText(f.label || "")}
                </p>
                <p style={{ margin: "2px 0 0", fontSize: 13, color: "#1A1A2E", fontWeight: 500 }}>
                  {decodeText(f.value || "")}
                </p>
              </div>
            ))}
          </div>
        )}

        {best_time && (
          <div style={{
            marginTop: 12, padding: "10px 12px", borderRadius: 8,
            background: "#F0FDFA", borderLeft: "3px solid #00A3A3",
            fontSize: 13, color: "#0F766E",
          }}>
            <strong style={{ marginRight: 6 }}>Best time:</strong>{decodeText(best_time)}
          </div>
        )}
        {local_tip && (
          <div style={{
            marginTop: 10, padding: "10px 12px", borderRadius: 8,
            background: "#FFF7ED", borderLeft: "3px solid #FF6B2B",
            fontSize: 13, color: "#9A3412", fontStyle: "italic",
          }}>{decodeText(local_tip)}</div>
        )}

        {nearby.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <p style={{
              margin: "0 0 6px", fontSize: 11, fontWeight: 700,
              textTransform: "uppercase", letterSpacing: "0.5px", color: "#6B7280",
            }}>Nearby</p>
            <ul style={{ margin: 0, paddingLeft: 18, color: "#1F2937", fontSize: 13 }}>
              {nearby.map((n, i) => (
                <li key={i}>{decodeText(typeof n === "string" ? n : n.name)}</li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 10 }}>
          {cost && (
            <span style={{
              fontFamily: "'DM Mono', monospace", fontWeight: 700,
              fontSize: 16, color: "#00A3A3",
            }}>{decodeText(cost)}</span>
          )}
          <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
            {book_url && (
              <a href={book_url} target="_blank" rel="noopener noreferrer" style={{
                padding: "8px 14px", borderRadius: 8, fontSize: 13,
                fontWeight: 600, background: "#FF6B2B", color: "white",
                textDecoration: "none",
              }}>Book</a>
            )}
            {map_url && (
              <a href={map_url} target="_blank" rel="noopener noreferrer" style={{
                padding: "8px 14px", borderRadius: 8, fontSize: 13,
                fontWeight: 600, background: "#00A3A3", color: "white",
                textDecoration: "none",
              }}>Map</a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
