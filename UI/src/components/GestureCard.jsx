import React from 'react';
import { Activity } from 'lucide-react';

export default function GestureCard({ name, isActive, currentAction, actions, onMap }) {
  // Pattern IDs for specific gestures
  const getPatternID = (n) => {
    if (n === 'spiderman') return '#SPD-88';
    if (n === 'rock_on') return '#RCK-72';
    return `#G-00${n.length}`;
  };

  return (
    <div className={`tactical-panel p-[2.5vh] h-[35vh] flex flex-col justify-between relative overflow-hidden transition-all
      ${isActive ? 'active-warning scale-[1.03] z-10 bg-amber-500/5' : 'opacity-60 border-zinc-900 grayscale hover:grayscale-0 hover:opacity-100'}`}>
      
      {isActive && <div className="scan-line" />}
      
      <div>
        <div className="flex justify-between items-start mb-[1.5vh]">
          <span className={`text-[1vh] font-bold px-2 py-0.5 rounded-sm ${isActive ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-500'}`}>
            {isActive ? 'SIGNAL_IN' : 'STANDBY'}
          </span>
          <span className="text-[0.8vh] text-amber-500/30 font-bold">{getPatternID(name)}</span>
        </div>
        
        <h3 className={`text-[2.8vh] font-black uppercase tracking-tighter italic leading-[1.1] transition-colors 
          ${isActive ? 'text-white' : 'text-zinc-500'}`}>
          {name.replace('_', ' ')}
        </h3>
      </div>

      <div className="space-y-[1vh]">
        <label className="text-[0.8vh] text-zinc-600 font-bold tracking-[0.2em]">LOGIC_BINDING</label>
        <div className="relative">
          <select
            value={currentAction || 'none'}
            onChange={(e) => onMap(e.target.value)}
            className="w-full bg-black border border-zinc-800 text-amber-500 text-[1.2vh] font-bold p-[1vh] outline-none focus:border-amber-500 transition-colors appearance-none cursor-pointer"
          >
            {actions.map(action => (
              <option key={action.id} value={action.id} className="bg-zinc-950">{action.label}</option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-amber-500 text-[1vh]">▼</div>
        </div>
      </div>
    </div>
  );
}