"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { GeoFeatureProperties } from "../lib/api";

interface VillageContextType {
  selectedLgdCode: string | null;
  selectedVillageContext: GeoFeatureProperties | null;
  setSelectedLgdCode: (code: string | null) => void;
  setSelectedVillageContext: (context: GeoFeatureProperties | null) => void;
}

const VillageContext = createContext<VillageContextType | undefined>(undefined);

export function VillageProvider({ children }: { children: ReactNode }) {
  const [selectedLgdCode, setSelectedLgdCode] = useState<string | null>(null);
  const [selectedVillageContext, setSelectedVillageContext] = useState<GeoFeatureProperties | null>(null);

  const handleSetLgdCode = (code: string | null) => {
    setSelectedLgdCode(code);
    if (!code) {
      setSelectedVillageContext(null);
    }
  };

  return (
    <VillageContext.Provider
      value={{
        selectedLgdCode,
        selectedVillageContext,
        setSelectedLgdCode: handleSetLgdCode,
        setSelectedVillageContext,
      }}
    >
      {children}
    </VillageContext.Provider>
  );
}

export function useVillageContext() {
  const context = useContext(VillageContext);
  if (context === undefined) {
    throw new Error("useVillageContext must be used within a VillageProvider");
  }
  return context;
}
