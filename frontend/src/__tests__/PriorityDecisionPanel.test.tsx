import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import PriorityDecisionPanel from '../components/PriorityDecisionPanel';
import * as api from '../lib/api';

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual('../lib/api');
  return {
    ...actual as any,
    getPriorityAssessments: vi.fn(),
    getEvidenceLedgerByPriorityAssessmentId: vi.fn()
  };
});

describe('PriorityDecisionPanel', () => {
  const mockAssessment = {
    priority_assessment_id: "a1",
    opportunity_id: "o1",
    lgd_village_code: "111111",
    canonical_need_type: "WATER_SUPPLY_DEFICIT",
    sector: "WATER",
    priority_score: 0.85,
    priority_version: "1.0.0-final",
    calculation_version: "v1.0",
    eligibility_status: "CONVERGENCE_IDENTIFIED",
    factors: {
      infrastructure_gap: { normalized_input: 0.5, configured_weight: 0.5, contribution: 0.25 },
      validated_demand: { normalized_input: 1.0, configured_weight: 0.3, contribution: 0.3 },
      household_exposure: { normalized_input: 0.2, configured_weight: 0.2, contribution: 0.04 }
    },
    citizen_evidence_provenance: "SYNTHETIC_DEMO_SIGNAL",
    public_evidence_provenance: "REAL_JJM_LGD",
    evaluated_at: new Date().toISOString()
  };

  const mockLedgerEntry = {
    ledger_entry_id: "l1",
    priority_assessment_id: "a1",
    convergence_opportunity_id: "o1",
    unmet_demand_assessment_id: "u1",
    lgd_village_code: "111111",
    canonical_need_type: "WATER_SUPPLY_DEFICIT",
    sector: "WATER",
    priority_score: 0.85,
    factor_inputs_normalized: { normalized_gap: 0.5 },
    factor_contributions: { gap_contribution: 0.25 },
    priority_version: "1.0.0-final",
    calculation_version: "v1.0",
    reported_household_gap: 50,
    household_exposure: 100,
    signal_count: 25,
    distinct_submitter_count: 20,
    generated_at: new Date().toISOString(),
    record_hash: "abcd1234hash"
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders priority score and version exactly as returned', async () => {
    vi.mocked(api.getPriorityAssessments).mockResolvedValue([mockAssessment]);

    render(<PriorityDecisionPanel lgdVillageCode="111111" />);

    expect(await screen.findByText('0.850')).toBeInTheDocument();
    expect(screen.getByText('1.0.0-final')).toBeInTheDocument();

    // Check factor rendering
    expect(screen.getByText('Infrastructure Gap')).toBeInTheDocument();
    expect(screen.getByText('Validated Citizen Demand')).toBeInTheDocument();
    expect(screen.getByText('Exposure Proxy')).toBeInTheDocument();
  });

  it('handles no-score state properly', async () => {
    const noScoreAssessment = {
      ...mockAssessment,
      priority_score: null,
      eligibility_status: "PUBLIC_EVIDENCE_ONLY",
      factors: {}
    };
    vi.mocked(api.getPriorityAssessments).mockResolvedValue([noScoreAssessment]);

    render(<PriorityDecisionPanel lgdVillageCode="222222" />);

    expect(await screen.findByText('No combined priority score available')).toBeInTheDocument();
    expect(screen.getByText('Status: PUBLIC_EVIDENCE_ONLY')).toBeInTheDocument();

    // Ensure 0 is not displayed for priority score
    const scores = screen.queryAllByText('0');
    expect(scores.length).toBe(0);
  });

  it('displays synthetic and real provenance explicitly', async () => {
    vi.mocked(api.getPriorityAssessments).mockResolvedValue([mockAssessment]);

    render(<PriorityDecisionPanel lgdVillageCode="111111" />);

    expect(await screen.findByText('SYNTHETIC DEMO CITIZEN EVIDENCE')).toBeInTheDocument();
    expect(screen.getByText('REAL / OFFICIAL PUBLIC EVIDENCE')).toBeInTheDocument();
  });

  it('fetches and displays evidence ledger without PII', async () => {
    vi.mocked(api.getPriorityAssessments).mockResolvedValue([mockAssessment]);
    vi.mocked(api.getEvidenceLedgerByPriorityAssessmentId).mockResolvedValue([mockLedgerEntry]);

    render(<PriorityDecisionPanel lgdVillageCode="111111" />);

    const btn = await screen.findByText('View Evidence Ledger');
    fireEvent.click(btn);

    expect(await screen.findByText(/abcd1234hash/)).toBeInTheDocument();
    expect(screen.getByText('reported_household_gap:')).toBeInTheDocument();

    // Check no PII leaks by confirming absence of raw text/pseudonyms in the mock and rendering
    const rawText = screen.queryByText('raw');
    expect(rawText).not.toBeInTheDocument();
  });

  it('preserves strict terminology', async () => {
    vi.mocked(api.getPriorityAssessments).mockResolvedValue([mockAssessment]);
    vi.mocked(api.getEvidenceLedgerByPriorityAssessmentId).mockResolvedValue([mockLedgerEntry]);

    render(<PriorityDecisionPanel lgdVillageCode="111111" />);

    await screen.findByText('Exposure Proxy');

    // Population/Beneficiaries should NOT be present in our UI labels (apart from strict data keys if they existed, but we don't render those labels)
    expect(screen.queryByText('Population')).not.toBeInTheDocument();
    expect(screen.queryByText('Citizens')).not.toBeInTheDocument();
    expect(screen.queryByText('Beneficiaries')).not.toBeInTheDocument();
  });

  it('displays error if API fails', async () => {
    vi.mocked(api.getPriorityAssessments).mockRejectedValue(new Error('API failed'));

    render(<PriorityDecisionPanel lgdVillageCode="999999" />);

    expect(await screen.findByText('API failed')).toBeInTheDocument();
  });
});
