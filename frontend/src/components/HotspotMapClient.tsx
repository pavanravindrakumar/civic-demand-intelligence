"use client";

import React, { useEffect, useState, useMemo } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { getGeoHotspots, GeoFeatureCollection } from "../lib/api";
import L from "leaflet";
import { useVillageContext } from "./VillageContext";

// Component to handle auto-fitting bounds based on geojson data
function FitBounds({ data }: { data: GeoFeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    if (data.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(data as any);
        const bounds = geoJsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [20, 20] });
        }
      } catch (e) {
        // Fallback for invalid bounds
      }
    }
  }, [data, map]);
  return null;
}

export default function HotspotMapClient() {
  const [data, setData] = useState<GeoFeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { selectedVillageContext, setSelectedVillageContext, setSelectedLgdCode } = useVillageContext();

  const [districtFilter, setDistrictFilter] = useState<string>("");
  const [blockFilter, setBlockFilter] = useState<string>("");
  const [limitFilter, setLimitFilter] = useState<number>(100);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getGeoHotspots(
        districtFilter || undefined,
        blockFilter || undefined,
        limitFilter
      );
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load map data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApplyFilters = () => {
    fetchData();
  };

  // Intensity color logic based on reported gap
  const getColor = (gap: number) => {
    return gap > 500 ? "#800026" :
           gap > 200 ? "#BD0026" :
           gap > 100 ? "#E31A1C" :
           gap > 50  ? "#FC4E2A" :
           gap > 10  ? "#FD8D3C" :
           gap > 0   ? "#FEB24C" :
                       "#FFEDA0";
  };

  const geoJsonStyle = (feature: any) => {
    const gap = feature.properties?.reported_household_gap || 0;
    return {
      fillColor: getColor(gap),
      weight: 1,
      opacity: 1,
      color: "white",
      dashArray: "3",
      fillOpacity: 0.7,
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    layer.on({
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({
          weight: 3,
          color: "#666",
          dashArray: "",
          fillOpacity: 0.9,
        });
        target.bringToFront();
      },
      mouseout: (e) => {
        const target = e.target;
        // reset style
        target.setStyle(geoJsonStyle(feature));
      },
      click: () => {
        setSelectedLgdCode(feature.properties.lgd_village_code);
        setSelectedVillageContext(feature.properties);
      },
    });
  };

  return (
    <div className="flex flex-col gap-4 w-full h-full">
      {/* Controls */}
      <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm flex flex-col sm:flex-row gap-4 items-end">
        <div className="flex flex-col gap-1">
          <label htmlFor="filter-district" className="text-xs font-semibold text-slate-600">District</label>
          <input
            id="filter-district"
            type="text"
            className="border border-slate-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="All Districts"
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="filter-block" className="text-xs font-semibold text-slate-600">Block</label>
          <input
            id="filter-block"
            type="text"
            className="border border-slate-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="All Blocks"
            value={blockFilter}
            onChange={(e) => setBlockFilter(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="filter-limit" className="text-xs font-semibold text-slate-600">Top N Limits</label>
          <select
            id="filter-limit"
            className="border border-slate-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={limitFilter}
            onChange={(e) => setLimitFilter(Number(e.target.value))}
          >
            <option value={10}>Top 10</option>
            <option value={50}>Top 50</option>
            <option value={100}>Top 100</option>
            <option value={500}>Top 500</option>
            <option value={1000}>Top 1000 (Max)</option>
          </select>
        </div>
        <button
          onClick={handleApplyFilters}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-semibold py-1.5 px-4 rounded transition-colors"
        >
          {loading ? "Loading..." : "Apply Filters"}
        </button>
      </div>

      {/* Main Map Area */}
      <div className="flex flex-col lg:flex-row gap-4 h-[600px]">
        <div className="relative flex-1 bg-slate-100 border border-slate-200 rounded-lg overflow-hidden shadow-sm z-0">

          {error && (
            <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-white/80">
              <div className="text-red-600 bg-red-50 px-4 py-2 rounded shadow-sm border border-red-200">
                {error}
              </div>
            </div>
          )}

          {loading && !error && (
            <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-white/60">
              <span className="text-blue-600 font-semibold bg-white px-3 py-1 rounded shadow-sm border border-blue-100">Updating Map...</span>
            </div>
          )}

          <div className="absolute top-2 left-12 z-[500] bg-white px-2 py-1 rounded shadow-sm border border-slate-200 text-xs font-semibold text-slate-700 pointer-events-none">
            Reported Household Tap-Connection Gap
          </div>

          <div className="absolute top-2 right-2 z-[500] bg-orange-100 text-orange-800 border border-orange-300 px-2 py-1 rounded shadow-sm text-xs font-bold tracking-wide pointer-events-none">
            PUBLIC EVIDENCE ONLY
          </div>

          <MapContainer
            center={[15.9129, 79.74]}
            zoom={6}
            style={{ height: "100%", width: "100%", zIndex: 1 }}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {data && data.features.length > 0 && (
              <>
                <GeoJSON
                  key={JSON.stringify(data.features.map(f => f.properties.lgd_village_code))}
                  data={data as any}
                  style={geoJsonStyle}
                  onEachFeature={onEachFeature}
                />
                <FitBounds data={data} />
              </>
            )}
          </MapContainer>

          {data && data.features.length === 0 && !loading && (
             <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-transparent pointer-events-none">
               <span className="text-slate-600 bg-white/90 px-3 py-1 rounded shadow-sm border border-slate-200">No villages found for current filters.</span>
             </div>
          )}

          {/* Legend */}
          <div className="absolute bottom-6 right-2 z-[500] bg-white/95 p-3 rounded shadow-sm border border-slate-200 pointer-events-none text-xs">
            <h4 className="font-semibold text-slate-700 mb-2">Household Gap</h4>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#800026] border border-slate-300"></span>&gt; 500</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#BD0026] border border-slate-300"></span>201 - 500</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#E31A1C] border border-slate-300"></span>101 - 200</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#FC4E2A] border border-slate-300"></span>51 - 100</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#FD8D3C] border border-slate-300"></span>11 - 50</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#FEB24C] border border-slate-300"></span>1 - 10</div>
              <div className="flex items-center gap-2"><span className="w-4 h-4 bg-[#FFEDA0] border border-slate-300"></span>0</div>
            </div>
          </div>
        </div>

        {/* Selected Detail Panel */}
        <div className="w-full lg:w-64 bg-white border border-slate-200 rounded-lg shadow-sm p-4 flex flex-col">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mb-3">Map Selection</h3>
          {selectedVillageContext ? (
            <div className="flex flex-col gap-3 text-sm">
              <div>
                <span className="block text-xs text-slate-500 font-semibold">Village</span>
                <span className="block text-slate-900 font-medium">{selectedVillageContext.village_name}</span>
                <span className="block text-xs text-slate-400">LGD: {selectedVillageContext.lgd_village_code}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="block text-xs text-slate-500 font-semibold">District</span>
                  <span className="block text-slate-700 text-xs">{selectedVillageContext.district}</span>
                </div>
                <div>
                  <span className="block text-xs text-slate-500 font-semibold">Block</span>
                  <span className="block text-slate-700 text-xs">{selectedVillageContext.block}</span>
                </div>
              </div>
              <div className="mt-2 bg-blue-50 border border-blue-100 rounded p-2">
                <span className="block text-xs text-blue-800 font-semibold mb-1">Reported Connection Gap</span>
                <span className="block text-xl font-bold text-blue-700">
                  {selectedVillageContext.reported_household_gap.toLocaleString()}
                </span>
                <span className="block text-xs text-blue-600 mt-1">
                  Exposure: {selectedVillageContext.household_exposure.toLocaleString()} HHs
                </span>
              </div>

              <div className="mt-2">
                 <span className="block text-xs text-slate-500 font-semibold">Evidence Quality</span>
                 <span className="inline-block mt-1 bg-slate-100 border border-slate-200 text-slate-700 text-xs px-2 py-0.5 rounded">
                   {selectedVillageContext.evidence_quality.replace(/_/g, " ")}
                 </span>
              </div>

              <div className="mt-2 pt-2 border-t border-slate-100">
                 <span className="text-xs text-blue-600 font-medium">Detailed analysis is shown in the workspace below.</span>
              </div>
            </div>
          ) : (
            <div className="text-slate-500 text-sm flex-1 flex items-center justify-center text-center">
              Click on a village on the map to select it.
            </div>
          )}

          <div className="mt-auto pt-4 text-[10px] text-slate-400 text-center border-t border-slate-100 leading-tight">
            Map Boundaries &copy; Geological Survey of India / NWIC.
            <br />
            77 analytical villages do not have matched boundary geometry and are not plotted.
          </div>
        </div>
      </div>
    </div>
  );
}
