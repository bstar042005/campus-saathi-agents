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
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const getSafeUrl = (value) => {
    try {
      const url = new URL(value);
      if (url.protocol === 'https:' || url.protocol === 'http:') {
        return url.href;
      }
    } catch {
      return null;
    }
    return null;
  };

  const handleSend = async (e) => {
    e?.preventDefault();

    const query = input.trim();

    if (!query || loading) return;

    const newMessages = [
      ...messages,
      { role: 'user', text: query }
    ];

    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });

      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
      }

      const data = await res.json();

      const isUnavailable =
        data.found === false || data.answer_type === 'not_available';

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          text: data.response || data.answer || 'No response received.',
          unavailable: isUnavailable,
          found: data.found ?? true,
          answerType: data.answer_type || 'knowledge',
          sources: Array.isArray(data.sources) ? data.sources : [],
          links: Array.isArray(data.links) ? data.links : [],
          nodeId: data.node_id ?? null,
          lastVerified: data.last_verified ?? null,
          suggestedContact: data.suggested_contact || null
        }
      ]);

    } catch (err) {
      console.error('Chat API error:', err);

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          text: 'Error connecting to the assistant. Please check if the backend is running.'
        }
      ]);

    } finally {
      setLoading(false);
    }
  };

  const getOfficialLink = (links = []) => {
    const officialLink = links.find((link) => {
      const url = typeof link === 'string' ? link : link?.url;

      try {
        const parsed = new URL(url);
        return parsed.protocol === 'https:' &&
          (parsed.hostname === 'iiitdmj.ac.in' ||
           parsed.hostname.endsWith('.iiitdmj.ac.in'));
      } catch {
        return false;
      }
    });

    if (!officialLink) {
      return {
        url: 'https://www.iiitdmj.ac.in',
        label: 'IIITDM Jabalpur Official Website'
      };
    }

    return typeof officialLink === 'string'
      ? { url: officialLink, label: 'IIITDM Jabalpur Official Website' }
      : officialLink;
  };

  const sampleQueries = [
    'I just arrived at the gate. What is the optimal path?',
    'I completed panini_gate and office. Where should I go next?',
    'I am at LHTC gate. What is the next procedure?'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">

      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-xl h-[620px] max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">

        {/* Header */}
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

              <p className="text-slate-400 text-xs">
                Autonomous multi-agent path reasoning
              </p>
            </div>

          </div>

          <button onClick={onClose} className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 flex items-center justify-center transition-colors cursor-pointer" aria-label="Close">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

        </div>

        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.unavailable ? (
                /* "Information not available" card */
                <div className="unavailable-card">
                  <div className="unavailable-card-header">
                    <span className="unavailable-card-icon" aria-hidden="true">!</span>
                    <span>Information Not Available</span>
                  </div>

                  <div className="unavailable-card-message whitespace-pre-wrap">
                    {msg.text}
                  </div>

                  {(() => {
                    const officialLink = getOfficialLink(msg.links);
                    const safeUrl = getSafeUrl(officialLink.url);

                    return safeUrl ? (
                      <a
                        href={safeUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="official-website-button"
                      >
                        <span>Visit Official Website</span>
                        <span aria-hidden="true">↗</span>
                      </a>
                    ) : null;
                  })()}

                  {msg.suggestedContact && (
                    <div className="suggested-contact">
                      <div className="suggested-contact-title">Suggested Contact</div>
                      <div className="suggested-contact-details">
                        {msg.suggestedContact.name && <div>{msg.suggestedContact.name}</div>}
                        {msg.suggestedContact.office && <div>{msg.suggestedContact.office}</div>}
                        {msg.suggestedContact.location_text && <div>{msg.suggestedContact.location_text}</div>}
                        {msg.suggestedContact.phone && <div>Phone: {msg.suggestedContact.phone}</div>}
                        {msg.suggestedContact.email && <div>Email: {msg.suggestedContact.email}</div>}
                        {msg.suggestedContact.hours && <div>Hours: {msg.suggestedContact.hours}</div>}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white rounded-br-none shadow-md shadow-cyan-900/30 font-medium'
                      : 'bg-[#1e293b]/90 text-slate-200 border border-slate-800/80 rounded-bl-none shadow'
                  }`}
                >

                  {/* Answer */}
                  <div className="whitespace-pre-wrap">
                    {msg.text}
                  </div>

                  {/* Structured assistant metadata */}
                  {msg.role === 'assistant' && (
                    <>

                      {/* Answer type */}
                      {msg.answerType && msg.answerType !== 'knowledge' && (
                        <span className="inline-block mt-2 px-2 py-1 rounded-md bg-slate-800 text-slate-400 text-[10px] capitalize">
                          {msg.answerType.replaceAll('_', ' ')}
                        </span>
                      )}

                      {/* Sources */}
                      {msg.sources?.some(source => getSafeUrl(source.url)) && (
                        <div className="mt-3 pt-3 border-t border-slate-700/70">

                          <p className="text-[11px] font-semibold text-cyan-400 mb-2">
                            Sources
                          </p>

                          <div className="space-y-2">

                            {msg.sources.map((source, index) => {
                              const safeUrl = getSafeUrl(source.url);

                              if (!safeUrl) return null;

                              return (
                                <a
                                  key={source.id || index}
                                  href={safeUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-2 text-xs text-cyan-300 hover:text-cyan-200 underline underline-offset-2 break-all"
                                >
                                  <span>{source.title}</span>
                                  <span aria-hidden="true">↗</span>
                                </a>
                              );
                            })}

                          </div>
                        </div>
                      )}

                      {/* External links */}
                      {msg.links?.some(link => getSafeUrl(link.url)) && (
                        <div className="mt-3 pt-3 border-t border-slate-700/70">

                          <p className="text-[11px] font-semibold text-cyan-400 mb-2">
                            Useful Links
                          </p>

                          <div className="flex flex-wrap gap-2">

                            {msg.links.map((link, index) => {
                              const safeUrl = getSafeUrl(link.url);

                              if (!safeUrl) return null;

                              return (
                                <a
                                  key={`${link.url}-${index}`}
                                  href={safeUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-950/70 border border-cyan-800 text-cyan-300 hover:bg-cyan-900 text-xs font-medium transition-colors"
                                >
                                  {link.label}
                                  <span aria-hidden="true">↗</span>
                                </a>
                              );
                            })}

                          </div>
                        </div>
                      )}

                      {/* Node information */}
                      {msg.nodeId && (
                        <p className="mt-2 text-[10px] text-slate-500">
                          Campus location: {msg.nodeId}
                        </p>
                      )}

                      {/* Verification date */}
                      {msg.lastVerified && (
                        <p className="mt-2 text-[10px] text-slate-500">
                          Last verified: {msg.lastVerified}
                        </p>
                      )}

                    </>
                  )}

                </div>
              )}
            </div>
          ))}

          {/* Loading animation */}
          {loading && (
            <div className="flex justify-start">

              <div className="bg-[#1e293b]/90 text-slate-400 border border-slate-800/80 rounded-2xl rounded-bl-none px-4 py-3 text-xs flex items-center gap-2 shadow">

                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse delay-150" />
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse delay-300" />

                <span className="text-slate-400 font-mono text-[11px] ml-1">
                  Simulating all algorithms & computing optimal path...
                </span>

              </div>
            </div>
          )}

          <div ref={messagesEndRef} />

        </div>

        {/* Sample queries */}
        {messages.length <= 1 && (
          <div className="px-5 py-2 border-t border-slate-800/50 bg-[#0b1222]/50">

            <span className="text-[11px] text-slate-400 font-mono block mb-1.5">
              Try asking:
            </span>

            <div className="flex flex-wrap gap-1.5">

              {sampleQueries.map((q, idx) => (
                <button key={idx} onClick={() => setInput(q)} className="text-[11px] bg-slate-800/80 hover:bg-slate-750 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700/60 transition-colors text-left cursor-pointer">
                  "{q}"
                </button>
              ))}

            </div>
          </div>
        )}

        {/* Input */}
        <form
          onSubmit={handleSend}
          className="p-4 bg-[#0b1222] border-t border-slate-800/80 flex items-center gap-2"
        >

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Campus Saathi where to go or describe your progress..."
            disabled={loading}
            className="flex-1 min-w-0 bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
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
