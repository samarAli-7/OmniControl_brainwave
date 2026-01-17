import React, { useState, useEffect, useRef } from 'react';
import { ref, onValue, update, set } from "firebase/database";
import { db } from './firebase'; 
import { Settings, Crosshair, ChevronLeft, ChevronRight, Brain, TrendingUp, MessageCircle, Download, AlertCircle } from 'lucide-react';
import GestureCard from './components/GestureCard';
import CalibrationMode from './components/CalibrationMode';
import RehabMode from './components/RehabMode';
import TutorialAgent from './components/TutorialAgent';

const MODES = {
  GESTURE_MAPPING: 'gesture_mapping',
  CALIBRATION: 'calibration',
  REHAB_TRAINING: 'rehab_training'
};

const CUSTOM_GESTURES = [
  'one', 'two', 'three', 'four',
  'five', 'fist', 'thumbs_up', 'thumbs_down'
];

const AVAILABLE_ACTIONS = [
  { id: 'none', label: '[ UNMAPPED ]' },
  { id: 'vtt_toggle', label: 'VOICE_TO_TEXT_TOGGLE' },
  { id: 'snapshot', label: 'SNAPSHOT' },
  { id: 'volume_up', label: 'VOLUME_UP' },
  { id: 'volume_down', label: 'VOLUME_DOWN' },
  { id: 'tab_switch', label: 'TAB_SWITCH' },
  { id: 'brightness_up', label: 'BRIGHTNESS_UP' },
  { id: 'brightness_down', label: 'BRIGHTNESS_DOWN' },
  { id: 'cursor_nav', label: 'CURSOR_NAVIGATION' },
  { id: 'media_play', label: 'MEDIA_PLAY_PAUSE' },
  { id: 'asl_mode_toggle', label: 'ASL_MODE_TOGGLE' }
];

const DEFAULT_MAPPINGS = {
  one: 'cursor_nav',
  two: 'media_play',
  three: 'brightness_up',
  four: 'brightness_down',
  five: 'snapshot',
  fist: 'tab_switch',
  thumbs_up: 'volume_up',
  thumbs_down: 'volume_down'
};

// 👈 YOUR EXACT AGENT CONFIG
const AGENT_CONFIG = {
  id: '696acde1c7d6dfdf7e337e5a',
  apiKey: 'odOSZ853W9XlcPhdfeNVcR1Ktga1SGna'
};

const normalizeMappings = (rawMappings) => {
  const normalized = { ...DEFAULT_MAPPINGS };
  
  Object.keys(rawMappings || {}).forEach(gesture => {
    const action = rawMappings[gesture];
    normalized[gesture] = AVAILABLE_ACTIONS.some(a => a.id === action) ? action : DEFAULT_MAPPINGS[gesture];
  });
  
  return normalized;
};

// 👈 TRACK PREVIOUS STATE FOR CHANGE DETECTION
const usePrevious = (value) => {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
};

// 👈 YOUR EXACT JSON FORMAT
const createJsonPayload = (mappings, hwStatus, currentMode, syncStatus) => ({
  timestamp: Date.now(),
  version: "1.0",
  mappings: mappings,
  active: true,
  metadata: {
    team: "BYTEFORCE",
    competition: "Brainwave 2.0",
    mode: currentMode,
    sync_status: syncStatus,
    hw_status: {
      mouse_nav: hwStatus.mouse_nav,
      left_active: hwStatus.left_active,
      right_active: hwStatus.right_active
    }
  }
});

