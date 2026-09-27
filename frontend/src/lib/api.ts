import { PriorityAssessmentResponse, EvidenceLedgerEntry } from "./api_priority_types";
export * from "./api_priority_types";

export interface ToolCallMetadata {
  name: string;
  args: Record<string, unknown>;
}

export interface ProvenanceMetadata {
  source_dataset?: string | null;
  calculation_version?: string | null;
}

export interface CopilotMetadata {
  tool_calls: ToolCallMetadata[];
  provenance: ProvenanceMetadata[];
}

export interface CopilotChatResponse {
  text: string;
  status: string;
  error_message?: string | null;
  metadata: CopilotMetadata;
}

export type ReadinessState = "READY" | "INCOMPLETE_DEMAND" | "PUBLIC_EVIDENCE_ONLY" | "INVALID_INPUTS";

export interface AnalyticsSummary {
  total_villages_analyzed: number;
  total_households: number;
  total_fhtc: number;
  total_reported_household_gap: number;
  readiness_state: ReadinessState;
  calculation_version: string;
  data_source: string;
}

export type ScenarioType = "WATER_CONVERGENCE" | "WATER_NO_PUBLIC_GAP" | "NON_WATER_DEMAND" | "UNRESOLVED_GEOGRAPHY";

export interface DemoScenarioRunRequest {
  scenario_id: ScenarioType;
  simulation_version?: string;
  seed?: string;
  batch_size?: number;
}

export interface DemoScenarioRunResponse {
  scenario_id: string;
  simulation_version: string;
  pipeline_status: string;
  ai_interpretation_mode: string;

  lgd_village_code?: string | null;

  generated_signal_count: number;
  interpreted_need_count: number;
  demand_evidence_count: number;
  unmet_demand_assessment_count: number;
  convergence_opportunity_count: number;
  priority_assessment_count: number;
  evidence_ledger_count: number;

  citizen_evidence_provenance: string;
  public_evidence_provenance: string;

  error_stage?: string | null;
  error_code?: string | null;
}

export interface LiveDemoResponse extends DemoScenarioRunResponse {
  gemini_request_count: number;
  gemini_model?: string | null;
  canonical_need_type?: string | null;
  detected_language?: string | null;
}

export type EvidenceQuality = "HIGH_CONFIDENCE" | "PARTIAL" | "CONFLICTING" | "MISSING";

export interface PriorityResult {
  lgd_village_code: string;
  readiness: ReadinessState;
  evidence_quality: EvidenceQuality;
  calculation_version: string;
  normalized_gap: number;
  normalized_exposure: number;
  normalized_demand: number;
  reported_household_gap: number;
  household_exposure: number;
  priority_score?: number | null;
}

export interface GeoFeatureProperties {
  lgd_village_code: string;
  village_name: string;
  district: string;
  block: string;
  panchayat: string;
  reported_household_gap: number;
  household_exposure: number;
  evidence_quality: EvidenceQuality;
  readiness: ReadinessState;
  priority_score?: number | null;
}

export interface GeoFeature {
  type: "Feature";
  geometry: {
    type: "Polygon" | "MultiPolygon" | "Point";
    coordinates: any[];
  };
  properties: GeoFeatureProperties;
}

export interface GeoFeatureCollection {
  type: "FeatureCollection";
  crs?: {
    type: string;
    properties: {
      name: string;
    };
  };
  features: GeoFeature[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendCopilotMessage(message: string): Promise<CopilotChatResponse> {
  const response = await fetch(`${API_URL}/api/copilot/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    let errorDetail = "An internal error occurred.";
    try {
      const errorData = await response.json();
      if (errorData.detail) errorDetail = errorData.detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const response = await fetch(`${API_URL}/api/analytics/summary`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch analytics summary.");
  }
  return response.json();
}

export async function getVillageAnalytics(lgdCode: string): Promise<PriorityResult> {
  const response = await fetch(`${API_URL}/api/analytics/village/${lgdCode}`, {
    method: "GET",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Village with LGD code ${lgdCode} not found.`);
    }
    throw new Error("Failed to fetch village analytics.");
  }
  return response.json();
}

export async function getGeoHotspots(district?: string, block?: string, limit: number = 100): Promise<GeoFeatureCollection> {
  const params = new URLSearchParams();
  if (district) params.append("district", district);
  if (block) params.append("block", block);
  params.append("limit", limit.toString());

  const response = await fetch(`${API_URL}/api/geo/hotspots?${params.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch geo hotspots.");
  }
  return response.json();
}

export async function getPriorityAssessments(params?: Record<string, string>): Promise<PriorityAssessmentResponse[]> {
  const qs = new URLSearchParams(params || {}).toString();
  const url = qs ? `${API_URL}/api/priority/assessments?${qs}` : `${API_URL}/api/priority/assessments`;
  const response = await fetch(url, { method: "GET" });
  if (!response.ok) {
    throw new Error("Failed to fetch priority assessments.");
  }
  return response.json();
}

export async function getPriorityAssessmentById(id: string): Promise<PriorityAssessmentResponse> {
  const response = await fetch(`${API_URL}/api/priority/assessments/${id}`, { method: "GET" });
  if (!response.ok) {
    if (response.status === 404) throw new Error("Priority Assessment not found.");
    throw new Error("Failed to fetch priority assessment detail.");
  }
  return response.json();
}

export async function getEvidenceLedger(params?: Record<string, string>): Promise<EvidenceLedgerEntry[]> {
  const qs = new URLSearchParams(params || {}).toString();
  const url = qs ? `${API_URL}/api/evidence/ledger?${qs}` : `${API_URL}/api/evidence/ledger`;
  const response = await fetch(url, { method: "GET" });
  if (!response.ok) {
    throw new Error("Failed to fetch evidence ledger.");
  }
  return response.json();
}

export async function getEvidenceLedgerByPriorityAssessmentId(priorityAssessmentId: string): Promise<EvidenceLedgerEntry[]> {
  const response = await fetch(`${API_URL}/api/evidence/ledger/${priorityAssessmentId}`, { method: "GET" });
  if (!response.ok) {
    if (response.status === 404) throw new Error("Evidence ledger entry not found.");
    throw new Error("Failed to fetch evidence ledger detail.");
  }
  return response.json();
}

export async function runDemoScenario(request: DemoScenarioRunRequest): Promise<DemoScenarioRunResponse> {
  const response = await fetch(`${API_URL}/api/demo/scenarios/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorDetail = "Failed to run demo scenario.";
    try {
      const errorData = await response.json();
      if (errorData.detail?.stage) {
        errorDetail = `Pipeline Error at stage: ${errorData.detail.stage}`;
      } else if (errorData.detail) {
        errorDetail = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function runLiveDemoScenario(): Promise<LiveDemoResponse> {
  const response = await fetch(`${API_URL}/api/demo/scenarios/live/water-convergence`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("LIVE_GEMINI_DEMO_DISABLED");
    }

    let errorDetail = "Failed to run live demo scenario.";
    try {
      const errorData = await response.json();
      if (errorData.detail?.stage) {
        errorDetail = `Pipeline Error at stage: ${errorData.detail.stage}`;
      } else if (errorData.detail) {
        errorDetail = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
