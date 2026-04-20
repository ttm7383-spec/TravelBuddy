import { decodeText } from "../../utils/helpers";

export default function ComparisonCard({ data }) {
  const { title, columns = [], rows = [], verdict } = data || {};
  if (!columns.length || !rows.length) return null;
  return (
    <div style={{
      background: "#FFFFFF", border: "1px solid #E5E7EB",
      borderRadius: 12, overflow: "hidden",
      boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
    }}>
      {title && (
        <div style={{
          padding: "14px 18px",
          background: "#1A1A2E", color: "white",
          fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 16,
        }}>{decodeText(title)}</div>
      )}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#1A1A2E", color: "white" }}>
              {columns.map((c, i) => (
                <th key={i} style={{
                  padding: "10px 14px", textAlign: "left",
                  fontWeight: 700, fontFamily: "'DM Sans', sans-serif",
                }}>{decodeText(c)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} style={{
                background: ri % 2 === 0 ? "#F9FAFB" : "#FFFFFF",
                borderTop: "1px solid #E5E7EB",
              }}>
                {columns.map((c, ci) => (
                  <td key={ci} style={{
                    padding: "10px 14px", color: "#1F2937",
                    fontWeight: ci === 0 ? 700 : 400,
                  }}>{decodeText(row[c] ?? row[c.toLowerCase?.()] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {verdict && (
        <div style={{
          padding: "12px 16px", margin: 14, borderRadius: 8,
          background: "#F0FDFA", borderLeft: "3px solid #00A3A3",
          color: "#0F766E", fontSize: 13, fontWeight: 500,
        }}>
          {decodeText(verdict)}
        </div>
      )}
    </div>
  );
}
