import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DemoPanel from "../components/DemoPanel";
import * as api from "../lib/api";

// Mock the API client
vi.mock("../lib/api", async () => {
  const actual = await vi.importActual("../lib/api");
  return {
    ...actual,
    runDemoScenario: vi.fn(),
    runLiveDemoScenario: vi.fn(),
  };
});

vi.mock("../components/VillageContext", () => ({
  useVillageContext: () => ({
    selectedLgdCode: null,
    setSelectedLgdCode: vi.fn(),
  }),
}));

describe("DemoPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders correctly on initial load", () => {
    render(<DemoPanel />);
    expect(screen.getByText("Deterministic Mock Demo")).toBeDefined();
    expect(screen.getByText("SYNTHETIC DEMO")).toBeDefined();
    expect(screen.getByText("AI MODE: DEMO / DETERMINISTIC MOCK")).toBeDefined();

    // Check scenario catalog
    const select = screen.getByRole("combobox");
    expect(select).toBeDefined();
    expect(screen.getByText("Water Convergence")).toBeDefined();
    expect(screen.getByText("Water (No Public Gap)")).toBeDefined();
    expect(screen.getByText("Non-Water Demand")).toBeDefined();
    expect(screen.getByText("Unresolved Geography")).toBeDefined();
  });

  it("displays loading state when running a scenario", async () => {
    // Return a never-resolving promise to simulate loading
    vi.mocked(api.runDemoScenario).mockImplementation(() => new Promise(() => {}));

    render(<DemoPanel />);

    const runBtn = screen.getByRole("button", { name: "Run Mock Scenario" });
    fireEvent.click(runBtn);

    expect(screen.getByRole("button", { name: "Running Scenario..." })).toBeDefined();
    expect(screen.getByRole("combobox")).toHaveProperty("disabled", true);
  });

  it("handles successful WATER_CONVERGENCE scenario", async () => {
    vi.mocked(api.runDemoScenario).mockResolvedValueOnce({
      scenario_id: "WATER_CONVERGENCE",
      simulation_version: "demo-v1.0",
      pipeline_status: "COMPLETED",
      ai_interpretation_mode: "DEMO / DETERMINISTIC MOCK",
      generated_signal_count: 5,
      interpreted_need_count: 5,
      demand_evidence_count: 1,
      unmet_demand_assessment_count: 1,
      convergence_opportunity_count: 1,
      priority_assessment_count: 1,
      evidence_ledger_count: 1,
      citizen_evidence_provenance: "SYNTHETIC_DEMO_SIGNAL",
      public_evidence_provenance: "REAL_JJM_LGD",
      lgd_village_code: "123456"
    });

    render(<DemoPanel />);

    // Use WATER_CONVERGENCE
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "WATER_CONVERGENCE" } });

    const runBtn = screen.getByRole("button", { name: "Run Mock Scenario" });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText("Pipeline Result")).toBeDefined();
    });

    // Provenance strict tags
    expect(screen.getByText("SYNTHETIC DEMO SIGNAL")).toBeDefined();
    expect(screen.getByText("REAL / OFFICIAL JJM/LGD")).toBeDefined();

    // Pipeline counts
    const count5 = screen.getAllByText("5");
    expect(count5.length).toBeGreaterThanOrEqual(2); // generated signals and needs

    // Inspect Evidence button appears
    expect(screen.getByRole("button", { name: "Inspect Evidence" })).toBeDefined();
  });

  it("handles scenario with zero priority (WATER_NO_PUBLIC_GAP)", async () => {
    vi.mocked(api.runDemoScenario).mockResolvedValueOnce({
      scenario_id: "WATER_NO_PUBLIC_GAP",
      simulation_version: "demo-v1.0",
      pipeline_status: "COMPLETED",
      ai_interpretation_mode: "DEMO / DETERMINISTIC MOCK",
      generated_signal_count: 1,
      interpreted_need_count: 1,
      demand_evidence_count: 1,
      unmet_demand_assessment_count: 1, // Let's say it makes one but gap is 0
      convergence_opportunity_count: 0,
      priority_assessment_count: 0,
      evidence_ledger_count: 0,
      citizen_evidence_provenance: "SYNTHETIC_DEMO_SIGNAL",
      public_evidence_provenance: "REAL_JJM_LGD",
      lgd_village_code: "123456"
    });

    render(<DemoPanel />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "WATER_NO_PUBLIC_GAP" } });

    const runBtn = screen.getByRole("button", { name: "Run Mock Scenario" });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText("Pipeline Result")).toBeDefined();
    });

    // Check for no-score explicit text
    expect(screen.getByText("No combined priority score available (Pipeline resolved without Priority calculation).")).toBeDefined();

    // Inspect Evidence button should NOT appear
    expect(screen.queryByRole("button", { name: "Inspect Evidence" })).toBeNull();
  });

  it("handles API error correctly", async () => {
    vi.mocked(api.runDemoScenario).mockRejectedValueOnce(new Error("Pipeline Error at stage: Unmet Demand"));

    render(<DemoPanel />);

    const runBtn = screen.getByRole("button", { name: "Run Mock Scenario" });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText("Pipeline Error at stage: Unmet Demand")).toBeDefined();
    });

    // Pipeline result should NOT be rendered
    expect(screen.queryByText("Pipeline Result")).toBeNull();
  });

  it("never sends arbitrary scenarios", async () => {
    render(<DemoPanel />);

    const select = screen.getByRole("combobox") as HTMLSelectElement;

    // Verify options are strictly limited
    const options = Array.from(select.options).map(opt => opt.value);
    expect(options).toEqual([
      "WATER_CONVERGENCE",
      "WATER_NO_PUBLIC_GAP",
      "NON_WATER_DEMAND",
      "UNRESOLVED_GEOGRAPHY"
    ]);
  });

  it("Live Demo - renders correctly and distinguishes from mock demo", () => {
    render(<DemoPanel />);
    expect(screen.getByText("LIVE GEMINI DEMO")).toBeDefined();
    expect(screen.getByText("LIVE GEMINI AI")).toBeDefined();
    expect(screen.getByText("SINGLE REQUEST DEMO")).toBeDefined();

    const liveRunBtn = screen.getByRole("button", { name: "Run Live Gemini Demo" });
    expect(liveRunBtn).toBeDefined();

    // Ensure no client-side parameters are available for live demo (like scenario selection)
    // The scenario selector is for the mock demo. Let's verify it's not in the live demo section.
    // (By visual structure, but we can just ensure only one select exists)
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBe(1); // Only for mock demo
  });

  it("Live Demo - handles successful live demo response and displays correct bounds", async () => {
    vi.mocked(api.runLiveDemoScenario).mockResolvedValueOnce({
      scenario_id: "WATER_CONVERGENCE",
      simulation_version: "live-demo-v1.0",
      pipeline_status: "COMPLETED",
      ai_interpretation_mode: "LIVE GEMINI DEMONSTRATION",
      gemini_request_count: 1,
      gemini_model: "gemini-3.1-flash-lite",
      canonical_need_type: "WATER_SUPPLY_DEFICIT",
      detected_language: "te",
      generated_signal_count: 1,
      interpreted_need_count: 1,
      demand_evidence_count: 1,
      unmet_demand_assessment_count: 1,
      convergence_opportunity_count: 1,
      priority_assessment_count: 1,
      evidence_ledger_count: 1,
      citizen_evidence_provenance: "SYNTHETIC_DEMO_SIGNAL",
      public_evidence_provenance: "REAL_JJM_LGD",
      lgd_village_code: "275084"
    });

    render(<DemoPanel />);

    const liveRunBtn = screen.getByRole("button", { name: "Run Live Gemini Demo" });
    fireEvent.click(liveRunBtn);

    // Check loading state
    expect(screen.getByRole("button", { name: "Running Live Gemini Demo..." })).toBeDefined();
    expect(liveRunBtn).toHaveProperty("disabled", true);

    await waitFor(() => {
      expect(screen.getByText("Live Pipeline Result")).toBeDefined();
    });

    // Verifies rendering exact requested info
    expect(screen.getByText("Gemini requests: 1")).toBeDefined();
    expect(screen.getByText("gemini-3.1-flash-lite")).toBeDefined();
    expect(screen.getByText("WATER_SUPPLY_DEFICIT (WATER)")).toBeDefined();
    expect(screen.getByText("Language: Telugu (te)")).toBeDefined();
    expect(screen.getByText("275084")).toBeDefined(); // selected village

    expect(screen.getByText("Priority Score is calculated deterministically from versioned evidence.")).toBeDefined();
    expect(screen.getByText("Priority Version: 1.0.0-final")).toBeDefined();

    // Visual visualization boundary checks (LIVE GEMINI active)
    expect(screen.getByText("LIVE GEMINI")).toBeDefined();
  });

  it("Live Demo - handles LIVE_GEMINI_DEMO_DISABLED error", async () => {
    vi.mocked(api.runLiveDemoScenario).mockRejectedValueOnce(new Error("LIVE_GEMINI_DEMO_DISABLED"));

    render(<DemoPanel />);

    const liveRunBtn = screen.getByRole("button", { name: "Run Live Gemini Demo" });
    fireEvent.click(liveRunBtn);

    await waitFor(() => {
      expect(screen.getByText("Live Gemini demonstration is currently disabled.")).toBeDefined();
    });
  });
});
