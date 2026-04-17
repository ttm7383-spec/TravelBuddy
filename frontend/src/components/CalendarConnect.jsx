import { useState, useEffect } from "react";
import { getCalendarAuthUrl, getCalendarWindows, disconnectCalendar } from "../services/api";

/**
 * CalendarConnect — Google Calendar integration component
 *
 * Shows below date inputs in the Dashboard search card.
 * Lets users connect Google Calendar, view free travel windows,
 * and click a window to auto-fill dates in the search form.
 */
export default function CalendarConnect({ user, onWindowSelect }) {
  const [status, setStatus] = useState("checking"); // checking | not_connected | loading | connected | error
  const [windows, setWindows] = useState([]);
  const [nextWeekend, setNextWeekend] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(null);

  useEffect(() => {
    if (!user) {
      setStatus("not_connected");
      return;
    }
    // Check if user has calendar connected by fetching windows
    fetchWindows();
  }, [user]);

  const fetchWindows = async () => {
    setStatus("loading");
    try {
      const data = await getCalendarWindows(user);
      if (data.connected) {
        setWindows(data.windows || []);
        setNextWeekend(data.next_free_weekend || null);
        setStatus("connected");
      } else {
        setStatus("not_connected");
      }
    } catch {
      setStatus("not_connected");
    }
  };

  const handleConnect = async () => {
    try {
      const data = await getCalendarAuthUrl(user);
      if (data.auth_url) {
        window.location.href = data.auth_url;
      }
    } catch {
      setStatus("error");
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectCalendar(user);
      setStatus("not_connected");
      setWindows([]);
      setNextWeekend(null);
      setSelectedIdx(null);
    } catch {
      // Ignore disconnect errors
    }
  };

  const handleWindowClick = (win, idx) => {
    setSelectedIdx(idx);
    if (onWindowSelect) {
      onWindowSelect(win.start, win.end);
    }
  };

  const formatChipLabel = (win) => {
    const start = new Date(win.start + "T00:00:00");
    const end = new Date(win.end + "T00:00:00");
    const startDay = start.getDate();
    const endDay = end.getDate();
    const startMonth = start.toLocaleDateString("en-GB", { month: "short" });
    const endMonth = end.toLocaleDateString("en-GB", { month: "short" });
    const dateRange = startMonth === endMonth
      ? `${startDay}-${endDay} ${startMonth}`
      : `${startDay} ${startMonth}-${endDay} ${endMonth}`;
    return `${win.duration_days} days · ${dateRange}`;
  };

  // ── Not connected state ──
  if (status === "not_connected" || status === "error") {
    return (
      <div style={styles.container}>
        <div style={styles.banner}>
          <span style={{ fontSize: 16 }}>📅</span>
          <span style={{ color: "#6C757D", fontSize: 13, fontWeight: 500, fontFamily: "'DM Sans', sans-serif" }}>
            Connect Google Calendar to auto-find your free dates
          </span>
        </div>
        <button onClick={handleConnect} style={styles.connectBtn}
          onMouseEnter={e => e.currentTarget.style.background = "#E6F7F7"}
          onMouseLeave={e => e.currentTarget.style.background = "white"}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00B4D8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          Connect Google Calendar
        </button>
        {status === "error" && (
          <div style={{ color: "#DC3545", fontSize: 12, marginTop: 8, fontFamily: "'DM Sans', sans-serif" }}>
            Could not connect. Check your Google Calendar setup.
          </div>
        )}
      </div>
    );
  }

  // ── Loading state ──
  if (status === "loading" || status === "checking") {
    return (
      <div style={styles.container}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ display: "inline-block", animation: "spin 1s linear infinite", fontSize: 16 }}>📅</span>
          <span style={{ color: "#6C757D", fontSize: 13, fontWeight: 500, fontFamily: "'DM Sans', sans-serif" }}>
            Checking your calendar...
          </span>
        </div>
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  // ── Connected state ──
  return (
    <div style={styles.container}>
      {windows.length > 0 && (
        <>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#6C757D", marginBottom: 10, fontFamily: "'DM Sans', sans-serif", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Your free windows
          </div>
          <div style={styles.chipScroll}>
            {windows.map((win, idx) => (
              <button key={idx} onClick={() => handleWindowClick(win, idx)}
                style={{
                  ...styles.chip,
                  ...(selectedIdx === idx ? styles.chipSelected : styles.chipDefault),
                }}
                onMouseEnter={e => {
                  if (selectedIdx !== idx) {
                    e.currentTarget.style.borderColor = "#00B4D8";
                    e.currentTarget.style.color = "#00B4D8";
                  }
                }}
                onMouseLeave={e => {
                  if (selectedIdx !== idx) {
                    e.currentTarget.style.borderColor = "#E9ECEF";
                    e.currentTarget.style.color = "#495057";
                  }
                }}>
                🗓️ {formatChipLabel(win)}
              </button>
            ))}
          </div>
        </>
      )}

      {windows.length === 0 && (
        <div style={{ fontSize: 13, color: "#6C757D", fontFamily: "'DM Sans', sans-serif" }}>
          No free windows found in the next 90 days.
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 10 }}>
        {nextWeekend && (
          <span style={{ fontSize: 12, color: "#ADB5BD", fontFamily: "'DM Sans', sans-serif" }}>
            Next free weekend: {new Date(nextWeekend + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
          </span>
        )}
        <button onClick={handleDisconnect}
          style={styles.disconnectBtn}
          onMouseEnter={e => e.currentTarget.style.color = "#DC3545"}
          onMouseLeave={e => e.currentTarget.style.color = "#ADB5BD"}>
          Disconnect
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    borderTop: "1px solid #E9ECEF",
    paddingTop: 16,
    marginTop: 8,
  },
  banner: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  connectBtn: {
    border: "1.5px solid #00B4D8",
    color: "#00B4D8",
    background: "white",
    borderRadius: 10,
    padding: "8px 16px",
    fontSize: 13,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
    display: "flex",
    alignItems: "center",
    gap: 8,
    cursor: "pointer",
    transition: "background 200ms",
  },
  chipScroll: {
    display: "flex",
    gap: 8,
    overflowX: "auto",
    paddingBottom: 4,
  },
  chip: {
    borderRadius: 20,
    padding: "6px 14px",
    fontSize: 12,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
    cursor: "pointer",
    whiteSpace: "nowrap",
    border: "1.5px solid",
    transition: "all 200ms",
  },
  chipDefault: {
    background: "white",
    borderColor: "#E9ECEF",
    color: "#495057",
  },
  chipSelected: {
    background: "#00B4D8",
    color: "white",
    borderColor: "#00B4D8",
  },
  disconnectBtn: {
    background: "none",
    border: "none",
    color: "#ADB5BD",
    fontSize: 12,
    fontFamily: "'DM Sans', sans-serif",
    cursor: "pointer",
    padding: 0,
    transition: "color 200ms",
  },
};
