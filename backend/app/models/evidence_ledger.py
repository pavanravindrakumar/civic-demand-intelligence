from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
import hashlib
import json

from backend.app.models.civic_need import NeedType, SectorType

class EvidenceLedgerEntry(BaseModel):
    """
    Append-only audit record for a Priority Assessment, capturing all upstream provenance
    without PII or hidden model internals.
    """
    ledger_entry_id: str

    # Upstream References
    priority_assessment_id: str
    convergence_opportunity_id: str
    unmet_demand_assessment_id: str
    lgd_village_code: str

    # Semantic Context
    canonical_need_type: NeedType
    sector: SectorType

    # Exact Priority Engine Results
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    factor_inputs_normalized: Dict[str, float]
    factor_contributions: Dict[str, float]

    # Versioning
    priority_version: str
    calculation_version: str

    # Evidence Temporal Vintage
    public_evidence_vintage: Optional[datetime] = None
    demand_aggregation_window_start: Optional[datetime] = None
    demand_aggregation_window_end: Optional[datetime] = None

    # Measurement References
    reported_household_gap: Optional[int] = None
    household_exposure: Optional[int] = None
    signal_count: Optional[int] = None
    distinct_submitter_count: Optional[int] = None

    # Metadata
    generated_at: datetime
    record_hash: str

    def calculate_hash(self) -> str:
        """
        Produces a deterministic SHA-256 hash of the canonical serialized ledger entry.
        """
        # Create a dictionary of fields that contribute to the hash, explicitly excluding generated_at and record_hash
        # and ledger_entry_id to allow deterministic recreation from the core facts.
        hash_dict = {
            "priority_assessment_id": self.priority_assessment_id,
            "convergence_opportunity_id": self.convergence_opportunity_id,
            "unmet_demand_assessment_id": self.unmet_demand_assessment_id,
            "lgd_village_code": self.lgd_village_code,
            "canonical_need_type": self.canonical_need_type,
            "priority_score": self.priority_score,
            "factor_inputs_normalized": self.factor_inputs_normalized,
            "factor_contributions": self.factor_contributions,
            "priority_version": self.priority_version,
            "calculation_version": self.calculation_version,
            "reported_household_gap": self.reported_household_gap,
            "household_exposure": self.household_exposure,
            "signal_count": self.signal_count,
            "distinct_submitter_count": self.distinct_submitter_count
        }

        # Serialize deterministically (sorted keys, no spaces)
        serialized = json.dumps(hash_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
