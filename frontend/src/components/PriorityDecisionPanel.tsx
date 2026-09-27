"use client";

import React, { useState, useEffect } from "react";
import {
  getPriorityAssessments,
  getEvidenceLedgerByPriorityAssessmentId,
  PriorityAssessmentResponse,
  EvidenceLedgerEntry,
  FactorExplanation
} from "../lib/api";

interface Props {
  lgdVillageCode: string;
}

export default function PriorityDecisionPanel({ lgdVillageCode }: Props) {
  const [assessment, setAssessment] = useState<PriorityAssessmentResponse | null>(null);
  const [ledgerEntries, setLedgerEntries] = useState<EvidenceLedgerEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [ledgerLoading, setLedgerLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ledgerError, setLedgerError] = useState<string | null>(null);
  const [showLedger, setShowLedger] = useState(false);

  useEffect(() => {
    async function fetchPriority() {
      if (!lgdVillageCode) return;

      setLoading(true);
      setError(null);
      setAssessment(null);
      setLedgerEntries(null);
      setShowLedger(false);

      try {
        const results = await getPriorityAssessments({ lgd_village_code: lgdVillageCode, limit: "1" });
        if (results && results.length > 0) {
          setAssessment(results[0]);
        } else {
          setError("Priority Assessment not found for this village.");
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to fetch priority assessment.");
      } finally {
        setLoading(false);
      }
    }
    fetchPriority();
  }, [lgdVillageCode]);

  const handleViewEvidence = async () => {
    if (!assessment) return;

    if (showLedger) {
      setShowLedger(false);
      return;
    }

    if (ledgerEntries) {
      setShowLedger(true);
      return;
    }

    setLedgerLoading(true);
    setLedgerError(null);
    try {
      const data = await getEvidenceLedgerByPriorityAssessmentId(assessment.priority_assessment_id);
      setLedgerEntries(data);
      setShowLedger(true);
    } catch (err: unknown) {
      setLedgerError(err instanceof Error ? err.message : "Failed to fetch evidence ledger.");
    } finally {
      setLedgerLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">Loading priority data...</div>;
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Priority & Evidence Decision Panel</h2>
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!assessment) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col gap-4">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Priority & Evidence Decision Panel</h2>
        <p className="text-sm text-gray-500 mt-1">LGD Village Code: {assessment.lgd_village_code}</p>
      </div>

      {/* Provenance Tags */}
      <div className="flex flex-wrap gap-2 text-xs font-bold tracking-wide">
        {assessment.citizen_evidence_provenance === "SYNTHETIC_DEMO_SIGNAL" && (
          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded border border-purple-200">
            SYNTHETIC DEMO CITIZEN EVIDENCE
          </span>
        )}
        {assessment.public_evidence_provenance && (
          <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded border border-emerald-200">
            REAL / OFFICIAL PUBLIC EVIDENCE
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
        <div className="flex flex-col border border-gray-200 rounded-md p-3 bg-gray-50">
          <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Priority Score</span>
          {assessment.priority_score !== null ? (
            <span className="text-3xl font-bold text-blue-700">
              {assessment.priority_score.toFixed(3)}
            </span>
          ) : (
            <span className="text-sm font-medium text-amber-600 mt-1">
              No combined priority score available
            </span>
          )}
          <span className="text-xs text-gray-400 mt-1">
            Status: {assessment.eligibility_status}
          </span>
        </div>

        <div className="flex flex-col border border-gray-200 rounded-md p-3 bg-gray-50 justify-center">
          <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Engine Version</span>
          <span className="text-sm font-bold text-gray-700">{assessment.priority_version}</span>
          <span className="text-xs text-gray-400 mt-1">
            Sector: {assessment.sector}
          </span>
        </div>
      </div>

      {/* Factor Explanations */}
      {assessment.priority_score !== null && assessment.factors && Object.keys(assessment.factors).length > 0 && (
        <div className="mt-2 border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-slate-50 px-4 py-2 border-b border-gray-200">
            <h3 className="font-semibold text-slate-800 text-sm uppercase tracking-wider">Why this surfaced? (Score Factors)</h3>
          </div>
          <div className="divide-y divide-gray-100">
            {assessment.factors["infrastructure_gap"] && (
              <FactorRow title="Infrastructure Gap" factor={assessment.factors["infrastructure_gap"]} />
            )}
            {assessment.factors["validated_demand"] && (
              <FactorRow title="Validated Citizen Demand" factor={assessment.factors["validated_demand"]} />
            )}
            {assessment.factors["household_exposure"] && (
              <FactorRow title="Exposure Proxy" factor={assessment.factors["household_exposure"]} />
            )}
          </div>
        </div>
      )}

      {/* Evidence Ledger Button */}
      <div className="mt-2">
        <button
          onClick={handleViewEvidence}
          disabled={ledgerLoading}
          className="px-4 py-2 bg-slate-800 text-white rounded-md text-sm font-medium hover:bg-slate-900 focus:outline-none transition-colors"
        >
          {ledgerLoading ? "Loading Ledger..." : showLedger ? "Hide Evidence Ledger" : "View Evidence Ledger"}
        </button>
      </div>

      {/* Ledger Drill Down */}
      {showLedger && ledgerError && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200">
          {ledgerError}
        </div>
      )}

      {showLedger && ledgerEntries && ledgerEntries.length > 0 && (
        <div className="mt-2 border-l-4 border-slate-700 pl-4 py-2 flex flex-col gap-3">
          {ledgerEntries.map(entry => (
            <div key={entry.ledger_entry_id} className="bg-slate-50 p-4 rounded-md border border-slate-200 text-sm font-mono flex flex-col gap-1 overflow-x-auto">
              <div className="font-semibold text-slate-700 border-b border-slate-200 pb-1 mb-1">
                Audit Record: {entry.ledger_entry_id}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <div><span className="text-slate-500">priority_assessment_id:</span> {entry.priority_assessment_id}</div>
                <div><span className="text-slate-500">convergence_opportunity_id:</span> {entry.convergence_opportunity_id}</div>
                <div><span className="text-slate-500">unmet_demand_assessment_id:</span> {entry.unmet_demand_assessment_id}</div>
                <div><span className="text-slate-500">generated_at:</span> {entry.generated_at}</div>

                <div className="mt-2 text-slate-700 font-semibold col-span-1 md:col-span-2">Evidence Measurements</div>
                {entry.reported_household_gap !== null && (
                  <div><span className="text-slate-500">reported_household_gap:</span> {entry.reported_household_gap}</div>
                )}
                {entry.household_exposure !== null && (
                  <div><span className="text-slate-500">household_exposure:</span> {entry.household_exposure}</div>
                )}
                {entry.signal_count !== null && (
                  <div><span className="text-slate-500">signal_count:</span> {entry.signal_count}</div>
                )}
                {entry.distinct_submitter_count !== null && (
                  <div><span className="text-slate-500">distinct_submitter_count:</span> {entry.distinct_submitter_count}</div>
                )}

                <div className="mt-2 text-slate-700 font-semibold col-span-1 md:col-span-2">Integrity</div>
                <div className="col-span-1 md:col-span-2 break-all">
                  <span className="text-slate-500">record_hash:</span> {entry.record_hash}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FactorRow({ title, factor }: { title: string, factor: FactorExplanation }) {
  return (
    <div className="p-3 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
      <div className="font-medium text-slate-700">{title}</div>
      <div className="flex gap-4 text-sm bg-white p-2 rounded border border-gray-100 shadow-sm w-full sm:w-auto overflow-x-auto justify-between sm:justify-end">
        <div className="flex flex-col items-center px-2 border-r border-gray-100">
          <span className="text-xs text-gray-400">Input</span>
          <span className="font-mono">{factor.normalized_input.toFixed(3)}</span>
        </div>
        <div className="flex flex-col items-center px-2 border-r border-gray-100">
          <span className="text-xs text-gray-400">Weight</span>
          <span className="font-mono">{factor.configured_weight.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center px-2">
          <span className="text-xs text-gray-400">Contrib</span>
          <span className="font-mono font-bold text-slate-700">{factor.contribution.toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
}
