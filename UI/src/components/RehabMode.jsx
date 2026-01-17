import React from 'react';

const RehabMode = ({ data }) => {
  const stages = [
    { name: 'BASIC', color: 'from-emerald-500 to-teal-500', stageNum: 1 },
    { name: 'INTERMEDIATE', color: 'from-teal-500 to-sky-500', stageNum: 2 },
    { name: 'ADVANCED', color: 'from-sky-500 to-purple-500', stageNum: 3 },
    { name: 'FULL CONTROL', color: 'from-purple-500 to-pink-500', stageNum: 4 }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-12">
      {/* HEADER */}
      <div className="flex items-center justify-center gap-6 mb-16">
        <div className="w-20 h-20 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl border-2 border-purple-500/30 p-4 flex items-center justify-center">
          <span className="text-2xl font-black text-purple-400">R</span>
        </div>
        <div>
          <h2 className="text-4xl font-black tracking-widest text-white uppercase mb-2">REHAB TRAINING</h2>
          <div className="text-xl font-mono tracking-widest text-purple-400">
            STAGE {data.stage || 1} / 4 • {Math.round(data.progress || 0)}% COMPLETE
          </div>
        </div>
      </div>

      {/* NOISE REDUCTION */}
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between text-sm font-mono text-zinc-400 mb-4 uppercase tracking-wider">
          <span>NOISE REDUCTION LEVEL</span>
          <span>{data.noiseReduction || 100}%</span>
        </div>
        <div className="w-full bg-zinc-900/50 rounded-2xl h-3 overflow-hidden border border-zinc-700/50">
          <div 
            className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-purple-600 rounded-2xl shadow-lg transition-all duration-1000"
            style={{ width: `${data.noiseReduction || 100}%` }}
          />
        </div>
      </div>

      {/* STAGES */}
      <div className="grid grid-cols-4 gap-6">
        {stages.map((stage, idx) => {
          const isActive = data.stage === stage.stageNum;
          const isComplete = data.stage > stage.stageNum;
          
          return (
            <div key={stage.name} className="group">
              <div className={`p-8 rounded-2xl border-2 transition-all duration-500 hover:scale-[1.02] h-full ${
                isComplete 
                  ? 'border-emerald-500/50 bg-emerald-950/30 shadow-2xl shadow-emerald-500/20' 
                  : isActive 
                  ? 'border-purple-500/70 bg-purple-950/40 shadow-2xl shadow-purple-500/30 scale-105 ring-2 ring-purple-500/30 animate-pulse' 
                  : 'border-zinc-800/50 bg-zinc-950/20 hover:border-zinc-600 hover:shadow-xl hover:shadow-zinc-500/20'
              }`}>
                <div className="text-center">
                  <div className="text-sm font-bold text-zinc-400 mb-3 uppercase tracking-wider">
                    {stage.name}
                  </div>
                  <div className={`text-3xl font-black mb-2 ${
                    isComplete ? 'text-emerald-400' : 
                    isActive ? 'bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent' : 
                    'text-zinc-600'
                  }`}>
                    {isComplete ? '✓' : isActive ? '●' : '○'}
                  </div>
                  <div className="text-xs font-mono text-zinc-500 tracking-wider">
                    STAGE {stage.stageNum}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* STATS */}
      <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
        <div className="tactical-panel p-8 rounded-2xl">
          <div className="text-sm text-zinc-400 mb-3 uppercase tracking-wider font-mono">EXERCISES</div>
          <div className="text-3xl font-black text-purple-400">{data.exercisesCompleted || 0}</div>
        </div>
        <div className="tactical-panel p-8 rounded-2xl">
          <div className="text-sm text-zinc-400 mb-3 uppercase tracking-wider font-mono">PROGRESS</div>
          <div className="text-3xl font-black text-cyan-400">{Math.round(data.progress || 0)}%</div>
        </div>
        <div className="tactical-panel p-8 rounded-2xl">
          <div className="text-sm text-zinc-400 mb-3 uppercase tracking-wider font-mono">NOISE</div>
          <div className="text-3xl font-black text-amber-400">{(data.noiseReduction || 100)}%</div>
        </div>
      </div>
    </div>
  );
};

export default RehabMode;
