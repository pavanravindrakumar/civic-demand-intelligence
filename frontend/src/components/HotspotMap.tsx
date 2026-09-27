"use client";

import dynamic from "next/dynamic";
import React from "react";

// Dynamically import the map client component with SSR disabled
const HotspotMapClient = dynamic(() => import("./HotspotMapClient"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-96 bg-slate-100 flex items-center justify-center border border-slate-200 rounded-lg">
      <div className="flex flex-col items-center">
        <svg
          className="animate-spin h-8 w-8 text-blue-600 mb-2"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p className="text-sm text-slate-500 font-medium">Initializing Map...</p>
      </div>
    </div>
  ),
});

export default function HotspotMap() {
  return <HotspotMapClient />;
}
