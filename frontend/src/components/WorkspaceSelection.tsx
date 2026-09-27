"use client";

import React from "react";
import VillageLookup from "./VillageLookup";
import PriorityDecisionPanel from "./PriorityDecisionPanel";
import { useVillageContext } from "./VillageContext";

export default function WorkspaceSelection() {
  const { selectedLgdCode } = useVillageContext();

  return (
    <div className="flex flex-col gap-6">
      <VillageLookup />

      {selectedLgdCode ? (
        <div id="decision-workspace" className="scroll-mt-6">
          <PriorityDecisionPanel lgdVillageCode={selectedLgdCode} />
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-12 flex flex-col items-center justify-center text-center text-slate-500 shadow-sm">
          <svg className="w-12 h-12 text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-700 mb-1">No Village Selected</h3>
          <p className="text-sm max-w-md">
            Select a village from the Hotspot Map or enter an LGD Village Code above to view its Priority Assessment and Evidence Ledger.
          </p>
        </div>
      )}
    </div>
  );
}
