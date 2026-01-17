import React from 'react';

const CalibrationMode = ({ data }) => {
  const exercises = [
    { name: 'UP', color: 'from-cyan-500 to-blue-500', progress: 25 },
    { name: 'DOWN', color: 'from-blue-500 to-indigo-500', progress: 50 },
    { name: 'LEFT', color: 'from-indigo-500 to-purple-500', progress: 75 },
    { name: 'RIGHT', color: 'from-purple-500 to-pink-500', progress: 100 }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* HEADER */}
      <div className="flex items-center justify-center gap-6 mb-16">
        <div className="w-20 h-20 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl border-2 border-cyan-500/30 p-4 flex items-center justify-center">
          <span className="text-2xl font-black text-cyan-400">C</span>
        </div>
        <div>
          <h2 className="text-4xl font-black tracking-widest text-white uppercase mb-2">USER CALIBRATION</h2>
          <div className={`text-xl font-mono tracking-widest ${
            data.status === 'running' ? 'text-cyan-400' : 
            data.status === 'complete' ? 'text-emerald-400' : 'text-zinc-500'
          }`}>
            STATUS: {data.status?.toUpperCase() || 'IDLE'}
          </div>
        </div>
      </div>

      {/* PROGRESS BAR */}
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between text-sm font-mono text-zinc-400 mb-4 uppercase tracking-wider">
          <span>NOISE PROFILE ACQUISITION</span>
          <span>{Math.round(data.progress || 0)}%</span>
        </div>
        <div className="w-full bg-zinc-900/50 rounded-2xl h-3 overflow-hidden border border-zinc-700/50">
          <div 
            className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 rounded-2xl shadow-lg transition-all duration-1000"
            style={{ width: `${data.progress || 0}%` }}
          />
        </div>
      </div>

      {/* EXERCISES GRID */}
      <div className="grid grid-cols-2 gap-8">
        {exercises.map((exercise, idx) => {
          const isComplete = (data.progress || 0) >= exercise.progress;
          const isActive = data.status === 'running' && Math.floor((data.progress || 0) / 25) === idx;
          
          return (
            <div key={exercise.name} className="group">
              <div className={`p-8 rounded-2xl border-2 transition-all duration-500 hover:scale-[1.02] ${
                isComplete 
                  ? 'border-emerald-500/50 bg-emerald-950/30 shadow-2xl shadow-emerald-500/20' 
                  : isActive 
                  ? 'border-cyan-500/70 bg-cyan-950/40 shadow-2xl shadow-cyan-500/30 scale-105 animate-pulse' 
                  : 'border-zinc-800/50 bg-zinc-950/20 hover:border-zinc-600 hover:shadow-xl hover:shadow-zinc-500/20'
              }`}>
                <div className="text-center">
                  <div className="text-lg font-bold text-zinc-400 mb-4 uppercase tracking-wider">
                    {exercise.name}
                  </div>
                  <div className={`text-3xl font-black mb-4 ${
                    isComplete ? 'text-emerald-400' : 
                    isActive ? 'bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent' : 
                    'text-zinc-600'
                  }`}>
                    {isComplete ? '✓ COMPLETE' : isActive ? '● ACTIVE' : '○ WAITING'}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CalibrationMode;
