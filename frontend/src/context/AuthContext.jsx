import { createContext, useContext, useState, useEffect } from "react";
import { onAuthChange, logoutUser } from "../services/firebase";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined); // undefined = loading
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const unsub = onAuthChange((u) => {
      setUser(u || null);
    });
    return unsub;
  }, []);

  const logout = async () => {
    await logoutUser();
    setUser(null);
    setProfile(null);
  };

  if (user === undefined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, profile, setProfile, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
