export interface FactorExplanation {
  normalized_input: number;
  configured_weight: number;
  contribution: number;
}

export interface PriorityAssessmentResponse {
  priority_assessment_id: string;
  opportunity_id: string;
  lgd_village_code: string;
  canonical_need_type: string;
  sector: string;
  priority_score: number | null;
  priority_version: string;
  calculation_version: string;
  eligibility_status: string;
  factors: Record<string, FactorExplanation>;
  citizen_evidence_provenance: string;
  public_evidence_provenance: string;
  evaluated_at: string;
}

export interface EvidenceLedgerEntry {
  ledger_entry_id: string;
  priority_assessment_id: string;
  convergence_opportunity_id: string;
  unmet_demand_assessment_id: string;
  lgd_village_code: string;
  canonical_need_type: string;
  sector: string;
  priority_score: number | null;
  factor_inputs_normalized: Record<string, number>;
  factor_contributions: Record<string, number>;
  priority_version: string;
  calculation_version: string;
  public_evidence_vintage?: string | null;
  demand_aggregation_window_start?: string | null;
  demand_aggregation_window_end?: string | null;
  reported_household_gap?: number | null;
  household_exposure?: number | null;
  signal_count?: number | null;
  distinct_submitter_count?: number | null;
  generated_at: string;
  record_hash: string;
}
