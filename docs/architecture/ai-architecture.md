# AI Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Governing Principle

> **AI interprets. Deterministic code calculates.**

Gemini is used for tasks that require natural language understanding, semantic classification, and grounded narrative generation. It is NEVER used to produce authoritative numbers, query databases, or resolve geographies without backend validation.

---

## 2. Gemini Model Selection

The Gemini model is **configurable via the `GEMINI_MODEL` environment variable**. No model name is hardcoded in application code.

Current validated candidate: `gemini-3.8-flash`

| Use Case | Env Var | Reason |
|----------|---------|--------|
| Civic need extraction (text) | `GEMINI_MODEL` | Flash tier: structured output, cost-effective, low latency |
| Civic need extraction (audio) | `GEMINI_MODEL` | Native multimodal; no separate STT pipeline (primary path) |
| Policymaker Copilot | `GEMINI_MODEL` | Function calling; grounded explanation |
| Multilingual support | `GEMINI_MODEL` | Strong multilingual understanding (Hindi, Telugu, Tamil, etc.) |

> **Note:** Confirm that the configured `GEMINI_MODEL` supports multimodal audio AND `response_schema` structured output in the same API call. Verify on Day 1 of the sprint.

---

## 3. Gemini Tasks and Contracts

### 3.1 Task 1: Civic Need Extraction

**Input:** Raw citizen signal (text or audio file reference + language hint)

**Output:** Structured `CivicNeedExtraction` JSON (Pydantic-validated)

**What Gemini MUST do:**
- Identify the underlying development need (not just the surface complaint)
- Extract location expression (as string -- backend resolves to LGD)
- Classify need category from an allowlist
- Detect language
- Assign urgency signal (HIGH / MEDIUM / LOW) based on tone and content
- Flag if the signal contains multiple distinct needs

**What Gemini MUST NOT do:**
- Resolve location string to LGD code
- Calculate gap figures
- Reference specific government statistics
- Invent census or JJM data
- Write to any database
- Execute any tools during extraction

**System prompt excerpt:**
```
You are a civic intelligence analyst. Your job is to understand a citizen's development request and extract the structured civic need it represents.

RULES:
1. Extract only what the citizen actually expressed. Do not invent context.
2. The location field must be the citizen's own words -- do not resolve it to an official code.
3. Do not produce any numerical infrastructure statistics.
4. Classify the need_type using ONLY the provided allowlist.
5. Return ONLY valid JSON matching the provided schema.
6. If you cannot determine a field, return null -- do not guess.
```

**Pydantic schema (CivicNeedExtraction):**
```python
class CivicNeedExtraction(BaseModel):
    need_type: Literal[
        "WATER_SUPPLY_DEFICIT",
        "WATER_QUALITY_ISSUE",
        "ROAD_CONNECTIVITY_DEFICIT",
        "SANITATION_DEFICIT",
        "ELECTRICITY_ACCESS_DEFICIT",
        "HEALTH_FACILITY_DEFICIT",
        "EDUCATION_FACILITY_DEFICIT",
        "OTHER_DEVELOPMENT_NEED"
    ]
    need_description: str          # 1-3 sentence description in English
    location_expression: str       # citizen's own location words
    location_confidence: float     # 0.0-1.0
    urgency: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    detected_language: str         # BCP-47 code
    is_multi_need: bool
    secondary_need_types: list[str] | None
    extraction_notes: str | None   # reasoning for edge cases
```

**API call pattern:**
```python
GEMINI_MODEL = os.environ["GEMINI_MODEL"]  # e.g. "gemini-3.8-flash"

response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=[signal_text_or_audio_part],
    config=types.GenerateContentConfig(
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=CivicNeedExtraction,
        temperature=0.1,            # low temperature for consistent extraction
    )
)
extraction = CivicNeedExtraction.model_validate_json(response.text)
```

**Fallback:** If Pydantic validation fails, retry once. On second failure, attempt GCP STT fallback (see Section 3.2). If all paths fail, store signal as `extraction_status = FAILED`.

---

### 3.2 Task 2: Voice / Audio Understanding

**Primary path:** Pass audio directly to Gemini multimodal.

