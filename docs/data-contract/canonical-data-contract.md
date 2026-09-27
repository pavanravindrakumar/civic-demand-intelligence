# Canonical Data Contract

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

This document defines the canonical data model -- the shared language between all system components. All source adapters must map to this model. All consumers must use these types.

---

## 1. Core Type Definitions

### 1.1 Geographic Identity

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date, datetime

class CanonicalGeography(BaseModel):
    """
    The canonical administrative geographic entity resolved from a source.
    LGD codes are the universal keys.
    """
    lgd_state_code:        int
    lgd_district_code:     int
    lgd_block_code:        Optional[int]     = None
    lgd_gp_code:           Optional[int]     = None
    lgd_village_code:      Optional[int]     = None

    # Human-readable names (canonical -- from LGD table)
    state_name_en:         str
    district_name_en:      str
    block_name_en:         Optional[str]     = None
    village_name_en:       Optional[str]     = None

    resolution_status:     Literal[
        "CONFIRMED",    # high confidence match
        "PROBABLE",     # medium confidence -- flagged for review
        "UNRESOLVED",   # could not resolve to LGD
    ]
    resolution_confidence: float = Field(ge=0.0, le=1.0)

    # Source-native identifiers preserved
    source_location_expression: str          # what the citizen said
    source_native_id:      Optional[str]     = None  # any ID from source system

    # Provenance
    resolved_at:           datetime
    resolution_version:    str               # e.g. "geo.resolver.v1.0"
```

### 1.2 Civic Need

```python
class CivicNeed(BaseModel):
    """
    The normalized, canonical representation of a civic development need.
    One need may be linked to multiple signals.
    """
    need_id:               str               # UUID

    canonical_need_type:   Literal[
        "WATER_SUPPLY_DEFICIT",
        "WATER_QUALITY_ISSUE",
        "ROAD_CONNECTIVITY_DEFICIT",
        "SANITATION_DEFICIT",
        "ELECTRICITY_ACCESS_DEFICIT",
        "HEALTH_FACILITY_DEFICIT",
        "EDUCATION_FACILITY_DEFICIT",
        "OTHER_DEVELOPMENT_NEED",
    ]
    sector:                Literal["WATER", "ROADS", "SANITATION", "ELECTRICITY", "HEALTH", "EDUCATION", "OTHER"]

    need_label_en:         str               # e.g. "Drinking Water Access"
    need_description:      Optional[str]     = None

    is_composite:          bool = False      # True if multiple sub-needs
    related_need_ids:      list[str] = []    # linked need IDs

    # Provenance
    first_seen_at:         datetime
    last_updated_at:       datetime
    processing_version:    str               # e.g. "extraction.v1.0"
```

### 1.3 Evidence Item

```python
class EvidenceQuality(str, Enum):
    AVAILABLE      = "AVAILABLE"
    PARTIAL        = "PARTIAL"
    MISSING        = "MISSING"
    CONFLICTING    = "CONFLICTING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"

class EvidenceItem(BaseModel):
    """
    A single piece of public evidence from an authoritative source.
    Evidence items are immutable once stored.
    """
    evidence_id:           str               # UUID

    # Geography (LGD canonical)
    lgd_district_code:     int
    lgd_village_code:      Optional[int]     = None

    source:                str               # e.g. "JJM", "MISSION_ANTYODAYA", "CENSUS_2011"
    source_native_id:      Optional[str]     = None
    source_url:            Optional[str]     = None

    # Data fields (source-specific)
    indicator_name:        str               # e.g. "FHTC_HOUSEHOLDS"
    indicator_value:       Optional[float]   = None
    indicator_unit:        Optional[str]     = None  # e.g. "households", "km"

    evidence_quality:      EvidenceQuality

    # Provenance
    data_as_of:            date              # when the source data was current
    ingested_at:           datetime
    snapshot_ref:          Optional[str]     = None  # GCS path to raw source
    processing_version:    str

    # Missing data handling
    is_missing:            bool = False
    missing_reason:        Optional[str]     = None  # e.g. "No village-level data available"
    assumptions:           list[str] = []
```

### 1.4 Gap Assessment

```python
class GapAssessment(BaseModel):
    """
    The calculated infrastructure gap for a civic need at a geography.
    All values are deterministic -- never LLM-generated.
    """
    gap_id:                str               # UUID
    civic_need_id:         str

    lgd_district_code:     int
    lgd_village_code:      Optional[int]     = None
    lgd_block_code:        Optional[int]     = None

    sector:                str
    gap_type:              str               # e.g. "HOUSEHOLD_TAP_CONNECTION"

    total_units:           Optional[int]     = None    # e.g. total households
    served_units:          Optional[int]     = None    # e.g. households with FHTC
    gap_units:             Optional[int]     = None    # total - served
    gap_percentage:        Optional[float]   = None    # gap / total

    evidence_quality:      EvidenceQuality
    primary_evidence_id:   Optional[str]     = None

    # Provenance
    calculation_version:   str               # e.g. "gap.water.v1.0"
    calculated_at:         datetime
    data_as_of:            Optional[date]    = None
    assumptions:           list[str] = []
