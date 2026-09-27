# Gap Assessment and Priority Contract

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Gap Calculation Contract (Water / JJM)

### 1.1 Gap Logic

The gap calculation for the Water sector is deterministic and defined in code.

```python
def calculate_water_gap(
    total_households: Optional[int],
    fhtc_households: Optional[int],
    evidence_quality: EvidenceQuality
) -> WaterGapResult:
    """
    Calculates the water access gap from JJM data.
    DETERMINISTIC -- never involves LLM.
    """
    if total_households is None or fhtc_households is None:
        return WaterGapResult(
            gap_units=None,
            gap_percentage=None,
            evidence_quality=EvidenceQuality.MISSING,
            calculation_notes=["Insufficient JJM data for gap calculation"]
        )

    if fhtc_households > total_households:
        # Data integrity issue -- flag as conflict
        return WaterGapResult(
            gap_units=None,
            gap_percentage=None,
            evidence_quality=EvidenceQuality.CONFLICTING,
            calculation_notes=["FHTC exceeds total households -- data integrity issue"]
        )

    gap_units = total_households - fhtc_households
    gap_percentage = gap_units / total_households if total_households > 0 else 0.0

    return WaterGapResult(
        gap_units=gap_units,
        gap_percentage=round(gap_percentage, 4),
        evidence_quality=evidence_quality,
        calculation_notes=[]
    )
```

### 1.2 Gap Assessment Schema

```python
class WaterGapResult(BaseModel):
    gap_units:              Optional[int]   # unmet households
    gap_percentage:         Optional[float] # 0.0 to 1.0
    evidence_quality:       EvidenceQuality
    calculation_notes:      list[str] = []

class GapAssessmentRecord(BaseModel):
    gap_id:                 str             # UUID
    civic_need_id:          str

    lgd_district_code:      int
    lgd_block_code:         Optional[int]
    lgd_village_code:       Optional[int]

    sector:                 str = "WATER"
    gap_type:               str = "HOUSEHOLD_TAP_CONNECTION"

    # The gap
    total_units:            Optional[int]   # total households
    served_units:           Optional[int]   # FHTC households
    gap_units:              Optional[int]   # unmet households
    gap_percentage:         Optional[float] # 0.0 to 1.0

    evidence_quality:       EvidenceQuality
    primary_evidence_id:    Optional[str]   # FK to evidence_jjm_village/district
    is_district_level_fallback: bool = False

    # Provenance
    calculation_version:    str = "gap.water.v1.0"
    calculated_at:          datetime
    data_as_of:             Optional[date]
    assumptions:            list[str] = []
```

---

## 2. Priority Score Contract

### 2.1 Priority Formula v1.0.0

The priority score is a **deterministic weighted sum**. This formula is implemented in code. Gemini NEVER calculates it.

```python
# Priority Formula v1.0.0 Parameters
PRIORITY_SCHEMA_VERSION = "1.0.0"

WEIGHTS = {
    "gap":     0.40,   # infrastructure gap (biggest driver)
    "demand":  0.30,   # citizen demand signal strength
    "pop":     0.20,   # population impact
    "quality": 0.10,   # evidence quality bonus/penalty
}

# Evidence quality multiplier
QUALITY_MULTIPLIERS = {
    EvidenceQuality.AVAILABLE:      1.00,
    EvidenceQuality.LOW_CONFIDENCE: 0.80,
    EvidenceQuality.PARTIAL:        0.60,
    EvidenceQuality.CONFLICTING:    0.50,  # conservative under conflict
    EvidenceQuality.MISSING:        0.20,  # penalize heavily for missing evidence
}

# Priority tier thresholds
TIER_THRESHOLDS = {
    "CRITICAL": 0.75,
    "HIGH":     0.50,
    "MEDIUM":   0.25,
    "LOW":      0.00,
}
```

### 2.2 Normalization Functions