**Audio handling (primary):**
1. Citizen uploads audio (max 5MB, WAV/MP3/OGG, max 60 seconds)
2. Backend stores audio in Cloud Storage (civic-audio bucket, TTL=24h)
3. GCS URI passed to Gemini as `Part.from_uri(gcs_uri, mime_type="audio/wav")`
4. Gemini extracts `CivicNeedExtraction` directly from audio in one call
5. Pydantic validates output

**Fallback path: Google Cloud Speech-to-Text**

Triggered when Gemini audio extraction fails validation twice:

1. Pass audio to GCP STT synchronous API
   - `language_code`: detected or hinted BCP-47 code (e.g. `te-IN`, `hi-IN`, `en-IN`)
   - `model`: `"latest_long"`
2. STT returns transcript string
3. Transcript passed to Gemini as TEXT input (standard extraction path)
4. Same `CivicNeedExtraction` Pydantic schema applies — **interface is path-agnostic**

**Key constraint:** The `CivicNeedExtraction` output schema is identical for both paths. Only the backend routing changes. The extraction contract does not change.

**Supported languages (pilot):**
| Language | BCP-47 | Gemini Audio | GCP STT |
|----------|--------|-------------|--------|
| Telugu | `te-IN` | Verify Day 1 | Supported |
| Hindi | `hi-IN` | Supported | Supported |
| English | `en-IN` | Supported | Supported |

**Final fallback:** If both Gemini and STT fail, the UI displays: "Could not process audio. Please type your request instead." Signal stored as `extraction_status = FAILED`.

---

### 3.3 Task 3: Policymaker Copilot (Grounded Explanation)

The Copilot uses Gemini function calling to answer policymaker questions about intelligence reports.

**Architecture:**
```
Policymaker question
  -> Backend validates question (length, injection check)
  -> Gemini receives question + allowed tool list + report context
  -> Gemini proposes tool call (e.g. get_hotspot_details)
  -> Backend VALIDATES tool call (allowlist check + authorization)
  -> Backend EXECUTES tool (read-only BigQuery query)
  -> Result returned to Gemini
  -> Gemini generates grounded narrative explanation
  -> Backend validates response (no injected statistics)
  -> Dashboard displays with [AI EXPLANATION] label
```

**Allowed tools (all read-only):**

| Tool | Description |
|------|-------------|
| `get_hotspot_details` | Returns aggregated demand and gap for a district |
| `get_intelligence_report` | Returns a full report by ID |
| `explain_priority_score` | Returns factor breakdown for a priority score |
| `get_jjm_scheme_status` | Returns JJM scheme coverage status for a geography from snapshot |
| `show_evidence_conflict` | Returns details of a detected conflict |
| `compare_policy_weights` | Returns priority scores under alternative weight configurations |

> **Removed:** `list_overlapping_interventions` — no intervention dataset available in MVP. Tool has been permanently removed.

**Security rules for Copilot:**
- Tool names validated against an allowlist before execution
- No tool accepts freeform SQL
- All tool inputs are typed and length-limited
- Gemini session context cleared between policymaker sessions
- Rate limiting: 20 Copilot queries per user per hour

---

## 4. Multilingual Support Strategy

| Language | Input Channel | Gemini Capability | Notes |
|----------|--------------|-------------------|-------|
| Hindi | Text + Voice | Strong | Major Indian language; well supported |
| Telugu | Text + Voice | Good | AP pilot language; verify audio quality |
| Tamil | Text + Voice | Good | South India; well supported |
| Kannada | Text + Voice | Moderate | Verify |
| Marathi | Text + Voice | Good | Verify |
| Bengali | Text + Voice | Good | Verify |
| English | Text + Voice | Excellent | Primary interface language |
| Mixed/Code-switch | Text | Moderate | Gemini handles; may need fallback |

**Approach:** No pre-translation step. Gemini extracts directly from native language input. The `detected_language` field is used for UI personalization, not for routing.

---

## 5. Hallucination Prevention

