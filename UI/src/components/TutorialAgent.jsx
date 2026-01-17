import React, { useState, useEffect } from 'react';
import { MessageCircle, X, Brain, TrendingUp, Settings, ChevronLeft } from 'lucide-react';

const TutorialAgent = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: 'agent',
      content: "👋 Welcome to **OMNI-CONTROL**! I'm your tutorial guide. I'll show you how to map gestures, calibrate, and start rehab training. What would you like to learn first?",
      type: 'welcome'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const tutorialTopics = {
    mapping: {
      title: "🎮 Gesture Mapping",
      steps: [
        "1. **Select a gesture card** (one, two, three, etc.)",
        "2. **Click the dropdown** in the card to see available actions",
        "3. **Choose an action** like SNAPSHOT, VOLUME_UP, or CURSOR_NAV",
        "4. **Watch the green SYNCED badge** - your mapping is live!",
        "**Pro tip:** Changes sync automatically to your hardware in real-time!"
      ]
    },
    calibration: {
      title: "🧠 Calibration Mode", 
      steps: [
        "1. **Click CALIBRATION** in the sidebar (Brain icon)",
        "2. **Follow on-screen prompts** to perform exercises: up/down/left/right",
        "3. **AI analyzes your movements** and builds a personal gesture profile",
        "4. **Improves accuracy** by learning your unique hand patterns",
        "**Duration:** ~2-3 minutes for optimal results"
      ]
    },
    rehab: {
      title: "💪 Rehab Training",
      steps: [
        "1. **Click REHAB TRAIN** in the sidebar (TrendingUp icon)",
        "2. **Progressive exercises** start simple, get harder over time",
        "3. **Real-time feedback** on noise reduction and progress",
        "4. **Tracks exercises completed** and motor skill improvement",
        "**Goal:** Build precise finger control through gamified training"
      ]
    }
  };

  const sendMessage = async (userMessage) => {
    // Add user message
    const userMsg = { id: Date.now(), role: 'user', content: userMessage };
    setMessages(prev => [...prev, userMsg]);
    
    setIsTyping(true);
    
    // Simulate AI response delay
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1200));
    
    let agentResponse;
    
    // Match user intent
    const lowerMsg = userMessage.toLowerCase();
    
    if (lowerMsg.includes('map') || lowerMsg.includes('gesture') || lowerMsg.includes('mapping')) {
      agentResponse = tutorialTopics.mapping;
    } else if (lowerMsg.includes('calib') || lowerMsg.includes('calibration')) {
      agentResponse = tutorialTopics.calibration;
    } else if (lowerMsg.includes('rehab') || lowerMsg.includes('training') || lowerMsg.includes('train')) {
      agentResponse = tutorialTopics.rehab;
    } else if (lowerMsg.includes('help') || lowerMsg.includes('how') || lowerMsg.includes('start')) {
      agentResponse = {
        title: "🚀 Quick Start Guide",
        steps: [
          "1. **GESTURE MAP** - Assign actions to hand gestures",
          "2. **CALIBRATION** - Personalize to your hand (recommended first)",
          "3. **REHAB TRAIN** - Improve precision through exercises",
          "**Ready?** Try 'show me gesture mapping' or 'how to calibrate'"
        ]
      };
    } else {
      agentResponse = {
        title: "🤔 Let me help you!",
        steps: [
          "**Ask me about:**",
          "• 'gesture mapping'",
          "• 'calibration'", 
          "• 'rehab training'",
          "• 'how to start'",
          "Type any of these to see step-by-step guides!"
        ]
      };
    }
    
    const responseMsg = {
      id: Date.now() + 1,
      role: 'agent',
      content: renderTutorialResponse(agentResponse),
      type: 'tutorial'
    };
    
    setMessages(prev => [...prev, responseMsg]);
    setIsTyping(false);
    setInput('');
  };

  const renderTutorialResponse = (topic) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
            <span className="text-xs font-bold text-white">AI</span>
          </div>
          <h4 className="text-lg font-black text-white tracking-tight">{topic.title}</h4>
        </div>
        <div className="space-y-2 pl-8">
          {topic.steps.map((step, i) => (
            <div key={i} className="flex items-start gap-3 group">
              <span className="w-6 h-6 bg-blue-500/20 border-2 border-blue-500/50 rounded-full flex items-center justify-center text-xs font-bold text-blue-400 flex-shrink-0 mt-0.5 group-hover:bg-blue-500/30 transition-all">
                {i + 1}
              </span>
              <span className="text-sm leading-relaxed text-zinc-300">{step}</span>
            </div>
          ))}
        </div>
        <div className="pt-4 mt-4 border-t border-zinc-800">
          <p className="text-xs text-zinc-500 italic">
            💡 **Next:** Try it now! Go back to the main interface and test what you just learned.
          </p>
        </div>
      </div>
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input.trim());
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-end lg:items-center justify-center p-4">
      <div className="w-full max-w-md h-[80vh] lg:h-auto bg-zinc-950/95 border border-zinc-800/50 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="p-6 border-b border-zinc-800/50 bg-gradient-to-r from-zinc-900/50 to-zinc-800/20 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-black text-white tracking-tight">Tutorial Guide</h3>
                <p className="text-xs text-zinc-500 uppercase tracking-wider font-mono">OMNI-CONTROL AI</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-zinc-800/50 transition-all text-zinc-400 hover:text-white"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'agent' ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[85%] p-4 rounded-2xl ${msg.role === 'agent' 
                ? 'bg-zinc-900/50 border border-zinc-700/50 backdrop-blur-sm' 
                : 'bg-amber-500/20 border border-amber-500/30'}`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 p-4 bg-zinc-900/50 border border-zinc-700/50 rounded-2xl backdrop-blur-sm max-w-[85%]">
                <div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce" />
                </div>
                <span className="text-sm text-zinc-400">Typing...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-6 border-t border-zinc-800/50 bg-zinc-950/50">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about gesture mapping, calibration, or rehab..."
              className="flex-1 bg-zinc-900/50 border border-zinc-700/50 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/75 transition-all outline-none"
              autoFocus
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-zinc-800/50 disabled:to-zinc-700/50 rounded-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-zinc-500 mt-2 text-center">
            Try: "gesture mapping" | "calibration" | "rehab training"
          </p>
        </form>
      </div>
    </div>
  );
};

export default TutorialAgent;
