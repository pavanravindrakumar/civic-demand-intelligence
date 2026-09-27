"use client";

import React, { useState } from "react";
import { getVillageAnalytics } from "../lib/api";
import { useVillageContext } from "./VillageContext";

export default function VillageLookup() {
  const [lgdCode, setLgdCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setSelectedVillageContext, setSelectedLgdCode } = useVillageContext();

  const handleLookup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!lgdCode.trim() || lgdCode.length !== 6) {
      setError("Please enter a valid 6-digit LGD Village Code.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getVillageAnalytics(lgdCode.trim());
      // Convert PriorityResult into GeoFeatureProperties shape
      setSelectedVillageContext({
        lgd_village_code: data.lgd_village_code,
        village_name: "Selected via Lookup",
        district: "Unknown",
        block: "Unknown",
        panchayat: "Unknown",
        reported_household_gap: data.reported_household_gap,
        household_exposure: data.household_exposure,
        evidence_quality: data.evidence_quality,
        readiness: data.readiness,
        priority_score: data.priority_score
      });
      setSelectedLgdCode(data.lgd_village_code);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Failed to fetch village data.";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Village Analytics Lookup</h2>
          <p className="text-sm text-gray-500 mt-1">Inspect deterministic data for a specific village.</p>
        </div>

        <form onSubmit={handleLookup} className="flex gap-2 w-full md:w-auto">
          <input
            id="lgd-lookup"
            aria-label="6-digit LGD Code"
            type="text"
            value={lgdCode}
            onChange={(e) => setLgdCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="6-digit LGD Code"
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full md:w-48"
            disabled={loading}
            maxLength={6}
          />
          <button
            type="submit"
            disabled={loading || lgdCode.length !== 6}
            className="px-4 py-2 bg-slate-800 text-white rounded-md text-sm font-medium hover:bg-slate-900 focus:outline-none disabled:bg-slate-300 transition-colors"
          >
            {loading ? "Loading..." : "Lookup"}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}


    </div>
  );
}
