# Evidence Contract

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Overview

The Evidence Contract defines the structure of all public evidence items used in intelligence calculations. Evidence is the factual foundation of every Civic Intelligence Report.

**Key principle:** Evidence items are **immutable** once stored. Corrections add new records, not overwrites.

---

## 2. JJM Evidence Contract (MVP Core)

The Jal Jeevan Mission provides the primary gap evidence for the Water sector MVP.

### 2.1 JJM Village Evidence Item

```python
class JJMVillageEvidence(BaseModel):
    """
    Village-level JJM Functional Household Tap Connection data.
    Source: JJM District/State Reports (CSV/PDF extract)
    """
    evidence_id:            str             # UUID (system-generated)

    # Source-native identifiers (preserved exactly as in source)
    source_state_name:      str             # as in JJM report
    source_district_name:   str             # as in JJM report
    source_block_name:      Optional[str]
    source_village_name:    str             # as in JJM report

    # Canonical LGD resolution
    lgd_state_code:         Optional[int]   # None if unresolved
    lgd_district_code:      Optional[int]   # None if unresolved
    lgd_block_code:         Optional[int]
    lgd_village_code:       Optional[int]
    resolution_status:      Literal["CONFIRMED", "PROBABLE", "UNRESOLVED"]
    resolution_confidence:  float = Field(ge=0.0, le=1.0)

    # Primary coverage fields (raw source values -- no calculated columns)
    total_households:       Optional[int]   = None  # As reported in JJM source
    fhtc_households:        Optional[int]   = None  # Functional Household Tap Connections (as reported)
    # NOTE: gap (total - fhtc) is calculated in GapAssessment, NOT stored in evidence

    # Quality and coverage context
    quality_affected_flag:  bool = False
    quality_issue_type:     Optional[Literal["ARSENIC", "FLUORIDE", "SALINITY", "IRON", "NITRATE"]] = None
    quality_affected_habitations: Optional[int] = None

    # Evidence quality
    evidence_quality:       EvidenceQuality

    # Provenance (all required)
    source:                 str = "JJM"
    source_report_ref:      Optional[str]   # e.g. "AP State Report Q3 2025"
    source_url:             Optional[str]   # JJM dashboard URL if applicable
    data_as_of:             date            # when JJM report was current
    ingested_at:            datetime
    snapshot_ref:           str             # GCS path to raw CSV file
    processing_version:     str             # e.g. "ingest.jjm.v1.0"

    # Missing data handling
    is_missing:             bool = False
    missing_reason:         Optional[str]   # if fields are None
    assumptions:            list[str] = []
```

**Validation rules:**
- Evidence table stores ONLY raw source values. No calculated fields.
- `data_as_of` MUST be a real date (not a fake date)
- `source_village_name` MUST be the exact name from the JJM source (no normalization)
- `snapshot_ref` MUST point to an existing GCS file
- `fhtc_households` MUST be <= `total_households` when both are present (validation, not storage)
- The gap `(total_households - fhtc_households)` is computed ONLY in `GapAssessment.gap_units`

### 2.2 JJM District Evidence Item

For cases where village-level data is unavailable:

```python
class JJMDistrictEvidence(BaseModel):
    evidence_id:            str
    source_district_name:   str
    lgd_district_code:      Optional[int]
    resolution_status:      Literal["CONFIRMED", "PROBABLE", "UNRESOLVED"]

    # Raw source values only -- no calculated gap columns
    total_households:       Optional[int]
    fhtc_households:        Optional[int]
    # NOTE: gap = total - fhtc belongs in GapAssessment, not here

    evidence_quality:       EvidenceQuality
    data_as_of:             date
    ingested_at:            datetime
    snapshot_ref:           str
    processing_version:     str

    # Note: district-level evidence is used as fallback only
    # when village-level is MISSING
    is_district_level_fallback: bool = True
```

---

## 3. Mission Antyodaya Evidence Contract (Supporting)

```python
class MissionAntyodayaEvidence(BaseModel):
    """
    GP-level infrastructure indicators from Mission Antyodaya 2022-23 survey.
    Used for development context, NOT for gap calculation.
    """
    evidence_id:            str

    # Source-native identifiers
    source_state_name:      str
    source_district_name:   str
    source_gp_name:         str
    source_gp_code:         Optional[str]

    # LGD resolution
    lgd_state_code:         Optional[int]
    lgd_district_code:      Optional[int]
    lgd_block_code:         Optional[int]
    lgd_gp_code:            Optional[int]
    resolution_status:      Literal["CONFIRMED", "PROBABLE", "UNRESOLVED"]

    # Key indicators (subset -- not all Mission Antyodaya fields)
    has_primary_health_centre: Optional[bool]
    has_secondary_school:   Optional[bool]
    has_paved_road_access:  Optional[bool]
    has_electricity:        Optional[bool]
    has_piped_water:        Optional[bool]
    total_population:       Optional[int]

    evidence_quality:       EvidenceQuality

    # Provenance
    source:                 str = "MISSION_ANTYODAYA"
    survey_year:            int = 2022             # Survey year (2022-23)
    data_as_of:             date                   # survey reference date
    ingested_at:            datetime
    snapshot_ref:           str
    processing_version:     str

    assumptions:            list[str] = [
        "Mission Antyodaya 2022-23 survey data; may not reflect current state",
        "Self-reported by Gram Panchayats; subject to reporting bias"
    ]
```

