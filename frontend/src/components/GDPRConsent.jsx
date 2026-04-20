import { useEffect, useState } from "react";

const STORAGE_KEY = "gdpr_accepted";

export default function GDPRConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) setShow(true);
    } catch { /* storage may be disabled */ }
  }, []);

  if (!show) return null;

  const persist = (value) => {
    try { localStorage.setItem(STORAGE_KEY, value); } catch { /* ignore */ }
    setShow(false);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 9999,
      background: "rgba(26,26,46,0.55)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 20,
    }}>
      <div style={{
        maxWidth: 440, background: "#FFFFFF",
        borderRadius: 16, padding: "28px 28px 22px",
        boxShadow: "0 18px 50px rgba(0,0,0,0.25)",
        fontFamily: "'DM Sans', sans-serif",
      }}>
        <h2 style={{
          margin: "0 0 10px",
          fontFamily: "'Playfair Display', serif",
          fontSize: 22, fontWeight: 700, color: "#1A1A2E",
        }}>Your privacy</h2>
        <p style={{ margin: "0 0 18px", fontSize: 14, color: "#4B5563", lineHeight: 1.6 }}>
          We store your travel preferences to personalise recommendations.
          No payment data. No location tracking.
        </p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={() => persist("declined")} style={{
            padding: "10px 18px", borderRadius: 8, cursor: "pointer",
            background: "transparent", color: "#4B5563",
            border: "1px solid #E5E7EB", fontSize: 14, fontWeight: 600,
            fontFamily: "'DM Sans', sans-serif",
          }}>Decline</button>
          <button onClick={() => persist("true")} style={{
            padding: "10px 18px", borderRadius: 8, cursor: "pointer",
            background: "#00A3A3", color: "white",
            border: 0, fontSize: 14, fontWeight: 600,
            fontFamily: "'DM Sans', sans-serif",
          }}>Accept &amp; Continue</button>
        </div>
      </div>
    </div>
  );
}
