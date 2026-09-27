# Copilot Tool Contract

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Overview

The AI Copilot uses Gemini function calling to answer policymaker questions about intelligence reports.

**Security model:**
- All tools are READ-ONLY
- Tool names validated against an allowlist before any execution
- All arguments validated by Pydantic schemas
- No freeform SQL accepted
- No write operations from any tool
- All tool calls logged with user pseudonym

---

## 2. Copilot Request/Response Contract

### POST /api/copilot

```python
class CopilotRequest(BaseModel):
    message:            str = Field(min_length=5, max_length=500)
    session_id:         str             # user session UUID (not linked to identity)
    report_context_id:  Optional[str]  # FK to intelligence_reports -- grounds the response
    conversation_history: list[dict] = []  # last N turns (max 10)

class CopilotResponse(BaseModel):
    response_id:        str             # UUID
    narrative:          str             # Gemini-generated grounded explanation
    sources_used:       list[str]       # evidence IDs or report IDs referenced
    tools_called:       list[str]       # tool names that were executed
    confidence:         Literal["HIGH", "MEDIUM", "LOW"]
    is_ai_generated:    bool = True     # always True -- labeled in UI
    generated_at:       datetime
    warning:            Optional[str]   # e.g. "Based on limited evidence"

class CopilotError(BaseModel):
    error_code:         str
    message:            str

# Error codes:
# "MESSAGE_TOO_SHORT" | "MESSAGE_TOO_LONG" | "RATE_LIMIT_EXCEEDED"
# "AI_UNAVAILABLE" | "TOOL_EXECUTION_FAILED" | "CONTEXT_NOT_FOUND"
```

---

## 3. Copilot Tool Declarations

### Tool 1: get_hotspot_details

```python
class GetHotspotDetailsInput(BaseModel):
    lgd_district_code:  int = Field(description="LGD numeric district code")
    sector:             Optional[str] = Field(default="WATER", description="Sector: WATER, ROADS, etc.")
    include_synthetic:  bool = Field(default=False, description="Include synthetic signals in demand count")

class GetHotspotDetailsOutput(BaseModel):
    lgd_district_code:  int
    district_name_en:   str
    state_name_en:      str
    sector:             str
    priority_score:     float
    priority_tier:      str
    gap_percentage:     Optional[float]
    gap_units:          Optional[int]
    demand_signal_count: int
    evidence_quality:   str
    data_as_of:         Optional[str]   # ISO date string
    conflicts_present:  bool

    # Tool metadata (always returned)
    tool_name:          str = "get_hotspot_details"
    executed_at:        str             # ISO datetime
    data_source:        str = "BigQuery -- civic_intelligence dataset"

TOOL_DECLARATION_get_hotspot_details = {
    "name": "get_hotspot_details",
    "description": "Returns demand and gap summary for a specific district. Use this to answer questions about why a district is prioritized or how bad the gap is.",
    "parameters": {
        "type": "object",
        "properties": {
            "lgd_district_code": {"type": "integer", "description": "LGD numeric district code"},
            "sector": {"type": "string", "enum": ["WATER", "ROADS", "SANITATION"], "description": "Development sector"},
            "include_synthetic": {"type": "boolean", "description": "Whether to include synthetic signals"}
        },
        "required": ["lgd_district_code"]
    }
}
```

### Tool 2: get_intelligence_report

```python
class GetIntelligenceReportInput(BaseModel):
    report_id:          str = Field(description="UUID of the Intelligence Report")

class GetIntelligenceReportOutput(BaseModel):
    report_id:          str
    district_name_en:   str
    civic_need_type:    str
    priority_score:     float
    priority_tier:      str
    gap_percentage:     Optional[float]
    demand_signal_count: int
    evidence_quality:   str
    conflicts_present:  bool
    generated_at:       str

    tool_name:          str = "get_intelligence_report"
    executed_at:        str

TOOL_DECLARATION_get_intelligence_report = {
    "name": "get_intelligence_report",
    "description": "Returns the full Intelligence Report for a specific report ID. Use this when the policymaker asks about a specific report.",
    "parameters": {
        "type": "object",
        "properties": {
            "report_id": {"type": "string", "description": "UUID of the Intelligence Report"}
        },
        "required": ["report_id"]
    }
}
```

### Tool 3: explain_priority_score

