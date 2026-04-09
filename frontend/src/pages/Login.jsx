import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../services/firebase";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginUser(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)" }}>
      {/* Left side — branding */}
      <div className="hidden lg:flex flex-1 flex-col justify-center px-16 text-white">
        <div className="text-5xl mb-4">✈️</div>
        <h1 className="text-4xl font-extrabold mb-3" style={{ lineHeight: 1.2 }}>
          Your next adventure<br />starts here
        </h1>
        <p className="text-lg text-white/60 max-w-md">
          Personalised trips, real-time prices, visa checks — all in one place.
        </p>
        <div className="flex gap-6 mt-8">
          {[["80+", "Destinations"], ["10", "Passport support"], ["Live", "Flight prices"]].map(([val, label]) => (
            <div key={label}>
              <div className="text-2xl font-extrabold">{val}</div>
              <div className="text-xs text-white/50">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right side — form */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-md bg-white rounded-3xl p-10" style={{ boxShadow: "0 25px 60px rgba(0,0,0,0.3)" }}>
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 mb-4">
              <span className="text-2xl">✈️</span>
              <span className="text-xl font-extrabold"><span style={{ color: "#0066FF" }}>Travel</span><span style={{ color: "#1A1A2E" }}>Buddy</span></span>
            </div>
            <h2 className="text-2xl font-extrabold text-gray-900">Welcome back</h2>
            <p className="text-gray-500 text-sm mt-1">Sign in to plan your next trip</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 text-sm rounded-xl p-3 mb-5 text-center">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                placeholder="Enter your password" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full text-white py-3.5 rounded-xl font-bold text-base border-0 cursor-pointer disabled:opacity-50 transition"
              style={{ background: "linear-gradient(90deg, #0066FF, #00BFFF)" }}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : "Sign In"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Don&apos;t have an account?{" "}
              <Link to="/register" className="text-blue-600 font-semibold hover:underline no-underline">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