| Risk | Prevention |
|------|-----------|
| Gemini invents JJM statistics | Gemini NEVER receives JJM data as input for extraction; only citizen text |
| Gemini fabricates LGD codes | Location extracted as string; LGD resolution is deterministic backend code |
| Gemini creates priority score | Priority calculation is deterministic code; Gemini only explains it after calculation |
| Copilot invents intervention data | All Copilot answers grounded via tool calls; tool results are real BQ data |
| Copilot hallucinates report details | Report context passed as structured JSON; Gemini instructed to reference only provided data |

**Prompt injection defense:**
- Citizen input is sanitized (HTML stripped, max length enforced) before concatenation into any prompt
- System prompt and user content are strictly separated using API message roles (not string concatenation)
- Gemini's structured output schema prevents freeform responses during extraction

---

## 6. Gemini API Configuration

```python
GEMINI_MODEL = os.environ["GEMINI_MODEL"]  # e.g. "gemini-3.8-flash"

EXTRACTION_CONFIG = {
    "model": GEMINI_MODEL,
    "temperature": 0.1,
    "top_p": 0.95,
    "max_output_tokens": 1024,
    "response_mime_type": "application/json",
}

COPILOT_CONFIG = {
    "model": GEMINI_MODEL,
    "temperature": 0.3,
    "top_p": 0.95,
    "max_output_tokens": 2048,
    "tools": COPILOT_TOOL_DECLARATIONS,  # typed function declarations
}
```

---

## 7. Gemini Failure Modes and Fallbacks

| Failure | Detection | Fallback |
|---------|-----------|---------|
| Pydantic validation fails | Exception in `model_validate_json()` | Retry once; then store as `FAILED` |
| Gemini returns non-JSON | JSON parse error | Retry with stricter prompt; then fail gracefully |
| Schema mismatch | Validation error | Log schema version mismatch; alert |
| API quota exceeded | HTTP 429 | Queue signal for delayed processing; show "processing" state |
| API unavailable | HTTP 5xx | Store signal; batch retry; UI shows "AI unavailable -- data saved" |
| Audio too large | Pre-check size | Reject with user message before API call |
| Audio language unrecognized | Gemini returns UNKNOWN language | Prompt user to re-submit with language hint |

---

## 8. AI Copilot Security Controls

See also [security-architecture.md](security-architecture.md).

```python
COPILOT_TOOL_ALLOWLIST = {
    "get_hotspot_details",
    "get_intelligence_report",
    "explain_priority_score",
    "get_jjm_scheme_status",      # replaces removed list_overlapping_interventions
    "show_evidence_conflict",
    "compare_policy_weights",
}
# REMOVED: "list_overlapping_interventions" -- no intervention dataset in MVP

def validate_and_execute_tool(tool_call: FunctionCall) -> dict:
    if tool_call.name not in COPILOT_TOOL_ALLOWLIST:
        raise SecurityError(f"Tool not in allowlist: {tool_call.name}")
    tool_fn = TOOL_REGISTRY[tool_call.name]
    validated_args = tool_fn.input_schema(**tool_call.args)  # Pydantic validation
    result = tool_fn.execute(validated_args)  # read-only BigQuery query
    # If no data found, return NO_DATA sentinel -- never fabricate
    return result if result else {"data_status": "NO_DATA", "message": "No data available for this query."}
```

---

## 9. Context Window Management

The configured `GEMINI_MODEL` (Flash tier) has a large context window. For the MVP:

- Extraction calls: ~500 tokens system + ~2000 tokens citizen input = well within limits
- Copilot calls: ~2000 tokens system + report JSON + conversation history = ~10,000 tokens max
- No retrieval-augmented generation needed in MVP (all evidence fetched via tools)
- Conversation history for Copilot limited to last 10 turns

---

## 10. AI Feature Roadmap (Post-MVP)

| Feature | Priority | Complexity |
|---------|----------|-----------|
| Semantic need clustering (similar needs grouping) | High | Medium |
| Cross-sector convergence detection | High | High |
| Trend analysis with Gemini narrative | Medium | Medium |
| Voice response (TTS) for accessibility | Medium | Low |
| Predictive demand forecasting | Low | High |
| Automatic intervention-gap matching | Low | High |

---

*Architecture V1 -- 2026-09-24*
