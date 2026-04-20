import { decodeText } from "../../utils/helpers";

export default function TextCard({ data }) {
  const { message, followup_question } = data || {};
  if (!message && !followup_question) return null;
  return (
    <div style={{
      background: "#FFFFFF",
      borderLeft: "4px solid #00A3A3",
      borderTop: "1px solid #E5E7EB",
      borderRight: "1px solid #E5E7EB",
      borderBottom: "1px solid #E5E7EB",
      borderRadius: 10,
      padding: "14px 16px",
      boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
    }}>
      {message && (
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: "#1F2937" }}>
          {decodeText(message)}
        </p>
      )}
      {followup_question && (
        <p style={{
          margin: "10px 0 0", fontSize: 13, color: "#00A3A3",
          fontStyle: "italic", fontWeight: 500,
        }}>
          {decodeText(followup_question)}
        </p>
      )}
    </div>
  );
}
