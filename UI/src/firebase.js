import { initializeApp, getApps, getApp } from "firebase/app";
import { getDatabase } from "firebase/database";
import { getAnalytics } from "firebase/analytics";


const firebaseConfig = {
  apiKey: "AIzaSyCO1oiJtsqRZcIw0iwE83jtjBAf1ZOQR3k",
  authDomain: "omnicontrol-2.firebaseapp.com",
  databaseURL: "https://omnicontrol-2-default-rtdb.firebaseio.com",
  projectId: "omnicontrol-2",
  storageBucket: "omnicontrol-2.firebasestorage.app",
  messagingSenderId: "371690956860",
  appId: "1:371690956860:web:ed66267201df2565e5fb39",
  measurementId: "G-FG2S2GKW1S"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// // Prevent multiple initializations during Hot Module Replacement (HMR)
// const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const db = getDatabase(app);