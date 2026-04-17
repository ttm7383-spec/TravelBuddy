import { useState, useRef, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (dropRef.current && !dropRef.current.contains(e.target)) setShowDropdown(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  if (!user) return null;

  const initials = (profile?.name || user?.email || "U").slice(0, 2).toUpperCase();
  const isActive = (path) => location.pathname === path;

  const navLink = (to, label) => (
    <Link to={to}
      className="no-underline transition-all"
      style={{
        fontSize: 14,
        fontWeight: 500,
        fontFamily: "'DM Sans', sans-serif",
        color: isActive(to) ? "var(--primary)" : "var(--body)",
        borderBottom: isActive(to) ? "2px solid var(--primary)" : "2px solid transparent",
        paddingBottom: 4,
      }}
      onMouseEnter={e => { if (!isActive(to)) e.currentTarget.style.color = "var(--primary-dark)"; }}
      onMouseLeave={e => { if (!isActive(to)) e.currentTarget.style.color = "var(--body)"; }}
    >
      {label}
    </Link>
  );

  return (
    <nav style={{
      background: "var(--surface)",
      borderBottom: "1px solid var(--border)",
      position: "sticky",
      top: 0,
      zIndex: 50,
      boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
    }}>
      <div style={{
        maxWidth: 1120,
        margin: "0 auto",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 64,
      }}>
        {/* Logo */}
        <Link to="/dashboard" className="no-underline" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Compass SVG icon */}
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: "var(--primary)", display: "flex",
            alignItems: "center", justifyContent: "center",
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="white" stroke="white"/>
            </svg>
          </div>
          <span style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 22, fontWeight: 700, color: "var(--dark)",
          }}>
            Travel<span style={{ color: "var(--primary)" }}>Buddy</span>
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          {navLink("/dashboard", "Explore")}
          {navLink("/chat", "AI Concierge")}
          {navLink("/history", "My Trips")}

          {/* Avatar */}
          <div className="relative" ref={dropRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                width: 36, height: 36, borderRadius: 8,
                background: "var(--primary-light)", color: "var(--primary-dark)",
                border: "1.5px solid var(--border)",
                fontSize: 13, fontWeight: 700,
                fontFamily: "'DM Sans', sans-serif",
                cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              {initials}
            </button>
            {showDropdown && (
              <div style={{
                position: "absolute", right: 0, marginTop: 8, width: 192,
                background: "var(--surface)", borderRadius: 12,
                boxShadow: "var(--shadow-lifted)", border: "1px solid var(--border)",
                padding: "8px 0", zIndex: 50,
              }}>
                <Link to="/profile" onClick={() => setShowDropdown(false)}
                  className="no-underline"
                  style={{
                    display: "block", padding: "10px 16px",
                    fontSize: 14, color: "var(--body)",
                    fontFamily: "'DM Sans', sans-serif",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--bg)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  Profile & Settings
                </Link>
                <button onClick={handleLogout}
                  style={{
                    width: "100%", textAlign: "left", padding: "10px 16px",
                    fontSize: 14, color: "#E53E3E",
                    fontFamily: "'DM Sans', sans-serif",
                    border: 0, background: "transparent", cursor: "pointer",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "#FFF5F5"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
