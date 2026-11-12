import React, { useEffect, useState, useRef } from 'react';
import { API_URL } from "../config";

export default function CampusMap({
  simulationResult,
  showBackground,
  playbackSpeed = 1,
  isPaused = false,
  onReset
}) {
  const [mapData, setMapData] = useState({ nodes: {}, edges: [] });
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/api/map`)
      .then(res => res.json())
      .then(data => setMapData(data))
      .catch(err => console.error('Failed to load map data:', err));
  }, []);

  const trace = simulationResult?.trace || [];
  const backgroundAgentsSteps = simulationResult?.background_steps || [];

  useEffect(() => {
    setCurrentStepIndex(0);
  }, [simulationResult]);

  useEffect(() => {
    if (!trace || trace.length === 0 || isPaused) return;

    const baseInterval = 650;
    const intervalTime = Math.max(120, Math.floor(baseInterval / playbackSpeed));

    const interval = setInterval(() => {
      setCurrentStepIndex(prev => {
        if (prev < trace.length - 1) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, intervalTime);

    return () => clearInterval(interval);
  }, [trace, isPaused, playbackSpeed, simulationResult]);

  const currentStep = trace[currentStepIndex];
  const currentNodeName = currentStep ? currentStep.current_room : 'gate';
  const currentNode = mapData.nodes[currentNodeName];
  const currentBgAgents = showBackground ? (backgroundAgentsSteps[currentStepIndex] || []) : [];

  const completedSteps = new Set(currentStep?.completed_steps || []);

  const traversedEdges = new Set();
  const pathCoordinates = [];

  for (let i = 0; i <= currentStepIndex && i < trace.length; i++) {
    const step = trace[i];
    const room = step.current_room;
    const pos = mapData.nodes[room];
    if (pos) {
      pathCoordinates.push({ x: pos.x, y: pos.y, room });
    }
    if (i > 0) {
      const prevRoom = trace[i - 1].current_room;
      if (prevRoom && room && prevRoom !== room) {
        traversedEdges.add(`${prevRoom}__${room}`);
        traversedEdges.add(`${room}__${prevRoom}`);
      }
    }
  }

  const activeWorkerCount = showBackground ? (currentBgAgents.length || 20) : 0;

  return (
    <div className="bg-[#0e1726]/90 backdrop-blur-xl p-6 rounded-2xl border border-slate-800/80 shadow-2xl relative overflow-hidden">
      <div className="absolute -top-24 -left-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-wrap justify-between items-center mb-4 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
            <h2 className="text-white text-base font-bold tracking-tight">
              Campus Navigation Simulation
            </h2>
          </div>
          <p className="text-slate-400 text-xs mt-0.5 font-mono">
            Real-time Topo-Graph • Dynamic Congestion Model
          </p>
        </div>

        <div className="flex items-center gap-2.5 text-xs font-mono">
          <div className="bg-[#0b121e] px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center gap-1.5 shadow-inner">
            <span className="text-slate-400">Active Agents:</span>
            <span className="font-bold text-rose-400">1 Main</span>
            <span className="text-slate-600">/</span>
            <span className="font-bold text-slate-200">
              {showBackground ? `${activeWorkerCount} Workers` : '0 Workers'}
            </span>
          </div>

          <div className="bg-[#0b121e] px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center gap-1.5 shadow-inner">
            <span className="text-slate-400">Path Quality:</span>
            <span className="font-bold text-emerald-400">
              {currentStepIndex === trace.length - 1 && trace.length > 0 ? 'Completed' : 'Optimal'}
            </span>
          </div>
        </div>
      </div>

      <div className="relative rounded-xl border border-slate-800 bg-[#080d1a] overflow-hidden shadow-inner flex justify-center items-center">
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.07]"
          style={{
            backgroundImage: `radial-gradient(circle, #38bdf8 1px, transparent 1px)`,
            backgroundSize: '24px 24px'
          }}
        />

        <div className="absolute top-4 left-4 z-10 flex flex-col items-center bg-[#0e1726]/80 px-2 py-1 rounded border border-slate-800 text-[10px] font-mono text-slate-400 shadow">
          <span className="text-cyan-400 font-bold">N</span>
          <span className="text-slate-500">▲</span>
        </div>

        <div className="absolute top-14 left-4 z-10 bg-[#0c1322]/90 backdrop-blur-md px-3 py-2.5 rounded-xl border border-slate-800/80 text-[11px] font-medium shadow-xl max-w-[170px]">
          <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1.5 border-b border-slate-800 pb-1 font-mono">
            Graph Legend
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-rose-500/30" />
              <span className="text-slate-300">Agent Location</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-emerald-500/30" />
              <span className="text-emerald-300">Completed Step</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-white opacity-90 shadow-[0_0_8px_rgba(255,255,255,0.7)]" />
              <span className="text-slate-300">Workers</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-0.5 bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
              <span className="text-cyan-300 font-semibold">Traversed Path</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-0.5 bg-slate-700" />
              <span className="text-slate-400">Roadway</span>
            </div>
          </div>
        </div>

        <svg width="780" height="520" viewBox="40 20 720 440" className="w-full h-auto max-h-[540px]">
          <defs>
            {}
            <filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="redGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>

          {mapData.edges && mapData.edges.map((edge, idx) => {
            const u = mapData.nodes[edge.from];
            const v = mapData.nodes[edge.to];
            if (!u || !v) return null;
            return (
              <line
                key={`base-edge-${idx}`}
                x1={u.x}
                y1={u.y}
                x2={v.x}
                y2={v.y}
                stroke="#1e293b"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            );
          })}

          {mapData.edges && mapData.edges.map((edge, idx) => {
            const u = mapData.nodes[edge.from];
            const v = mapData.nodes[edge.to];
            if (!u || !v) return null;

            const isTraversed =
              traversedEdges.has(`${edge.from}__${edge.to}`) ||
              traversedEdges.has(`${edge.to}__${edge.from}`);

            if (!isTraversed) return null;

            return (
              <g key={`highlight-edge-${idx}`}>
                <line
                  x1={u.x}
                  y1={u.y}
                  x2={v.x}
                  y2={v.y}
                  stroke="#06b6d4"
                  strokeWidth="6"
                  strokeOpacity="0.4"
                  strokeLinecap="round"
                  filter="url(#cyanGlow)"
                />
                <line
                  x1={u.x}
                  y1={u.y}
                  x2={v.x}
                  y2={v.y}
                  stroke="#38bdf8"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </g>
            );
          })}

          {mapData.nodes && Object.entries(mapData.nodes).map(([id, pos]) => {
            const isCompleted = completedSteps.has(id);
            const isCurrent = currentNodeName === id;

            let fill = '#334155';
            let stroke = '#475569';
            let strokeWidth = '2';
            let r = 6.5;

            if (isCurrent) {
              fill = '#f43f5e';
              stroke = '#ffe4e6';
              strokeWidth = '3';
              r = 8;
            } else if (isCompleted) {
              fill = '#10b981';
              stroke = '#6ee7b7';
              strokeWidth = '2';
              r = 7;
            }

            return (
              <g key={`node-${id}`} className="transition-all duration-300">
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={r}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                  className="transition-all duration-300"
                />

                <text
                  x={pos.x}
                  y={pos.y - 12}
                  fill={isCurrent ? '#f43f5e' : isCompleted ? '#34d399' : '#94a3b8'}
                  fontSize="10"
                  fontWeight={isCurrent || isCompleted ? '700' : '500'}
                  textAnchor="middle"
                  fontFamily="system-ui, sans-serif"
                >
                  {id}
                </text>
              </g>
            );
          })}

          {showBackground && currentBgAgents.map((bgAgent, idx) => {
            const bgNode = mapData.nodes[bgAgent.current_room];
            if (!bgNode) return null;
            const offsetX = (idx % 4 - 1.5) * 6;
            const offsetY = (Math.floor(idx / 4) - 1.5) * 6;

            return (
              <circle
                key={`bg-worker-${idx}`}
                cx={bgNode.x + offsetX}
                cy={bgNode.y + offsetY}
                r="4.5"
                fill="#ffffff"
                opacity="0.85"
                className="transition-all duration-200"
                style={{
                  filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.8))'
                }}
              />
            );
          })}

          {currentNode && (
            <g>
              <circle
                cx={currentNode.x}
                cy={currentNode.y}
                r="16"
                fill="#f43f5e"
                opacity="0.3"
                className="animate-ping"
                style={{ transformOrigin: `${currentNode.x}px ${currentNode.y}px`, animationDuration: '1.6s' }}
              />
              <circle
                cx={currentNode.x}
                cy={currentNode.y}
                r="10"
                fill="#f43f5e"
                stroke="#fff"
                strokeWidth="2.5"
                filter="url(#redGlow)"
              />
            </g>
          )}
        </svg>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-slate-400 font-mono">
        <div className="flex items-center gap-2">
          <span>Step Progress:</span>
          <span className="text-cyan-400 font-bold">
            {trace.length > 0 ? currentStepIndex + 1 : 0}
          </span>
          <span className="text-slate-600">/</span>
          <span>{trace.length}</span>
        </div>

        {currentStep && (
          <div className="bg-[#0b1222] px-2.5 py-1 rounded border border-slate-800 text-[11px]">
            Action:{' '}
            <span className="text-cyan-300 font-bold">
              {currentStep.action_taken ? `${currentStep.action_taken[0]} → ${currentStep.action_taken[1]}` : 'idle'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}