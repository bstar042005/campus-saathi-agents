import React, { useState, useEffect } from 'react';
import CampusMap from './components/CampusMap';
import MetricsPanel from './components/MetricsPanel';
import ChatModal from './components/ChatModal';
import { API_URL } from "./config";

export default function App() {
  const [selectedAlgo, setSelectedAlgo] = useState('a_star');
  const [qIterations, setQIterations] = useState(100);
  const [useCongestion, setUseCongestion] = useState(true);
  const [simulationData, setSimulationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const algorithms = [
    { id: 'a_star', label: 'A* Search' },
    { id: 'bfs', label: 'Breadth-First Search (BFS)' },
    { id: 'dfs', label: 'Depth-First Search (DFS)' },
    { id: 'greedy_nearest', label: 'Greedy Nearest' },
    { id: 'ids', label: 'Iterative Deepening Search (IDS)' },
    { id: 'simulated_annealing', label: 'Simulated Annealing' },
    { id: 'q_learning', label: 'Q-Learning (RL)' }
  ];

  const qIterationOptions = [10, 25, 50, 100, 500];

  const runSimulation = async (algoId, congestionState, iterations = qIterations) => {
    setLoading(true);
    try {
      const url = `${API_URL}/api/simulate/${algoId}?congestion=${congestionState}&iterations=${iterations}`;
      const response = await fetch(url);
      const data = await response.json();
      setSimulationData(data);
    } catch (err) {
      console.error("Failed to run simulation:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation(selectedAlgo, useCongestion, qIterations);
  }, []);

  const handleAlgoClick = (algoId) => {
    setSelectedAlgo(algoId);
    runSimulation(algoId, useCongestion, qIterations);
  };

  const handleIterationsChange = (iter) => {
    setQIterations(iter);
    setSelectedAlgo('q_learning');
    runSimulation('q_learning', useCongestion, iter);
  };

  const handleToggleCongestion = () => {
    const nextState = !useCongestion;
    setUseCongestion(nextState);
    runSimulation(selectedAlgo, nextState, qIterations);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      {/* Header with Title and Congestion Toggle */}
      <header className="max-w-6xl mx-auto mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Campus Saathi</h1>
          <p className="text-slate-400 text-sm mt-1">Multi-Agent Campus Pathfinding Simulation Dashboard</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Chat button */}
          <button
            type="button"
            onClick={() => setIsChatOpen(true)}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white px-4 py-2.5 rounded-lg font-medium text-xs shadow-md shadow-cyan-900/30 transition-all flex items-center gap-2 border border-cyan-400/40 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <span>Ask Campus Saathi AI</span>
          </button>

          {/*Congestion Toggle Button */}
          <button
            type="button"
            onClick={handleToggleCongestion}
            className="bg-white text-slate-900 px-4 py-2.5 rounded-lg font-medium text-xs shadow-md hover:bg-slate-100 transition-all flex items-center gap-2 border border-slate-300 cursor-pointer"
          >
            <span>Background Workers Congestion</span>
            <span className={`w-2.5 h-2.5 rounded-full ${useCongestion ? 'bg-emerald-600' : 'bg-rose-500'}`} />
            <span className="text-[10px] uppercase font-bold text-slate-600">
              {useCongestion ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">

        <div className="lg:col-span-2 space-y-6">
          <CampusMap simulationResult={simulationData} showBackground={useCongestion} />
        </div>

        {/* Right Sidebar: Controls & Metrics */}
        <div className="space-y-6">
          {/* Algorithm Controls */}
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-700 shadow-xl">
            <h3 className="text-lg font-bold mb-4">Select Algorithm</h3>
            <div className="space-y-2.5">
              {algorithms.map((algo) => {
                const isSelected = selectedAlgo === algo.id;
                return (
                  <div key={algo.id} className="space-y-2">
                    <button
                      onClick={() => handleAlgoClick(algo.id)}
                      disabled={loading}
                      className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all text-left flex justify-between items-center cursor-pointer ${isSelected
                        ? 'bg-sky-600 text-white shadow-lg shadow-sky-900/40'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                    >
                      <span>{algo.label}</span>
                      {isSelected && loading && (
                        <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                      )}
                    </button>

                    {/* Q-Learning Iteration Options */}
                    {algo.id === 'q_learning' && isSelected && (
                      <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 space-y-2">
                        <span className="text-xs text-slate-400 font-medium block">
                          Training Iterations (Episodes):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {qIterationOptions.map((iter) => (
                            <button
                              key={iter}
                              onClick={() => handleIterationsChange(iter)}
                              disabled={loading}
                              className={`px-2.5 py-1 text-xs rounded font-medium transition-all cursor-pointer ${qIterations === iter
                                ? 'bg-amber-500 text-slate-950 font-bold'
                                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                            >
                              {iter} iter
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Metrics Panel */}
          <MetricsPanel metrics={simulationData?.metrics} />
        </div>

      </main>

      {/* Groq Chat Assistant Interface */}
      <ChatModal isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}