import React from 'react';
import { Activity, Wifi, Cpu } from 'lucide-react';

export default function StatusHeader({ activeGesture }) {
  return (
    <header className="flex flex-col md:flex-row justify-between items-center bg-slate-900/50 p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
      <div>
        <h1 className="text-2xl font-black tracking-tighter text-white flex items-center gap-2">
          <Cpu className="text-cyan-500" /> OMNI<span className="text-cyan-500">CONTROL</span>
        </h1>
        <p className="text-slate-400 text-xs font-mono mt-1">v1.0.4 // HYBRID HID ECOSYSTEM</p>
      </div>

      <div className="flex gap-6 mt-4 md:mt-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-bold text-slate-300 uppercase">ESP32: Online</span>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-500" />
          <span className="text-xs font-bold text-slate-300 uppercase">
            Model: {activeGesture ? `Detecting [${activeGesture.toUpperCase()}]` : 'Scanning...'}
          </span>
        </div>
      </div>
    </header>
  );
}