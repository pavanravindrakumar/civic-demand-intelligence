import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.app.models.priority_assessment import PriorityAssessment
from backend.app.models.convergence_opportunity import ConvergenceOpportunity
from backend.app.models.evidence_ledger import EvidenceLedgerEntry
from backend.app.data.evidence_ledger_repository import EvidenceLedgerRepository

class EvidenceLedgerService:
    """
    Records derived Priority Assessments into the append-only Evidence Ledger.
    Does NOT recalculate scores or normalize factors.
    """

    def __init__(self, ledger_repo: EvidenceLedgerRepository):
        self.ledger_repo = ledger_repo

    def record_assessment(
        self,
        assessment: PriorityAssessment,
        opportunity: ConvergenceOpportunity
    ) -> EvidenceLedgerEntry:
        """
        Constructs and records an Evidence Ledger Entry for a Priority Assessment.
        """
        now = datetime.now(timezone.utc)

        # We must link the assessments
        if assessment.opportunity_id != opportunity.opportunity_id:
            raise ValueError("Mismatched PriorityAssessment and ConvergenceOpportunity")

        # Construct the entry
        entry = EvidenceLedgerEntry(
            ledger_entry_id=str(uuid.uuid4()),
            priority_assessment_id=assessment.assessment_id,
            convergence_opportunity_id=opportunity.opportunity_id,
            unmet_demand_assessment_id=opportunity.assessment_id,
            lgd_village_code=assessment.lgd_village_code,
            canonical_need_type=assessment.canonical_need_type,
            sector=assessment.sector,
            priority_score=assessment.priority_score,
            factor_inputs_normalized=assessment.factor_inputs_normalized,
            factor_contributions=assessment.factor_contributions,
            priority_version=assessment.priority_version,
            calculation_version=opportunity.calculation_version,
            public_evidence_vintage=opportunity.public_evidence_vintage,
            demand_aggregation_window_start=opportunity.demand_aggregation_window_start,
            demand_aggregation_window_end=opportunity.demand_aggregation_window_end,
            reported_household_gap=opportunity.reported_household_gap,
            household_exposure=opportunity.household_exposure,
            signal_count=opportunity.signal_count,
            distinct_submitter_count=opportunity.distinct_submitter_count,
            generated_at=now,
            record_hash="" # Placeholder to calculate it
        )

        # Calculate deterministic hash
        entry.record_hash = entry.calculate_hash()

        # Append idempotently
        self.ledger_repo.append_entry(entry)

        return entry