```

### 1.5 Priority Assessment

```python
class PriorityTier(str, Enum):
    CRITICAL = "CRITICAL"   # score >= 0.75
    HIGH     = "HIGH"       # score >= 0.50
    MEDIUM   = "MEDIUM"     # score >= 0.25
    LOW      = "LOW"        # score < 0.25

class PriorityAssessment(BaseModel):
    """
    The deterministic priority score for a gap assessment.
    All factor weights and values are explicitly stored.
    """
    priority_id:           str               # UUID
    gap_id:                str

    priority_score:        float = Field(ge=0.0, le=1.0)
    priority_tier:         PriorityTier

    # Factor breakdown (stored for full transparency)
    factor_gap_weight:     float
    factor_gap_value:      float             # normalized gap_percentage
    factor_demand_weight:  float
    factor_demand_value:   float             # normalized demand count
    factor_pop_weight:     float
    factor_pop_value:      float             # normalized population impact
    factor_quality_weight: float
    factor_quality_value:  float             # evidence quality multiplier

    # Raw inputs to factors
    demand_signal_count:   int               # organic signals only
    synthetic_demand_count: int
    population_context:    Optional[int]     = None  # Census 2011 (historical)

    # Provenance
    priority_schema_version: str             # e.g. "1.0.0"
    calculated_at:         datetime
```

### 1.6 Intelligence Report

```python
class DataQualityNote(BaseModel):
    field:                 str
    quality:               EvidenceQuality
    note:                  Optional[str]     = None

class IntelligenceReport(BaseModel):
    """
    The assembled Civic Intelligence Report.
    This is the primary user-facing analytical object.
    """
    report_id:             str               # UUID
    report_version:        int = 1
    report_schema_version: str               # e.g. "1.0.0"

    # Core entities
    civic_need:            CivicNeed
    geography:             CanonicalGeography
    gap_assessment:        GapAssessment
    priority_assessment:   PriorityAssessment

    # Demand context
    demand_signal_count:   int               # organic
    synthetic_signal_count: int
    demand_trend_pct:      Optional[float]   = None  # month-over-month change

    # Population context
    population_context:    Optional[int]     = None  # Census 2011 -- labeled historical
    population_data_note:  str = "Population from Census 2011 -- historical context only"

    # Evidence
    evidence_items:        list[EvidenceItem]
    evidence_conflicts:    list[dict] = []   # references to evidence_conflicts table
    data_quality_notes:    list[DataQualityNote] = []

    # AI narrative (labeled)
    gemini_narrative:      Optional[str]     = None
    narrative_grounded_on: list[str] = []    # list of evidence IDs used

    # Provenance
    generated_at:          datetime
    is_published:          bool = False
    conflicts_present:     bool = False
    synthetic_signals_present: bool = False

    # Assumptions
    assumptions:           list[str] = []
```

---

## 2. Versioning Rules

| Field | Format | Notes |
|-------|--------|-------|
| `processing_version` | `"extraction.v{major}.{minor}"` | Tracks Gemini extraction logic |
| `calculation_version` | `"gap.{sector}.v{major}.{minor}"` | Tracks gap formula |
| `priority_schema_version` | `"{major}.{minor}.{patch}"` | Tracks priority formula |
| `report_schema_version` | `"{major}.{minor}.{patch}"` | Tracks report structure |
| `resolution_version` | `"geo.resolver.v{major}.{minor}"` | Tracks geography resolver |

When any version changes, existing records are preserved. New records carry the new version. Historical analysis can always query by version.

---

## 3. Missing Data Rules

| Situation | Representation | Forbidden |
|-----------|---------------|---------|
| No official evidence found | `is_missing = True`, `evidence_quality = MISSING` | Do NOT return 0 |
| Only district data (no village) | `lgd_village_code = null`, `evidence_quality = PARTIAL` | Do NOT interpolate village values |
| Evidence older than 2 years | `evidence_quality = LOW_CONFIDENCE` | Do NOT present as current |
| Two sources disagree | `evidence_quality = CONFLICTING` | Do NOT silently average |
| LGD code cannot be resolved | `resolution_status = UNRESOLVED` | Do NOT infer geography |

---

## 4. Synthetic Data Rules

All synthetic data MUST:
1. Set `is_synthetic = TRUE` at creation
2. Never have `is_synthetic` changed to `FALSE`
3. Be aggregated separately (`synthetic_demand_count`)
4. Be labeled in every UI view
5. Never appear in official evidence tables (only in signal tables)

---

## 5. Provenance Requirements

Every `EvidenceItem` MUST carry:
- `source` -- system identifier
- `data_as_of` -- when the source data was accurate
- `ingested_at` -- when it entered our system
- `processing_version` -- which code version processed it
- `snapshot_ref` -- path to the original raw file in GCS

Every `GapAssessment` MUST carry:
- `calculation_version` -- exact formula version used
- `calculated_at` -- when the calculation ran
- `assumptions` -- list of any assumptions made

Every `PriorityAssessment` MUST carry:
- `priority_schema_version` -- formula version
- All factor weights and values individually stored

---

*Architecture V1 -- 2026-09-24*