---

## 4. Census 2011 Evidence Contract (Contextual)

```python
class Census2011Evidence(BaseModel):
    """
    Village-level population baseline from Census 2011.
    ALWAYS labeled as historical context -- not current data.
    """
    evidence_id:            str

    source_state_name:      str
    source_district_name:   str
    source_village_name:    str
    census_location_code:   str             # Census 2011 native code

    lgd_village_code:       Optional[int]   # via LGD-Census mapping table
    lgd_district_code:      Optional[int]
    resolution_status:      Literal["CONFIRMED", "PROBABLE", "UNRESOLVED"]

    total_population:       Optional[int]
    total_households:       Optional[int]

    evidence_quality:       EvidenceQuality = EvidenceQuality.LOW_CONFIDENCE

    source:                 str = "CENSUS_2011"
    data_as_of:             date = date(2011, 3, 1)   # Census reference date
    ingested_at:            datetime
    snapshot_ref:           str
    processing_version:     str

    # MANDATORY assumptions -- always present
    assumptions:            list[str] = [
        "Data from Census 2011 -- approximately 15 years old",
        "Population figures are directional context only",
        "Actual current population likely differs significantly"
    ]
```

---

## 5. Evidence Conflict Contract

```python
class ConflictType(str, Enum):
    VALUE_MISMATCH    = "VALUE_MISMATCH"      # two sources give different numbers
    DATE_MISMATCH     = "DATE_MISMATCH"       # same field, different dates
    COVERAGE_MISMATCH = "COVERAGE_MISMATCH"   # one source shows coverage, other doesn't
    CITIZEN_DISPUTE   = "CITIZEN_DISPUTE"     # citizen signals contradict official data

class EvidenceConflict(BaseModel):
    """
    A detected conflict between two evidence sources.
    Both sources are preserved. No automatic resolution by LLM.
    """
    conflict_id:            str
    report_id:              Optional[str]   # if detected during report generation

    # Source A
    evidence_id_a:          str
    source_a:               str
    value_a:                Optional[str]   # the conflicting value
    data_as_of_a:           Optional[date]

    # Source B
    evidence_id_b:          str
    source_b:               str
    value_b:                Optional[str]
    data_as_of_b:           Optional[date]

    # Conflict details
    conflict_type:          ConflictType
    field_name:             str             # which field conflicts
    conflict_description:   str

    # Resolution (human-driven only)
    resolution_status:      Literal["OPEN", "REVIEWED", "DISMISSED", "REFERRED"] = "OPEN"
    resolution_note:        Optional[str]
    resolved_by:            Optional[str]   # user pseudonym
    resolved_at:            Optional[datetime]

    detected_at:            datetime

    # What this conflict means for the report
    impact_on_report:       str             # e.g. "Gap calculation uses more conservative value"
```

---

## 6. Evidence Ledger Entry Contract

```python
class LedgerStepType(str, Enum):
    SIGNAL_RECEIVED       = "SIGNAL_RECEIVED"
    NEED_EXTRACTED        = "NEED_EXTRACTED"
    GEOGRAPHY_RESOLVED    = "GEOGRAPHY_RESOLVED"
    EVIDENCE_QUERIED      = "EVIDENCE_QUERIED"
    GAP_CALCULATED        = "GAP_CALCULATED"
    PRIORITY_CALCULATED   = "PRIORITY_CALCULATED"
    CONFLICT_DETECTED     = "CONFLICT_DETECTED"
    REPORT_GENERATED      = "REPORT_GENERATED"

class EvidenceLedgerEntry(BaseModel):
    """
    An immutable audit record of one step in the intelligence pipeline.
    The full chain of entries for a report provides complete provenance.
    """
    ledger_id:              str
    report_id:              str

    step_type:              LedgerStepType
    step_order:             int             # 1, 2, 3, ...

    entity_id:              Optional[str]   # ID of entity produced at this step
    entity_type:            Optional[str]   # table name

    source:                 Optional[str]
    source_version:         Optional[str]
    data_as_of:             Optional[date]
    processing_version:     Optional[str]
    calculation_version:    Optional[str]

    assumptions:            list[str] = []
    data_quality:           Optional[EvidenceQuality]

    recorded_at:            datetime

    # Links back to superseded entries (for corrections)
    supersedes_ledger_id:   Optional[str] = None
```

---

## 7. Evidence API Responses

### GET /api/evidence/{evidence_id}

```python
class EvidenceDetailResponse(BaseModel):
    evidence_id:            str
    source:                 str
    field_name:             str
    value:                  Optional[str]   # always string for display
    evidence_quality:       EvidenceQuality
    data_as_of:             Optional[date]
    ingested_at:            datetime
    source_url:             Optional[str]
    assumptions:            list[str]
    conflicts:              list[EvidenceConflict]
```

---

*Architecture V1 -- 2026-09-24*
