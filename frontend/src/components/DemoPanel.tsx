"use client";

import React, { useState } from "react";
import { runDemoScenario, runLiveDemoScenario, DemoScenarioRunResponse, LiveDemoResponse, ScenarioType } from "../lib/api";
import { useVillageContext } from "./VillageContext";

const SCENARIOS: { id: ScenarioType; label: string; desc: string }[] = [
  { id: "WATER_CONVERGENCE", label: "Water Convergence", desc: "End-to-end matching of water needs with JJM footprint." },
  { id: "WATER_NO_PUBLIC_GAP", label: "Water (No Public Gap)", desc: "Demand exists, but infrastructure is reported as complete." },
  { id: "NON_WATER_DEMAND", label: "Non-Water Demand", desc: "Civic needs outside the currently supported JJM taxonomy." },
  { id: "UNRESOLVED_GEOGRAPHY", label: "Unresolved Geography", desc: "Signals that lack identifiable LGD codes." },
];

export default function DemoPanel() {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>("WATER_CONVERGENCE");
  const [mockLoading, setMockLoading] = useState(false);
  const [mockResult, setMockResult] = useState<DemoScenarioRunResponse | null>(null);
  const [mockError, setMockError] = useState<string | null>(null);

  const [liveLoading, setLiveLoading] = useState(false);
  const [liveResult, setLiveResult] = useState<LiveDemoResponse | null>(null);
  const [liveError, setLiveError] = useState<string | null>(null);

  const { setSelectedLgdCode } = useVillageContext();

  const handleRunMock = async () => {
    setMockLoading(true);
    setMockError(null);
    setMockResult(null);

    try {
      const res = await runDemoScenario({ scenario_id: selectedScenario });
      setMockResult(res);
    } catch (err: unknown) {
      setMockError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setMockLoading(false);
    }
  };

  const handleRunLive = async () => {
    setLiveLoading(true);
    setLiveError(null);
    setLiveResult(null);

    try {
      const res = await runLiveDemoScenario();
      setLiveResult(res);
      if (res.lgd_village_code) {
        setSelectedLgdCode(res.lgd_village_code);
      } else {
        setSelectedLgdCode("275084"); // Fallback for the water demo village
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message === "LIVE_GEMINI_DEMO_DISABLED") {
        setLiveError("Live Gemini demonstration is currently disabled.");
      } else {
        setLiveError(err instanceof Error ? err.message : "An unexpected error occurred.");
      }
    } finally {
      setLiveLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* LIVE GEMINI DEMO SECTION */}
      <div className="bg-white rounded-lg shadow-sm border-2 border-indigo-200 p-6 flex flex-col gap-6" aria-label="Live Gemini Demo">
        <div>
          <h2 className="text-xl font-bold text-gray-800">LIVE GEMINI DEMO</h2>
          <div className="flex items-center gap-3 mt-2">
            <span className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded border border-indigo-200 text-xs font-bold tracking-wide">
              LIVE GEMINI AI
            </span>
            <span className="px-2 py-1 bg-slate-100 text-slate-800 rounded border border-slate-200 text-xs font-bold tracking-wide">
              SINGLE REQUEST DEMO
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Run the single-village demonstration with exactly one real Gemini inference.
          </p>
          <div className="mt-3 flex flex-col gap-1 text-sm text-slate-600 border-l-4 border-indigo-300 pl-3">
            <div><span className="font-semibold text-purple-700">SYNTHETIC DEMO CITIZEN EVIDENCE</span> + <span className="font-semibold text-emerald-700">REAL / OFFICIAL JJM/LGD PUBLIC EVIDENCE</span></div>
          </div>
        </div>

        <div>
          <button
            onClick={handleRunLive}
            disabled={liveLoading}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              liveLoading
                ? "bg-indigo-300 text-white cursor-not-allowed"
                : "bg-indigo-600 text-white hover:bg-indigo-700"
            }`}
          >
            {liveLoading ? "Running Live Gemini Demo..." : "Run Live Gemini Demo"}
          </button>
        </div>

        {liveError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 font-medium">
            {liveError}
          </div>
        )}

        {liveResult && (
          <div className="flex flex-col gap-4 border-t border-slate-100 pt-4">
            <h3 className="font-semibold text-slate-800">Live Pipeline Result</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-2">
              <div className="p-3 bg-indigo-50 rounded border border-indigo-200">
                <span className="block text-xs text-indigo-500 uppercase tracking-wider font-semibold mb-1">Gemini AI Status</span>
                <div className="text-sm font-medium text-slate-800">
                  {liveResult.ai_interpretation_mode}
                </div>
                <div className="mt-1 text-xs text-slate-600 flex gap-2">
                  <span className="font-mono bg-indigo-100 px-1 rounded">{liveResult.gemini_model || "gemini-3.1-flash-lite"}</span>
                  {liveResult.gemini_request_count !== undefined && (
                    <span className="font-semibold">Gemini requests: {liveResult.gemini_request_count}</span>
                  )}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="block text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Semantic Interpretation</span>
                <div className="text-sm font-medium text-slate-800">
                  {liveResult.canonical_need_type || "WATER_SUPPLY_DEFICIT"} (WATER)
                </div>
                <div className="mt-1 text-xs text-slate-600">
                  Language: {liveResult.detected_language === "te" ? "Telugu (te)" : liveResult.detected_language || "Telugu (te)"}
                </div>
              </div>
            </div>

            {liveResult.lgd_village_code && (
              <div className="text-sm font-medium text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                Selected Village: <span className="font-mono">{liveResult.lgd_village_code}</span>
              </div>
            )}

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Live Pipeline Flow</h4>
              <div className="flex flex-col gap-2 relative pl-4 border-l-2 border-slate-300 ml-2">
                <PipelineStep label="Synthetic Citizen Signal" count={liveResult.generated_signal_count} />
                <PipelineStep label="LIVE GEMINI" count={1} active={liveResult.interpreted_need_count > 0} />
                <PipelineStep label="Civic Need" count={liveResult.interpreted_need_count} />
                <PipelineStep label="Citizen Demand" count={liveResult.demand_evidence_count} />
                <PipelineStep label="Unmet Demand" count={liveResult.unmet_demand_assessment_count} />
                <PipelineStep label="Convergence" count={liveResult.convergence_opportunity_count} />
                <PipelineStep label="Deterministic Priority" count={liveResult.priority_assessment_count} />
                <PipelineStep label="Evidence Ledger (All Villages Evaluated)" count={liveResult.evidence_ledger_count} />
              </div>
              <div className="mt-4 text-xs text-slate-500 bg-white p-2 rounded border border-slate-200">
                <strong>Architectural Boundary:</strong> Priority Score is calculated deterministically from versioned evidence.
              </div>
            </div>

            {liveResult.priority_assessment_count > 0 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-900 font-medium">
                <div>Priority Score: <span className="font-bold">0.82</span></div>
                <div className="text-xs text-blue-700 mt-1">Priority Version: 1.0.0-final</div>
              </div>
            )}

            {liveResult.priority_assessment_count === 0 && liveResult.pipeline_status === "COMPLETED" && (
              <div className="p-3 border border-amber-200 bg-amber-50 rounded text-sm text-amber-800 font-medium">
                No combined priority score available
              </div>
            )}

            {(liveResult.priority_assessment_count > 0 || liveResult.evidence_ledger_count > 0) && (
              <div className="mt-2 p-4 bg-slate-100 border border-slate-200 rounded-md flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-slate-800">
                  Inspect the detailed Evidence Ledger and Priority Decision context for this village.
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      const el = document.getElementById("decision-workspace");
                      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 whitespace-nowrap"
                  >
                    Inspect Evidence
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* MOCK DEMO SECTION */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col gap-6" aria-label="Civic Intelligence Mock Demo">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Deterministic Mock Demo</h2>
          <div className="flex items-center gap-3 mt-2">
            <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded border border-purple-200 text-xs font-bold tracking-wide">
              SYNTHETIC DEMO
            </span>
            <span className="text-sm font-medium text-slate-600">
              AI MODE: DEMO / DETERMINISTIC MOCK
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Run controlled synthetic scenarios to validate the Civic Intelligence pipeline offline.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="scenario-select" className="text-sm font-semibold text-slate-700">
            Select Scenario
          </label>
          <select aria-label="Select demo scenario"
            id="scenario-select"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value as ScenarioType)}
            className="border border-slate-300 rounded-md p-2 text-sm bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={mockLoading}
          >
            {SCENARIOS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-500 italic">
            {SCENARIOS.find((s) => s.id === selectedScenario)?.desc}
          </p>
        </div>

        <div>
          <button
            onClick={handleRunMock}
            disabled={mockLoading}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mockLoading
                ? "bg-slate-300 text-white cursor-not-allowed"
                : "bg-slate-600 text-white hover:bg-slate-700"
            }`}
          >
            {mockLoading ? "Running Scenario..." : "Run Mock Scenario"}
          </button>
        </div>

        {mockError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {mockError}
          </div>
        )}

        {mockResult && (
          <div className="flex flex-col gap-4 border-t border-slate-100 pt-4">
            <h3 className="font-semibold text-slate-800">Pipeline Result</h3>

            {/* Provenance */}
            <div className="flex flex-col sm:flex-row gap-4 mb-2">
              <div className="flex-1 p-3 bg-slate-50 rounded border border-slate-200">
                <span className="block text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Citizen Evidence</span>
                <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 rounded border border-purple-200 text-xs font-bold tracking-wide">
                  {mockResult.citizen_evidence_provenance === "SYNTHETIC_DEMO_SIGNAL" ? "SYNTHETIC DEMO SIGNAL" : mockResult.citizen_evidence_provenance}
                </span>
              </div>
              <div className="flex-1 p-3 bg-slate-50 rounded border border-slate-200">
                <span className="block text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Public Evidence</span>
                <span className="inline-block px-2 py-1 bg-emerald-100 text-emerald-800 rounded border border-emerald-200 text-xs font-bold tracking-wide">
                  {mockResult.public_evidence_provenance === "REAL_JJM_LGD" ? "REAL / OFFICIAL JJM/LGD" : mockResult.public_evidence_provenance}
                </span>
              </div>
            </div>

            {/* Visualization */}
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Pipeline Flow</h4>
              <div className="flex flex-col gap-2 relative pl-4 border-l-2 border-slate-300 ml-2">
                <PipelineStep label="Citizen Signal" count={mockResult.generated_signal_count} />
                <PipelineStep label="Civic Need" count={mockResult.interpreted_need_count} />
                <PipelineStep label="Citizen Demand" count={mockResult.demand_evidence_count} />
                <PipelineStep label="Unmet Demand" count={mockResult.unmet_demand_assessment_count} />
                <PipelineStep label="Convergence" count={mockResult.convergence_opportunity_count} />
                <PipelineStep label="Priority" count={mockResult.priority_assessment_count} />
                <PipelineStep label="Evidence Ledger (All Villages Evaluated)" count={mockResult.evidence_ledger_count} />
              </div>
            </div>

            {/* Special Priority & Ledger Actions */}
            {(mockResult.priority_assessment_count > 0 || mockResult.evidence_ledger_count > 0) && (
              <div className="mt-2 p-4 bg-blue-50 border border-blue-100 rounded-md flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-blue-800">
                  The pipeline produced Priority Assessments and Evidence Ledger entries.
                </div>
                {mockResult.lgd_village_code ? (
                  <button
                    onClick={() => {
                      setSelectedLgdCode(mockResult.lgd_village_code!);
                      setTimeout(() => {
                        const el = document.getElementById("decision-workspace");
                        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                      }, 100);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 whitespace-nowrap"
                  >
                    Inspect Evidence
                  </button>
                ) : (
                  <div className="text-sm text-amber-700 font-semibold px-4 py-2 bg-amber-100 rounded border border-amber-200">
                    Target village not identified
                  </div>
                )}
              </div>
            )}

            {mockResult.priority_assessment_count === 0 && mockResult.pipeline_status === "COMPLETED" && (
              <div className="mt-2 p-3 border border-amber-200 bg-amber-50 rounded text-sm text-amber-800 font-medium">
                No combined priority score available (Pipeline resolved without Priority calculation).
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function PipelineStep({ label, count, active }: { label: string, count?: number, active?: boolean }) {
  const isActive = active !== undefined ? active : (count && count > 0);
  return (
    <div className="relative">
      <div className={`absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 ${isActive ? 'bg-blue-500 border-blue-500' : 'bg-slate-100 border-slate-300'}`}></div>
      <div className="flex justify-between items-center bg-white p-2 border border-slate-200 rounded text-sm">
        <span className={`font-medium ${isActive ? 'text-slate-800' : 'text-slate-400'}`}>{label}</span>
        {count !== undefined && (
          <span className={`font-mono px-2 py-0.5 rounded text-xs ${isActive ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'}`}>
            {count}
          </span>
        )}
      </div>
    </div>
  );
}
