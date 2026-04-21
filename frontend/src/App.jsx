import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import GDPRConsent from "./components/GDPRConsent";

// Eager-load only the auth pages; everything else is code-split so the
// initial bundle stays small.
import Login from "./pages/Login";
import Register from "./pages/Register";

const Onboarding = lazy(() => import("./pages/Onboarding"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Itinerary = lazy(() => import("./pages/Itinerary"));
const MultiCityItinerary = lazy(() => import("./pages/MultiCityItinerary"));
const History = lazy(() => import("./pages/History"));
const Profile = lazy(() => import("./pages/Profile"));
const Chat = lazy(() => import("./pages/Chat"));
const MyTrips = lazy(() => import("./pages/MyTrips"));

function RouteFallback() {
  return (
    <div style={{
      minHeight: "60vh",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'DM Sans', sans-serif", color: "var(--muted)",
    }}>
      <span style={{
        width: 32, height: 32, borderRadius: "50%",
        border: "3px solid #E5E7EB", borderTopColor: "#00A3A3",
        animation: "spin 800ms linear infinite", display: "inline-block",
      }} />
      <style>{"@keyframes spin { to { transform: rotate(360deg); } }"}</style>
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      <Navbar />
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <Register />} />

          {/* Protected routes */}
          <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/itinerary/multi" element={<ProtectedRoute><MultiCityItinerary /></ProtectedRoute>} />
          <Route path="/itinerary/:destinationId" element={<ProtectedRoute><Itinerary /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/my-trips" element={<ProtectedRoute><MyTrips /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </Suspense>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-slate-50">
          <GDPRConsent />
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