// 👈 SEND TO YOUR AI AGENT - ONLY ON USER CHANGE
const sendToAIAgent = async (mappings, hwStatus, currentMode, setAgentStatus) => {
  const jsonData = createJsonPayload(mappings, hwStatus, currentMode, 'ai_synced');
  
  try {
    setAgentStatus('agent_sending');
    console.log('🤖 → AI AGENT (USER CHANGE):', AGENT_CONFIG.id);
    
    const response = await fetch(`https://api.x.ai/v1/chat/completions`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${AGENT_CONFIG.apiKey}`
      },
      body: JSON.stringify({
        model: "grok-beta",
        messages: [{
          role: "user",
          content: `GESTURE MAPPING UPDATE:\n\n${JSON.stringify(jsonData, null, 2)}`
        }],
        stream: false
      })
    });

    if (response.ok) {
      setAgentStatus('agent_synced');
      console.log('✅ AI AGENT RECEIVED JSON');
      return jsonData;
    } else {
      setAgentStatus('agent_error');
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    setAgentStatus('agent_error');
    console.error('❌ AI AGENT ERROR:', error);
  }
};

// 👈 DOWNLOAD JSON (unchanged)
const downloadJsonFile = (mappings, hwStatus, currentMode) => {
  const jsonData = createJsonPayload(mappings, hwStatus, currentMode, 'manual_download');
  
  const filename = `omnicontral-gestures-${Date.now()}.json`;
  const dataStr = JSON.stringify(jsonData, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(dataBlob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
  
  console.log('💾 JSON DOWNLOADED:', filename);
};

export default function App() {
  const [syncStatus, setSyncStatus] = useState('sync_idle');
  const [agentStatus, setAgentStatus] = useState('agent_idle');
  const [isTutorialOpen, setIsTutorialOpen] = useState(false);
  
  const [activeMode, setActiveMode] = useState(MODES.GESTURE_MAPPING);
  const [isSidePanelOpen, setIsSidePanelOpen] = useState(true);
  const [activeGesture, setActiveGesture] = useState(null);
  const [mappings, setMappings] = useState(DEFAULT_MAPPINGS);
  const [hwStatus, setHwStatus] = useState({ 
    mouse_nav: true, 
    left_active: false,
    right_active: false
  });
  const [calibrationData, setCalibrationData] = useState({ status: 'idle', progress: 0 });
  const [rehabData, setRehabData] = useState({
    stage: 1, progress: 0, noiseReduction: 100, exercisesCompleted: 0
  });

  // 👈 DETECT USER MAPPING CHANGES → SEND JSON
  const prevMappings = usePrevious(mappings);
  
  useEffect(() => {
    // 👈 ONLY send when USER changes mappings (not Firebase noise)
    if (activeMode === MODES.GESTURE_MAPPING && 
        prevMappings && 
        JSON.stringify(prevMappings) !== JSON.stringify(mappings)) {
      console.log('🔄 USER CHANGE DETECTED → SENDING JSON');
      sendToAIAgent(mappings, hwStatus, activeMode, setAgentStatus);
    }
  }, [mappings, hwStatus, activeMode]);

  // 👈 Reset statuses when leaving gesture mapping
  useEffect(() => {
    if (activeMode !== MODES.GESTURE_MAPPING) {
      setSyncStatus('sync_idle');
      setAgentStatus('agent_idle');
    }
  }, [activeMode]);

  useEffect(() => {
    const initializeFirebase = async () => {
      try {
        await set(ref(db, 'settings/mappings'), DEFAULT_MAPPINGS);
        console.log('✅ Firebase initialized');
      } catch (error) {
        console.error('Firebase init error:', error);
      }
    };
    initializeFirebase();
  }, []);

  // 👈 NO AUTO-SYNC IN FIREBASE LISTENERS - PREVENTS SPAM
  useEffect(() => {
    const gestureRef = ref(db, 'system/current_gesture');
    const mappingsRef = ref(db, 'settings/mappings');
    const hardwareRef = ref(db, 'system/hardware');
    const calibrationRef = ref(db, 'user/calibration');
    const rehabRef = ref(db, 'user/rehab');

    const unsubscribeGesture = onValue(gestureRef, (snap) => {
      setActiveGesture(snap.val());
    });

    const unsubscribeMappings = onValue(mappingsRef, (snap) => {
      const rawData = snap.val();
      const safeMappings = normalizeMappings(rawData);
      setMappings(safeMappings);
      // 👈 NO AUTO-SEND HERE - useEffect handles change detection
    });
    
    const unsubscribeHardware = onValue(hardwareRef, (snap) => {
      const data = snap.val() || {};
      setHwStatus({
        mouse_nav: data.mouse_nav ?? true,
        left_active: data.left_click ?? false,
        right_active: data.right_click ?? false
      });
    });
    
    const unsubscribeCalibration = onValue(calibrationRef, (snap) => {
      setCalibrationData(snap.val() || { status: 'idle', progress: 0 });
    });
    
    const unsubscribeRehab = onValue(rehabRef, (snap) => {
      setRehabData(snap.val() || { 
        stage: 1, progress: 0, noiseReduction: 100, exercisesCompleted: 0 
      });
    });

    return () => {
      unsubscribeGesture(); unsubscribeMappings(); unsubscribeHardware();
      unsubscribeCalibration(); unsubscribeRehab();
    };
  }, []); // 👈 EMPTY deps = NO SPAM

  const handleUpdateMapping = async (gesture, actionId) => {
    try {
      await update(ref(db, `settings/mappings`), { [gesture]: actionId });
      // 👈 useEffect will detect this change → auto-send
    } catch (error) {
      console.error('❌ Update failed:', error);
    }
  };

  const handleAIAgentSync = async () => {
    await sendToAIAgent(mappings, hwStatus, activeMode, setAgentStatus);
  };

  const handleDownloadJson = () => {
    downloadJsonFile(mappings, hwStatus, activeMode);
    setAgentStatus('agent_downloaded');
  };

  const startCalibration = async () => {
    try {
      await set(ref(db, 'user/calibration'), {
        status: 'running',
        progress: 0,
        exercises: ['up', 'down', 'left', 'right'],
        timestamp: Date.now()
      });
      setActiveMode(MODES.CALIBRATION);
    } catch (error) {
      console.error('❌ Calibration failed:', error);
    }
  };

  const startRehabTraining = async () => {
    try {
      await set(ref(db, 'user/rehab'), {
        stage: 1,
        progress: 0,
        noiseReduction: 100,
        exercisesCompleted: 0,
        timestamp: Date.now()
      });
      setActiveMode(MODES.REHAB_TRAINING);
    } catch (error) {
      console.error('❌ Rehab failed:', error);
    }
  };

  const getSyncDisplay = () => {
    switch (syncStatus) {
      case 'synced': return { text: 'SYNCED', color: 'text-green-400 bg-green-500/20 border-green-500/30' };
      case 'sync_live': return { text: 'SYNC LIVE', color: 'text-amber-400 bg-amber-500/20 border-amber-500/30 animate-pulse' };
      case 'sync_error': return { text: 'SYNC ERROR', color: 'text-red-400 bg-red-500/20 border-red-500/30' };
      default: return { text: 'SYNC IDLE', color: 'text-zinc-400/70 bg-zinc-800/30 border-zinc-700/50' };
    }
  };

  const getAgentDisplay = () => {
    switch (agentStatus) {
      case 'agent_synced': return { text: 'AI SYNCED', color: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30' };
      case 'agent_sending': return { text: 'AI SENDING', color: 'text-blue-400 bg-blue-500/20 border-blue-500/30 animate-pulse' };
      case 'agent_downloaded': return { text: 'JSON READY', color: 'text-purple-400 bg-purple-500/20 border-purple-500/30' };
      case 'agent_error': return { text: 'AI ERROR', color: 'text-red-400 bg-red-500/20 border-red-500/30 animate-pulse' };
      default: return { text: 'AI READY', color: 'text-zinc-400/70 bg-zinc-800/30 border-zinc-700/50' };
    }
  };

  const syncDisplay = getSyncDisplay();
  const agentDisplay = getAgentDisplay();

  return (
    <>
      <div className="h-screen w-screen flex overflow-hidden bg-[#050505]">
        {/* SIDE PANEL */}
        <div className={`h-full bg-zinc-950/80 backdrop-blur-sm border-r border-zinc-800/50 transition-all duration-300 flex flex-col ${
          isSidePanelOpen ? 'w-[280px]' : 'w-[60px]'
        }`}>
          <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
            {isSidePanelOpen && <h3 className="text-lg font-black tracking-tight text-white">MODES</h3>}
            <button
              onClick={() => setIsSidePanelOpen(!isSidePanelOpen)}
              className="p-2 rounded-lg hover:bg-zinc-800/50 transition-all text-zinc-400 hover:text-white"
            >
              {isSidePanelOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
            </button>
          </div>

          <nav className="flex-1 p-4 space-y-2 mt-4">
            <button onClick={() => setActiveMode(MODES.GESTURE_MAPPING)} className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all font-mono uppercase tracking-wider text-sm ${
              activeMode === MODES.GESTURE_MAPPING
                ? 'bg-amber-500/20 border-2 border-amber-500/50 text-amber-300 shadow-lg shadow-amber-500/20'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white border border-zinc-700/50'
            }`}>
              <Settings size={20} />{isSidePanelOpen && 'GESTURE MAP'}
            </button>

            <button onClick={startCalibration} className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all font-mono uppercase tracking-wider text-sm ${
              activeMode === MODES.CALIBRATION
                ? 'bg-cyan-500/20 border-2 border-cyan-500/50 text-cyan-300 shadow-lg shadow-cyan-500/20'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white border border-zinc-700/50'
            }`}>
              <Brain size={20} />{isSidePanelOpen && 'CALIBRATION'}
            </button>

            <button onClick={startRehabTraining} className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all font-mono uppercase tracking-wider text-sm ${
              activeMode === MODES.REHAB_TRAINING
                ? 'bg-purple-500/20 border-2 border-purple-500/50 text-purple-300 shadow-lg shadow-purple-500/20'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white border border-zinc-700/50'
            }`}>
              <TrendingUp size={20} />{isSidePanelOpen && 'REHAB TRAIN'}
            </button>
          </nav>
        </div>

        {/* MAIN CONTENT */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* HEADER */}
          <header className="border-b-2 border-amber-500/30 p-6 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-4">
              <Crosshair className={`w-12 h-12 ${activeGesture ? 'text-amber-400 animate-pulse' : 'text-amber-500'}`} />
              <div className="flex items-end gap-2 pb-1">
                <h1 className="text-5xl font-black tracking-tight text-white italic leading-tight">
                  OMNI<span className="text-amber-500">CONTROL</span>
                </h1>
                <span className="text-xs text-white/60 font-mono tracking-wider uppercase">by BYTEFORCE</span>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <button onClick={() => setIsTutorialOpen(true)} className="p-3 rounded-xl hover:bg-zinc-800/50 transition-all text-zinc-400 hover:text-white hover:shadow-lg group" title="Tutorial Guide">
                <MessageCircle size={24} className="group-hover:rotate-12 transition-transform duration-300" />
              </button>
              
              <div className="text-right">
                <div className="text-xs tracking-widest text-amber-500/60 uppercase font-mono">
                  {activeMode === MODES.CALIBRATION ? 'CALIBRATION_MODE' : 
                   activeMode === MODES.REHAB_TRAINING ? 'REHAB_TRAINING' : 'GESTURE_MAPPING'}
                </div>
                <div className={`text-lg font-black mt-1 italic ${hwStatus.mouse_nav ? 'text-amber-500' : 'text-red-500'}`}>
                  {hwStatus.mouse_nav ? 'NAV_ACTIVE' : 'NAV_DISABLED'}
                </div>
              </div>
            </div>
          </header>

          {/* HARDWARE STATUS */}
          <div className="p-6 border-b border-zinc-800/30 shrink-0">
            <div className="grid grid-cols-3 gap-4 h-32">
              <div className={`group tactical-panel p-6 border-2 hover:shadow-xl cursor-pointer flex-1 flex flex-col justify-between transition-all duration-200 ${
                hwStatus.mouse_nav ? 'border-amber-500/40 bg-amber-500/5 hover:border-amber-500/70' : 'border-red-900/50 bg-red-950/10 hover:border-red-500/70'
              }`}>
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">RING FINGER</span>
                <div className={`text-2xl font-black italic flex-1 flex items-end pb-1 ${hwStatus.mouse_nav ? 'text-white' : 'text-red-400'}`}>
                  NAV_{hwStatus.mouse_nav ? 'ENABLED' : 'DISABLED'}
                </div>
              </div>

              <div className={`group tactical-panel p-6 border-2 hover:shadow-xl cursor-pointer flex-1 flex flex-col justify-between transition-all duration-200 ${
                hwStatus.left_active ? 'border-amber-400/70 bg-amber-500/20 shadow-[0_0_25px_rgba(251,191,36,0.4)] hover:shadow-[0_0_35px_rgba(251,191,36,0.6)]' : 'border-zinc-800/50 hover:border-zinc-600'
              }`}>
                <div className="text-xs text-zinc-400 font-bold mb-2 tracking-wider flex items-start">INDEX FINGER</div>
                <div className={`text-2xl font-black italic flex-1 flex items-end pb-1 transition-colors ${hwStatus.left_active ? 'text-white' : 'text-zinc-400'}`}>
                  LEFT CLICK
                </div>
              </div>

              <div className={`group tactical-panel p-6 border-2 hover:shadow-xl cursor-pointer flex-1 flex flex-col justify-between transition-all duration-200 ${
                hwStatus.right_active ? 'border-amber-400/70 bg-amber-500/20 shadow-[0_0_25px_rgba(251,191,36,0.4)] hover:shadow-[0_0_35px_rgba(251,191,36,0.6)]' : 'border-zinc-800/50 hover:border-zinc-600'
              }`}>
                <div className="text-xs text-zinc-400 font-bold mb-2 tracking-wider flex items-start">MIDDLE FINGER</div>
                <div className={`text-2xl font-black italic flex-1 flex items-end pb-1 transition-colors ${hwStatus.right_active ? 'text-white' : 'text-zinc-400'}`}>
                  RIGHT CLICK
                </div>
              </div>
            </div>
          </div>

          {/* MAIN CONTENT */}
          <main className="flex-1 overflow-y-auto p-8">
            {activeMode === MODES.GESTURE_MAPPING && (
              <div>
                <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4 mb-12">
                  <div className="flex items-center gap-4">
                    <Settings className="w-8 h-8 text-amber-400" />
                    <h2 className="text-2xl font-black tracking-widest text-amber-500 uppercase">GESTURE MAPPING</h2>
                  </div>
                  
                  <div className="flex gap-3 flex-wrap">
                    <span className={`text-xs px-3 py-1.5 rounded-full font-mono font-bold border ${syncDisplay.color}`}>
                      {syncDisplay.text}
                    </span>
                    <span className={`text-xs px-3 py-1.5 rounded-full font-mono font-bold border ${agentDisplay.color}`}>
                      {agentDisplay.text}
                    </span>
                  </div>
                </div>

                {/* AI AGENT / JSON CONTROLS */}
                <div className="mb-8 p-6 bg-zinc-950/50 border border-zinc-800/50 rounded-2xl max-w-2xl backdrop-blur-sm">
                  <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Download className="w-5 h-5 text-purple-400" />
                      <div>
                        <h3 className="font-bold text-white text-sm uppercase tracking-wider">Brainwave 2.0 JSON → AI</h3>
                        <p className="text-xs text-zinc-400">AUTO-SYNC on user changes</p>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={handleAIAgentSync}
                        disabled={agentStatus === 'agent_sending'}
                        className="px-4 py-2 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/40 hover:border-emerald-500/70 text-emerald-300 hover:text-emerald-200 rounded-xl font-mono text-xs uppercase tracking-wider transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {agentStatus === 'agent_sending' ? (
                          <>
                            <div className="w-3 h-3 bg-emerald-400 rounded-full animate-bounce" />
                            Sending...
                          </>
                        ) : (
                          'FORCE SYNC'
                        )}
                      </button>
                      
                      <button
                        onClick={handleDownloadJson}
                        className="px-4 py-2 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/40 hover:border-purple-500/70 text-purple-300 hover:text-purple-200 rounded-xl font-mono text-xs uppercase tracking-wider transition-all hover:scale-105 shadow-lg hover:shadow-purple-500/20 flex items-center gap-1"
                      >
                        <Download className="w-4 h-4" />
                        JSON
                      </button>
                    </div>
                  </div>
                  
                  {agentStatus === 'agent_error' && (
                    <div className="flex items-center gap-2 text-red-400 text-xs p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
                      <AlertCircle className="w-4 h-4" />
                      AI sync failed. Use FORCE SYNC or download JSON.
                    </div>
                  )}
                  
                  <div className="text-xs text-zinc-500 mt-4 text-center">
                    
                  </div>
                </div>

                <div className="grid grid-cols-4 grid-rows-2 gap-8 max-w-6xl mx-auto">
                  {CUSTOM_GESTURES.map(gesture => (
                    <GestureCard 
                      key={gesture}
                      name={gesture}
                      isActive={activeGesture === gesture}
                      currentAction={mappings[gesture]}
                      actions={AVAILABLE_ACTIONS}
                      onMap={(actionId) => handleUpdateMapping(gesture, actionId)}
                    />
                  ))}
                </div>
              </div>
            )}

            {activeMode === MODES.CALIBRATION && <CalibrationMode data={calibrationData} />}
            {activeMode === MODES.REHAB_TRAINING && <RehabMode data={rehabData} />}
          </main>
        </div>
      </div>

      <TutorialAgent isOpen={isTutorialOpen} onClose={() => setIsTutorialOpen(false)} />
    </>
  );
}