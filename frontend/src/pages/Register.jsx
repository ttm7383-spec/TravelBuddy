import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../services/firebase";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 6) { setError("Password must be at least 6 characters"); return; }
    setLoading(true);
    try {
      await registerUser(email, password);
      sessionStorage.setItem("reg_name", name);
      sessionStorage.setItem("reg_email", email);
      navigate("/onboarding");
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)" }}>
      {/* Left side — branding */}
      <div className="hidden lg:flex flex-1 flex-col justify-center px-16 text-white">
        <div className="text-5xl mb-4">🌍</div>
        <h1 className="text-4xl font-extrabold mb-3" style={{ lineHeight: 1.2 }}>
          Plan trips that<br />actually fit you
        </h1>
        <p className="text-lg text-white/60 max-w-md">
          Tell us your budget, style and passport — we&apos;ll do the rest.
        </p>
        <div className="flex gap-4 mt-8">
          {["🏖️ Beach", "🧗 Adventure", "🏛️ Culture", "🌿 Nature"].map((t) => (
            <div key={t} className="bg-white/10 backdrop-blur px-3 py-2 rounded-full text-xs font-medium">{t}</div>
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
            <h2 className="text-2xl font-extrabold text-gray-900">Create your account</h2>
            <p className="text-gray-500 text-sm mt-1">Start planning your next adventure</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 text-sm rounded-xl p-3 mb-5 text-center">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Full Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} required
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                placeholder="Your name" />
            </div>
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
                placeholder="At least 6 characters" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full text-white py-3.5 rounded-xl font-bold text-base border-0 cursor-pointer disabled:opacity-50 transition"
              style={{ background: "linear-gradient(90deg, #0066FF, #00BFFF)" }}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account...
                </span>
              ) : "Create Account"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Already have an account?{" "}
              <Link to="/login" className="text-blue-600 font-semibold hover:underline no-underline">Sign In</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
