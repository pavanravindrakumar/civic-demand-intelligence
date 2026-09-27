import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import HotspotMapClient from "../components/HotspotMapClient";
import * as api from "../lib/api";

// Mock the react-leaflet components since they require a real DOM / WebGL sometimes
vi.mock("react-leaflet", () => {
  return {
    MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => <div data-testid="tile-layer" />,
    GeoJSON: ({ data }: any) => <div data-testid="geojson-layer" data-features={data.features.length} />,
    useMap: () => ({
      fitBounds: vi.fn(),
    }),
  };
});

// Mock Leaflet
vi.mock("leaflet", () => {
  return {
    default: {
      geoJSON: () => ({
        getBounds: () => ({
          isValid: () => true,
        }),
      }),
    },
  };
});

vi.mock("../components/VillageContext", () => ({
  useVillageContext: () => ({
    selectedLgdCode: null,
    selectedVillageContext: null,
    setSelectedLgdCode: vi.fn(),
    setSelectedVillageContext: vi.fn(),
  }),
}));

describe("HotspotMapClient", () => {
  const mockHotspots = {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [80, 15] },
        properties: {
          lgd_village_code: "123",
          village_name: "Test Village",
          district: "Test District",
          block: "Test Block",
          panchayat: "Test Panchayat",
          reported_household_gap: 150,
          household_exposure: 500,
          evidence_quality: "HIGH_CONFIDENCE" as any,
          readiness: "PUBLIC_EVIDENCE_ONLY" as any,
          priority_score: null,
        }
      }
    ]
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", async () => {
    vi.spyOn(api, "getGeoHotspots").mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<HotspotMapClient />);
    expect(screen.getByText(/Updating Map\.\.\./i)).toBeInTheDocument();
  });

  it("renders error state when API fails", async () => {
    vi.spyOn(api, "getGeoHotspots").mockRejectedValue(new Error("API Error"));
    render(<HotspotMapClient />);

    await waitFor(() => {
      expect(screen.getByText("API Error")).toBeInTheDocument();
    });
  });

  it("renders map features successfully", async () => {
    vi.spyOn(api, "getGeoHotspots").mockResolvedValue(mockHotspots);
    render(<HotspotMapClient />);

    await waitFor(() => {
      expect(screen.getByTestId("geojson-layer")).toBeInTheDocument();
      expect(screen.getByTestId("geojson-layer")).toHaveAttribute("data-features", "1");
    });

    // Check metric semantics are displayed
    expect(screen.getByText("Reported Household Tap-Connection Gap")).toBeInTheDocument();
    expect(screen.getByText("PUBLIC EVIDENCE ONLY")).toBeInTheDocument();
  });

  it("calls API with correct default limit", async () => {
    const spy = vi.spyOn(api, "getGeoHotspots").mockResolvedValue({ type: "FeatureCollection", features: [] });
    render(<HotspotMapClient />);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith(undefined, undefined, 100);
    });
  });
});
