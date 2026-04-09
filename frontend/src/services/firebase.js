import { initializeApp } from "firebase/app";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Check if Firebase is configured (has a real API key)
const isFirebaseConfigured =
  firebaseConfig.apiKey && firebaseConfig.apiKey !== "your_firebase_api_key";

let app = null;
let auth = null;

if (isFirebaseConfigured) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
}

export { auth, isFirebaseConfigured };

// In demo mode, we use a simple listener system so login/register
// can notify the AuthContext that the user changed.
let _demoAuthCallback = null;

function _buildDemoUser(email) {
  return {
    uid: "demo-user-001",
    email,
    getIdToken: async () => "demo-token",
  };
}

function _notifyDemoAuth(user) {
  if (_demoAuthCallback) _demoAuthCallback(user);
}

export async function registerUser(email, password) {
  if (!isFirebaseConfigured) {
    const demoUser = _buildDemoUser(email);
    localStorage.setItem("demo_user", JSON.stringify({ uid: demoUser.uid, email }));
    _notifyDemoAuth(demoUser);
    return demoUser;
  }
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  return cred.user;
}

export async function loginUser(email, password) {
  if (!isFirebaseConfigured) {
    const demoUser = _buildDemoUser(email);
    localStorage.setItem("demo_user", JSON.stringify({ uid: demoUser.uid, email }));
    _notifyDemoAuth(demoUser);
    return demoUser;
  }
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

export async function logoutUser() {
  if (!isFirebaseConfigured) {
    localStorage.removeItem("demo_user");
    _notifyDemoAuth(null);
    return;
  }
  await signOut(auth);
}

export function onAuthChange(callback) {
  if (!isFirebaseConfigured) {
    // Store the callback so login/register/logout can trigger it
    _demoAuthCallback = callback;

    // Check if already logged in from a previous session
    const stored = localStorage.getItem("demo_user");
    if (stored) {
      const parsed = JSON.parse(stored);
      callback(_buildDemoUser(parsed.email));
    } else {
      callback(null);
    }

    return () => { _demoAuthCallback = null; };
  }
  return onAuthStateChanged(auth, callback);
}