```python
def normalize_demand(signal_count: int, max_reference: int = 1000) -> float:
    """
    Normalize signal count to 0.0-1.0.
    Reference max is configurable (default: 1000 signals = max score).
    """
    return min(signal_count / max_reference, 1.0)

def normalize_population_impact(
    gap_units: Optional[int],
    population: Optional[int],
    household_size: float = 4.5  # India average household size
) -> float:
    """
    Normalize population impact to 0.0-1.0.
    Uses gap_units * household_size as estimated individuals affected.
    Reference max: 500,000 individuals.
    """
    if gap_units is None:
        return 0.0
    estimated_individuals = gap_units * household_size
    return min(estimated_individuals / 500_000, 1.0)

def calculate_priority_score(
    gap_percentage: Optional[float],
    demand_signal_count: int,
    population: Optional[int],
    gap_units: Optional[int],
    evidence_quality: EvidenceQuality,
    weights: dict = WEIGHTS
) -> tuple[float, PriorityTier, dict]:
    """
    Calculates the priority score and returns the score, tier, and factor breakdown.
    All calculations are deterministic.
    """
    factor_gap_value     = gap_percentage if gap_percentage is not None else 0.0
    factor_demand_value  = normalize_demand(demand_signal_count)
    factor_pop_value     = normalize_population_impact(gap_units, population)
    factor_quality_value = QUALITY_MULTIPLIERS[evidence_quality]

    score = (
        weights["gap"]     * factor_gap_value +
        weights["demand"]  * factor_demand_value +
        weights["pop"]     * factor_pop_value +
        weights["quality"] * factor_quality_value
    )
    score = round(min(score, 1.0), 4)

    if score >= TIER_THRESHOLDS["CRITICAL"]:
        tier = PriorityTier.CRITICAL
    elif score >= TIER_THRESHOLDS["HIGH"]:
        tier = PriorityTier.HIGH
    elif score >= TIER_THRESHOLDS["MEDIUM"]:
        tier = PriorityTier.MEDIUM
    else:
        tier = PriorityTier.LOW

    factor_breakdown = {
        "gap":     {"weight": weights["gap"],     "value": factor_gap_value,     "contribution": weights["gap"] * factor_gap_value},
        "demand":  {"weight": weights["demand"],  "value": factor_demand_value,  "contribution": weights["demand"] * factor_demand_value},
        "pop":     {"weight": weights["pop"],     "value": factor_pop_value,     "contribution": weights["pop"] * factor_pop_value},
        "quality": {"weight": weights["quality"], "value": factor_quality_value, "contribution": weights["quality"] * factor_quality_value},
    }

    return score, tier, factor_breakdown
```

### 2.3 Priority Assessment Schema

```python
class PriorityAssessmentRecord(BaseModel):
    priority_id:            str             # UUID
    gap_id:                 str

    priority_score:         float = Field(ge=0.0, le=1.0)
    priority_tier:          PriorityTier

    # Factor breakdown (all stored explicitly)
    factor_gap_weight:      float
    factor_gap_value:       float
    factor_gap_contribution: float

    factor_demand_weight:   float
    factor_demand_value:    float
    factor_demand_contribution: float

    factor_pop_weight:      float
    factor_pop_value:       float
    factor_pop_contribution: float

    factor_quality_weight:  float
    factor_quality_value:   float
    factor_quality_contribution: float

    # Raw inputs
    demand_signal_count:    int             # organic signals only
    synthetic_demand_count: int
    population_context:     Optional[int]   # Census 2011 if available

    # Provenance
    priority_schema_version: str = "1.0.0"
    calculated_at:          datetime

    # What data was NOT used (transparency)
    factors_excluded:       list[str] = []  # e.g. ["urgency_score", "accessibility"]
    exclusion_reason:       Optional[str]   # "Not available in MVP data sources"
```

---

## 3. Gap and Priority API Contracts

### GET /api/hotspots

Request:
```
GET /api/hotspots
  ?district_code=527   (optional -- filter by district LGD code)
  &sector=WATER        (optional)
  &tier=CRITICAL       (optional)
  &limit=20            (default: 20, max: 100)
  &include_synthetic=false (default: false)
Authorization: Bearer {firebase_id_token}
```

Response:
```python
class HotspotSummary(BaseModel):
    lgd_district_code:      int
    district_name_en:       str
    state_name_en:          str
    sector:                 str
    civic_need_type:        str

    priority_score:         float
    priority_tier:          PriorityTier

    gap_percentage:         Optional[float]
    gap_units:              Optional[int]
    demand_signal_count:    int
    synthetic_signal_count: int

    evidence_quality:       EvidenceQuality
    conflicts_present:      bool

    report_id:              Optional[str]   # latest report for this hotspot
    data_as_of:             Optional[date]

    # Map coordinate (from Geocoding or hardcoded fallback)
    latitude:               Optional[float]
    longitude:              Optional[float]

class HotspotListResponse(BaseModel):
    hotspots:               list[HotspotSummary]
    total_count:            int
    filters_applied:        dict
    generated_at:           datetime
    has_synthetic_signals:  bool
```

### GET /api/reports/{report_id}

Response: `IntelligenceReport` (see canonical-data-contract.md)

---

## 4. Weight Configuration Contract (Admin -- Future MVP)

```python
class PriorityWeightConfig(BaseModel):
    """
    Admin-configurable priority weights.
    Sum of all weights must equal 1.0.
    Changes create a new priority_schema_version.
    """
    config_id:              str
    weight_gap:             float = Field(ge=0.0, le=1.0)
    weight_demand:          float = Field(ge=0.0, le=1.0)
    weight_pop:             float = Field(ge=0.0, le=1.0)
    weight_quality:         float = Field(ge=0.0, le=1.0)

    resulting_version:      str             # new priority_schema_version
    created_by:             str             # admin user pseudonym
    created_at:             datetime
    rationale:              str             # why weights were changed

    @validator("weight_quality")
    def weights_must_sum_to_one(cls, v, values):
        total = values.get("weight_gap", 0) + values.get("weight_demand", 0) + values.get("weight_pop", 0) + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v
```

---

*Architecture V1 -- 2026-09-24*
