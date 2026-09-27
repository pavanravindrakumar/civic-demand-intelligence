from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict

class ReadinessState(str, Enum):
    READY = "READY"
    INCOMPLETE_DEMAND = "INCOMPLETE_DEMAND"
    PUBLIC_EVIDENCE_ONLY = "PUBLIC_EVIDENCE_ONLY"
    INVALID_INPUTS = "INVALID_INPUTS"

class EvidenceQuality(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    PARTIAL = "PARTIAL"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"

class PriorityWeights(BaseModel):
    version: str = "1.0.0-final"
    infrastructure_gap: float = 0.5
    validated_demand: float = 0.3
    household_exposure: float = 0.2
    # The weights must sum to 1.0 (or close to it)

class VillageInput(BaseModel):
    lgd_village_code: str
    households: int
    fhtc_house_connections: int
    reported_household_gap: int
    validated_citizen_demand_count: Optional[int] = None
    data_valid: bool = True

class PriorityResult(BaseModel):
    lgd_village_code: str
    readiness: ReadinessState
    evidence_quality: EvidenceQuality
    calculation_version: str

    # Normalized factors [0.0, 1.0]
    normalized_gap: float
    normalized_exposure: float
    normalized_demand: float

    # Absolute metrics
    reported_household_gap: int
    household_exposure: int

    # Final Score
    priority_score: Optional[float] = None

class CivicAnalyticsEngine:
    CALCULATION_VERSION = "v1.0"

    def __init__(self, weights: PriorityWeights):
        self.weights = weights

    def assess_village(self, data: VillageInput) -> PriorityResult:
        # Base validation
        if not data.data_valid or data.households < 0 or data.fhtc_house_connections < 0 or data.reported_household_gap < 0:
            return self._invalid_result(data.lgd_village_code)

        if data.fhtc_house_connections > data.households:
            return self._invalid_result(data.lgd_village_code)

        if data.reported_household_gap != (data.households - data.fhtc_house_connections):
            return self._invalid_result(data.lgd_village_code)

        # 1. Deterministic Gap Assessment
        # Gap normalized to percentage of households without connections
        normalized_gap = data.reported_household_gap / data.households if data.households > 0 else 0.0
        # Bound normalization
        normalized_gap = max(0.0, min(1.0, normalized_gap))

        # 2. Exposure Normalization
        # Simple capping saturation mechanism (e.g. any village over 1000 households has max exposure weight)
        MAX_HOUSEHOLDS_CAP = 1000.0
        normalized_exposure = data.households / MAX_HOUSEHOLDS_CAP
        normalized_exposure = max(0.0, min(1.0, normalized_exposure))

        # 3. Demand Normalization
        has_demand = data.validated_citizen_demand_count is not None
        normalized_demand = 0.0
        if has_demand:
            # Saturation capping for demand to prevent manipulation (e.g. 50 distinct validated requests hits cap)
            MAX_DEMAND_CAP = 50.0
            demand_val = float(data.validated_citizen_demand_count)
            normalized_demand = demand_val / MAX_DEMAND_CAP
            normalized_demand = max(0.0, min(1.0, normalized_demand))

        # 4. State & Score Calculation
        if not has_demand:
            state = ReadinessState.PUBLIC_EVIDENCE_ONLY
            evidence_quality = EvidenceQuality.PARTIAL
            # No final score calculated without demand, keeping it strictly deterministic
            final_score = None
        else:
            state = ReadinessState.READY
            evidence_quality = EvidenceQuality.HIGH_CONFIDENCE
            final_score = (
                (normalized_gap * self.weights.infrastructure_gap) +
                (normalized_exposure * self.weights.household_exposure) +
                (normalized_demand * self.weights.validated_demand)
            )
            # Ensure output is bounded
            final_score = max(0.0, min(1.0, final_score))

        return PriorityResult(
            lgd_village_code=data.lgd_village_code,
            readiness=state,
            evidence_quality=evidence_quality,
            calculation_version=self.CALCULATION_VERSION,
            normalized_gap=normalized_gap,
            normalized_exposure=normalized_exposure,
            normalized_demand=normalized_demand,
            reported_household_gap=data.reported_household_gap,
            household_exposure=data.households,
            priority_score=final_score
        )

    def _invalid_result(self, lgd_code: str) -> PriorityResult:
        return PriorityResult(
            lgd_village_code=lgd_code,
            readiness=ReadinessState.INVALID_INPUTS,
            evidence_quality=EvidenceQuality.MISSING,
            calculation_version=self.CALCULATION_VERSION,
            normalized_gap=0.0,
            normalized_exposure=0.0,
            normalized_demand=0.0,
            reported_household_gap=0,
            household_exposure=0,
            priority_score=None
        )