```python
class ExplainPriorityScoreInput(BaseModel):
    priority_id:        str = Field(description="UUID of the priority assessment")

class ExplainPriorityScoreOutput(BaseModel):
    priority_id:        str
    priority_score:     float
    priority_tier:      str
    priority_schema_version: str

    # Full factor breakdown
    factors: list[dict]   # [{name, weight, value, contribution, description}]

    # What was NOT included and why
    excluded_factors: list[dict]  # [{name, reason}]

    tool_name:          str = "explain_priority_score"
    executed_at:        str

TOOL_DECLARATION_explain_priority_score = {
    "name": "explain_priority_score",
    "description": "Returns the detailed breakdown of how a priority score was calculated, including all factor weights and values. Use this to explain why a district received its priority score.",
    "parameters": {
        "type": "object",
        "properties": {
            "priority_id": {"type": "string", "description": "UUID of the priority assessment"}
        },
        "required": ["priority_id"]
    }
}
```

### Tool 4: get_jjm_scheme_status

> **Replaces:** `list_overlapping_interventions` (removed — no intervention dataset in MVP)

```python
class GetJJMSchemeStatusInput(BaseModel):
    lgd_district_code:  int = Field(description="LGD district code")
    lgd_village_code:   Optional[int] = Field(default=None, description="Optional: narrow to village")

class GetJJMSchemeStatusOutput(BaseModel):
    lgd_district_code:  int
    district_name_en:   str
    total_households:   Optional[int]       # as reported in JJM snapshot
    fhtc_households:    Optional[int]       # as reported in JJM snapshot
    data_as_of:         Optional[str]       # ISO date of JJM snapshot used
    resolution_status:  str                 # CONFIRMED / PROBABLE / UNRESOLVED
    data_status:        str                 # AVAILABLE / PARTIAL / MISSING
    # If MISSING: real NO_DATA sentinel returned; Gemini explains the absence

    tool_name:          str = "get_jjm_scheme_status"
    executed_at:        str

TOOL_DECLARATION_get_jjm_scheme_status = {
    "name": "get_jjm_scheme_status",
    "description": "Returns JJM (Jal Jeevan Mission) scheme coverage data for a district from the preloaded evidence snapshot. Use to answer questions about tap connection coverage or scheme status.",
    "parameters": {
        "type": "object",
        "properties": {
            "lgd_district_code": {"type": "integer", "description": "LGD district code"},
            "lgd_village_code": {"type": "integer", "description": "Optional LGD village code"}
        },
        "required": ["lgd_district_code"]
    }
}
```

### Tool 5: show_evidence_conflict

```python
class ShowEvidenceConflictInput(BaseModel):
    conflict_id:        str = Field(description="UUID of the evidence conflict")

class ShowEvidenceConflictOutput(BaseModel):
    conflict_id:        str
    conflict_type:      str
    field_name:         str

    source_a:           str
    value_a:            Optional[str]
    data_as_of_a:       Optional[str]

    source_b:           str
    value_b:            Optional[str]
    data_as_of_b:       Optional[str]

    resolution_status:  str
    impact_on_report:   str

    tool_name:          str = "show_evidence_conflict"
    executed_at:        str

TOOL_DECLARATION_show_evidence_conflict = {
    "name": "show_evidence_conflict",
    "description": "Returns details of a specific evidence conflict, showing both sources side by side. Use this when a policymaker asks about a conflict or discrepancy in the data.",
    "parameters": {
        "type": "object",
        "properties": {
            "conflict_id": {"type": "string", "description": "UUID of the evidence conflict"}
        },
        "required": ["conflict_id"]
    }
}
```

### Tool 6: compare_policy_weights

```python
class ComparePolicyWeightsInput(BaseModel):
    lgd_district_code:  int
    weight_scenarios:   list[dict] = Field(
        description="List of weight scenarios to compare. Max 3.",
        max_items=3
    )
    # Each scenario: {"gap": 0.5, "demand": 0.3, "pop": 0.1, "quality": 0.1}

class ComparePolicyWeightsOutput(BaseModel):
    lgd_district_code:  int
    district_name_en:   str
    scenarios:          list[dict]  # [{scenario_name, weights, priority_score, tier}]
    current_score:      float
    current_tier:       str

    tool_name:          str = "compare_policy_weights"
    executed_at:        str

TOOL_DECLARATION_compare_policy_weights = {
    "name": "compare_policy_weights",
    "description": "Compares how a district's priority score would change under different weight configurations. Use this when a policymaker asks 'what if we weighted demand more?' or similar policy exploration questions.",
    "parameters": {
        "type": "object",
        "properties": {
            "lgd_district_code": {"type": "integer"},
            "weight_scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scenario_name": {"type": "string"},
                        "weight_gap": {"type": "number"},
                        "weight_demand": {"type": "number"},
                        "weight_pop": {"type": "number"},
                        "weight_quality": {"type": "number"}
                    }
                },
                "maxItems": 3
            }
        },
        "required": ["lgd_district_code", "weight_scenarios"]
    }
}
```

