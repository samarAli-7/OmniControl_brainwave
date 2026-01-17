// utils/jsonSync.js - Auto-syncs Firebase mappings to JSON file
import { ref, onValue, set } from "firebase/database";
import { db } from '../firebase';

let jsonSyncInterval;

export const startJsonSync = (jsonFilePath = './gesture_mappings.json') => {
  // Listen for Firebase changes
  onValue(ref(db, 'settings/mappings'), async (snapshot) => {
    const mappings = snapshot.val() || {};
    
    // Format for CNN backend
    const jsonData = {
      timestamp: Date.now(),
      version: '1.0',
      mappings: mappings,
      active: true
    };
    
    try {
      // Write to JSON file (your friend's agent will handle this endpoint)
      await fetch('/api/sync-mappings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jsonData)
      });
      
      console.log('✅ JSON synced:', jsonData);
    } catch (error) {
      console.error('JSON sync failed:', error);
    }
  }, { onlyOnce: false });
};

// Auto-start on app load
export const initJsonSync = () => {
  if (!jsonSyncInterval) {
    startJsonSync();
  }
};
