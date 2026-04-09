import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();
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

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50" style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between" style={{ height: 64 }}>
        <Link to="/dashboard" className="flex items-center gap-2 no-underline">
          <span className="text-2xl">✈️</span>
          <span style={{ fontSize: 22, fontWeight: 800 }}>
            <span style={{ color: "#0066FF" }}>Travel</span>
            <span style={{ color: "#1A1A2E" }}>Buddy</span>
          </span>
        </Link>
        <div className="flex items-center gap-5">
          <Link to="/dashboard" className="text-sm text-gray-600 hover:text-blue-600 transition no-underline font-medium">
            Dashboard
          </Link>
          <Link to="/chat" className="text-sm text-gray-600 hover:text-blue-600 transition no-underline font-medium flex items-center gap-1">
            💬 AI Chat
          </Link>
          <Link to="/history" className="text-sm text-gray-600 hover:text-blue-600 transition no-underline font-medium flex items-center gap-1">
            📋 My Trips
          </Link>
          <div className="relative" ref={dropRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold cursor-pointer border-0"
              style={{ background: "#0066FF", fontSize: 14 }}
            >
              {initials}
            </button>
            {showDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-200 py-2 z-50">
                <Link to="/profile" onClick={() => setShowDropdown(false)}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline">
                  👤 Profile
                </Link>
                <button onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-50 border-0 bg-transparent cursor-pointer">
                  🚪 Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
