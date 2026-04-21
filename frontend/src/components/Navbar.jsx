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
        fontFamily: "var(--font-body)",
        fontSize: 14,
        fontWeight: 400,
        color: isActive(to) ? "var(--seafoam)" : "var(--muted)",
        letterSpacing: "0.2px",
        paddingBottom: 4,
        borderBottom: isActive(to) ? "2px solid var(--seafoam)" : "2px solid transparent",
      }}
      onMouseEnter={e => { if (!isActive(to)) e.currentTarget.style.color = "var(--seafoam)"; }}
      onMouseLeave={e => { if (!isActive(to)) e.currentTarget.style.color = "var(--muted)"; }}
    >
      {label}
    </Link>
  );

  return (
    <nav style={{
      background: "rgba(10,22,40,0.85)",
      backdropFilter: "blur(16px)",
      WebkitBackdropFilter: "blur(16px)",
      borderBottom: "1px solid var(--glass-border)",
      position: "sticky",
      top: 0,
      zIndex: 50,
    }}>
      <div style={{
        maxWidth: 1200, margin: "0 auto",
        padding: "0 28px", height: 68,
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        {/* Logo */}
        <Link to="/dashboard" className="no-underline" style={{
          display: "flex", alignItems: "center", gap: 10, color: "inherit",
        }}>
          <span style={{ fontSize: 22, lineHeight: 1 }} role="img" aria-label="wave">{"\uD83C\uDF0A"}</span>
          <span style={{ fontSize: 24, lineHeight: 1, display: "inline-flex", alignItems: "baseline", gap: 2 }}>
            <span style={{
              fontFamily: "var(--font-display)", fontStyle: "italic",
              fontWeight: 700, color: "var(--white)",
            }}>Travel</span>
            <span style={{
              fontFamily: "var(--font-body)", fontWeight: 600,
              color: "var(--seafoam)", letterSpacing: "-0.2px",
            }}>Buddy</span>
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          {navLink("/dashboard", "Explore")}
          {navLink("/chat", "AI Concierge")}
          {navLink("/my-trips", "My Trips")}
          {navLink("/history", "History")}

          <button onClick={() => navigate("/dashboard")} style={{
            background: "linear-gradient(135deg, var(--sunset), var(--coral))",
            color: "var(--white)",
            border: 0,
            padding: "8px 20px",
            borderRadius: 100,
            fontFamily: "var(--font-body)",
            fontWeight: 600,
            fontSize: 13,
            boxShadow: "var(--shadow-sunset)",
            transition: "transform 150ms ease, filter 150ms ease",
          }}
            onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.03)"; e.currentTarget.style.filter = "brightness(1.05)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.filter = "none"; }}
          >
            Plan a Trip
          </button>

          {/* Avatar */}
          <div className="relative" ref={dropRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                width: 38, height: 38, borderRadius: "50%",
                background: "var(--ocean-blue)",
                color: "var(--seafoam)",
                border: "1px solid var(--glass-border)",
                fontSize: 13, fontWeight: 700,
                fontFamily: "var(--font-body)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              {initials}
            </button>
            {showDropdown && (
              <div style={{
                position: "absolute", right: 0, marginTop: 10, width: 200,
                background: "var(--midnight-blue)",
                borderRadius: 12,
                boxShadow: "var(--shadow-medium)",
                border: "1px solid var(--glass-border)",
                padding: "6px 0",
                zIndex: 60,
              }}>
                <Link to="/profile" onClick={() => setShowDropdown(false)}
                  className="no-underline"
                  style={{
                    display: "block", padding: "10px 18px",
                    fontSize: 14, color: "var(--white)",
                    fontFamily: "var(--font-body)",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--ocean-dark)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  Profile & Settings
                </Link>
                <button onClick={handleLogout}
                  style={{
                    width: "100%", textAlign: "left", padding: "10px 18px",
                    fontSize: 14, color: "var(--coral)",
                    fontFamily: "var(--font-body)",
                    border: 0, background: "transparent",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "rgba(231,111,81,0.08)"}
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