---

## 4. Tool Execution Security Model

```python
COPILOT_TOOL_ALLOWLIST = {
    "get_hotspot_details",
    "get_intelligence_report",
    "explain_priority_score",
    "get_jjm_scheme_status",       # replaces removed list_overlapping_interventions
    "show_evidence_conflict",
    "compare_policy_weights",
}
# REMOVED: "list_overlapping_interventions" -- no intervention dataset in MVP

TOOL_REGISTRY = {
    "get_hotspot_details":          get_hotspot_details_fn,
    "get_intelligence_report":      get_intelligence_report_fn,
    "explain_priority_score":       explain_priority_score_fn,
    "get_jjm_scheme_status":        get_jjm_scheme_status_fn,
    "show_evidence_conflict":       show_evidence_conflict_fn,
    "compare_policy_weights":       compare_policy_weights_fn,
}

INPUT_SCHEMAS = {
    "get_hotspot_details":          GetHotspotDetailsInput,
    "get_intelligence_report":      GetIntelligenceReportInput,
    "explain_priority_score":       ExplainPriorityScoreInput,
    "get_jjm_scheme_status":        GetJJMSchemeStatusInput,
    "show_evidence_conflict":       ShowEvidenceConflictInput,
    "compare_policy_weights":       ComparePolicyWeightsInput,
}

async def validate_and_execute_tool(
    tool_call: FunctionCall,
    user_pseudonym: str
) -> dict:
    # 1. Allowlist check
    if tool_call.name not in COPILOT_TOOL_ALLOWLIST:
        raise SecurityError(f"Tool not in allowlist: {tool_call.name}")

    # 2. Input validation
    input_schema = INPUT_SCHEMAS[tool_call.name]
    try:
        validated_args = input_schema(**tool_call.args)
    except ValidationError as e:
        raise ValidationError(f"Invalid tool arguments: {e}")

    # 3. Execute (read-only BQ query)
    tool_fn = TOOL_REGISTRY[tool_call.name]
    result = await tool_fn(validated_args)

    # 4. Log execution
    await log_tool_execution(
        tool_name=tool_call.name,
        user_pseudonym=user_pseudonym,
        args_hash=hash(str(tool_call.args)),  # no raw args in log
        executed_at=datetime.utcnow()
    )

    return result.model_dump()
```

---

## 5. Copilot System Prompt Contract

```
You are a Policy Intelligence Analyst for the Civic Demand Intelligence Platform.

Your role is to help policymakers understand development intelligence reports by:
1. Answering questions grounded in official evidence from the report
2. Explaining priority scores and their factors
3. Highlighting data quality issues and conflicts

STRICT RULES:
1. ONLY use information provided in the report context or returned by tools
2. NEVER invent infrastructure statistics, population figures, or coverage percentages
3. NEVER reference information not in the provided context
4. If you are unsure, say "I don't have sufficient data to answer this"
5. Always cite which evidence you are drawing from
6. When tools return MISSING data, say "This data is not currently available in the system"
7. Do not speculate about future policy outcomes

When calling tools:
- Call tools ONLY to retrieve factual data needed to answer the question
- Do not call the same tool twice with the same parameters
- Maximum 3 tool calls per response

Your response should be:
- Factual and evidence-grounded
- Clear to a non-technical policymaker
- Transparent about data limitations
- 100-300 words maximum
```

---

## 6. Rate Limiting

```
Copilot endpoint:
  20 queries per user per hour
  100 queries per user per day
  5 tool calls per conversation turn

Response on limit exceeded:
  HTTP 429
  error_code: "RATE_LIMIT_EXCEEDED"
  message: "Query limit reached. Please try again later."
```

---

*Architecture V1 -- 2026-09-24*
