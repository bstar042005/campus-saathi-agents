import React, { useState, useRef, useEffect } from 'react';
import { API_URL } from "../config";

export default function ChatModal({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hello! I am Campus Saathi, your campus navigation assistant. Tell me where you currently are and what steps you have already completed, and I will find the optimal path for you.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = async (e) => {
    e?.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    const newMessages = [...messages, { role: 'user', text: query }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setMessages([
        ...newMessages,
        { role: 'assistant', text: data.response || 'No response received.' }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        { role: 'assistant', text: 'Error connecting to the assistant. Please check if the backend is running.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'I just arrived at the gate. What is the optimal path?',
    'I completed panini_gate and office. Where should I go next?',
    'I am at LHTC gate. What is the next procedure?'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-xl h-[620px] max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">
        <div className="px-6 py-4 bg-[#0b1222] border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-500/20">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white text-sm font-bold flex items-center gap-2">
                Campus Saathi AI Assistant
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                  Qwen-3.8 27B
                </span>
              </h3>
              <p className="text-slate-400 text-xs">Autonomous multi-agent path reasoning</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-cyan-600 text-white rounded-br-none shadow-md shadow-cyan-900/30 font-medium'
                    : 'bg-[#1e293b]/90 text-slate-200 border border-slate-800/80 rounded-bl-none shadow'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.text}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#1e293b]/90 text-slate-400 border border-slate-800/80 rounded-2xl rounded-bl-none px-4 py-3 text-xs flex items-center gap-2 shadow">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse delay-150" />
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse delay-300" />
                <span className="text-slate-400 font-mono text-[11px] ml-1">Simulating all algorithms & computing optimal path...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {messages.length <= 1 && (
          <div className="px-5 py-2 border-t border-slate-800/50 bg-[#0b1222]/50">
            <span className="text-[11px] text-slate-400 font-mono block mb-1.5">Try asking:</span>
            <div className="flex flex-wrap gap-1.5">
              {sampleQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q)}
                  className="text-[11px] bg-slate-800/80 hover:bg-slate-750 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700/60 transition-colors text-left cursor-pointer"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSend} className="p-4 bg-[#0b1222] border-t border-slate-800/80 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Campus Saathi where to go or describe your progress..."
            disabled={loading}
            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-md shadow-cyan-900/30 flex items-center gap-1.5 cursor-pointer"
          >
            <span>Send</span>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
