"use client";

import React, { useEffect, useState } from "react";
import { getAnalyticsSummary, AnalyticsSummary } from "../lib/api";

export default function AnalyticsOverview() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await getAnalyticsSummary();
        setSummary(data);
        setError(null);
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : "Failed to load summary.";
        setError(errMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col gap-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-200 rounded"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-md"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6 flex items-center justify-center text-red-600 bg-red-50">
        <p>{error}</p>
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800">National Overview</h2>
          <p className="text-sm text-gray-500 mt-1">Deterministic metrics derived from the JJM/LGD Analytics Dataset.</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span
            className={`text-xs font-semibold px-2 py-1 rounded-full ${
              summary.readiness_state === "PUBLIC_EVIDENCE_ONLY"
                ? "bg-amber-100 text-amber-800 border border-amber-200"
                : "bg-blue-100 text-blue-800 border border-blue-200"
            }`}
          >
            {summary.readiness_state.replace(/_/g, " ")}
          </span>
          <span className="text-xs text-gray-400 font-mono">Ver: {summary.calculation_version}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-50 border border-gray-100 p-4 rounded-lg flex flex-col justify-center">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide">Villages Analyzed</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{summary.total_villages_analyzed.toLocaleString()}</p>
        </div>

        <div className="bg-gray-50 border border-gray-100 p-4 rounded-lg flex flex-col justify-center">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Households</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{summary.total_households.toLocaleString()}</p>
        </div>

        <div className="bg-gray-50 border border-gray-100 p-4 rounded-lg flex flex-col justify-center">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide">Reported FHTC</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{summary.total_fhtc.toLocaleString()}</p>
        </div>

        <div className="bg-red-50 border border-red-100 p-4 rounded-lg flex flex-col justify-center">
          <h3 className="text-xs font-medium text-red-800 uppercase tracking-wide">Reported Household Tap-Connection Gap</h3>
          <p className="text-2xl font-bold text-red-600 mt-2">{summary.total_reported_household_gap.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
