# Copilot Tool Contract & Safety Architecture

## Phase 7.1A Constraints
- **Gemini is NOT connected yet.** This document enforces the deterministic safety boundary before any LLM integration.
- **Citizen Demand is NOT implemented yet.** The Copilot must operate in the `PUBLIC_EVIDENCE_ONLY` mode. It MUST NOT fabricate or simulate citizen demand.

## Tool Registry
The backend enforces a strict allowlist of tools through `backend/app/copilot/tools.py`. The LLM is restricted to calling only these tools.

### Approved Tools (MVP)
1. `get_analytics_summary`
   - **Purpose**: Retrieve global summary metrics (total villages, gap, readiness).
   - **Input**: None
   - **Output**: `AnalyticsSummary`

2. `get_village_analytics`
   - **Purpose**: Retrieve deterministic analytics for a specific village.
   - **Input**: `lgd_village_code` (Strictly validated as 6 digits).
   - **Output**: `PriorityResult`

3. `get_analytics_readiness`
   - **Purpose**: Retrieve the current overall readiness state (e.g. why demand is missing).
   - **Input**: None
   - **Output**: `ReadinessOutput`

## Safety Classification
**ALL tools in the MVP are classified as `READ_ONLY`.**
There is no mechanism for the LLM to execute arbitrary SQL, mutate databases, or perform HTTP requests. Any future write-capable tool will require a separate authorization boundary and explicit user consent.

## Tool Execution Contract
1. LLM suggests a tool call.
2. Backend validates tool exists in `CopilotToolRegistry`.
3. Backend strictly parses and validates input using Pydantic (rejects arbitrary/SQL input).
4. Backend executes deterministic Python function.
5. Backend wraps output in `CopilotResultWrapper` ensuring provenance (`source_dataset`, `calculation_version`) is attached.
6. LLM formulates response based *only* on the executed tool's deterministic output.

## Provenance
Every successful tool execution is explicitly annotated with `provenance_source: "JJM/LGD Analytics Dataset"`. The LLM is instructed to reference this provenance when explaining numbers.

## Error Contract
Errors are categorized predictably:
- `INVALID_ARGUMENT`: Input failed regex or type validation.
- `TOOL_NOT_ALLOWED`: Tool not in registry or not read-only.
- `NOT_FOUND`: Data requested does not exist (e.g. unknown LGD code).
- `DATA_UNAVAILABLE`: Dataset incomplete.
- `INCOMPLETE_INPUTS`: Priority calculation missing inputs (like citizen demand).
- `INTERNAL_ERROR`: Execution failed without leaking stack traces.

## Model Behavior Rules
When Gemini is finally connected (Phase 7.1B+), the prompt must enforce:
1. Use tools for ALL authoritative data. Do not invent numbers.
2. Do not state a numeric result as authoritative if a tool was not called.
3. Explicitly distinguish between *measured public evidence* and *citizen demand*.
4. Acknowledge when citizen demand is explicitly missing (i.e. readiness is `PUBLIC_EVIDENCE_ONLY`).
5. **DO NOT fabricate population values.**
6. **DO NOT treat `household_exposure` as a population headcount.**
7. **DO NOT call `reported_household_gap` an absolute water shortage.** It is specifically a tap-connection infrastructure gap.

## Phase 7.1B.3: Gemini Declaration Adapter
- **Explicit Declarations**: Gemini sees explicit `types.FunctionDeclaration` objects representing our approved tools.
- **Derived from Registry**: These declarations are automatically derived from the authoritative `CopilotToolRegistry` and its Pydantic input schemas.
- **Not a Security Boundary**: The Gemini function declarations are merely a model-facing hint. They are NOT the security boundary.
- **Authoritative Executor**: The backend `CopilotExecutor` remains strictly authoritative for all runtime validation, authorization, and execution.
- **Deferred Invocation**: Actual Gemini client invocation, generation loops, and automatic function execution are intentionally deferred to the next phase.

## Phase 7.1B.4: Local Copilot Orchestrator
- **Manual Multi-Turn Orchestration**: The application explicitly controls the `model response -> function call -> function execution -> function response -> model` loop.
- **Application-Owned Execution**: The `CopilotOrchestrator` mandates that every tool call strictly routes through the deterministic `CopilotExecutor`. There is no automatic SDK function execution.
- **Bounded Tool Rounds**: The loop is statically capped by a configurable maximum tool rounds limit to mathematically prevent infinite execution loops.
- **Mocked Testing Strategy**: Validated entirely offline using a `MockModelAdapter` simulating both successful flows and error conditions.
- **Deferred Cloud Integration**: Actual live Gemini API invocation remains deferred to the next phase.

## Phase 7.1B.4C: SDK Adapter & Configuration
- **Google Cloud Backed**: Uses `genai.Client(vertexai=True)` relying exclusively on Application Default Credentials. API keys are strictly forbidden.
- **Configuration Design**: `GEMINI_MODEL`, `google_cloud_project`, and `google_cloud_location` are configurable to allow environment-specific testing.
- **Manual Function Calling**: SDK configuration explicitly disables automatic SDK execution, relying instead on our deterministic orchestration loop.
- **Deferred Live Testing**: Actual network smoke tests with `generate_content` are deferred to Phase 7.1C.

## Phase 7.1C.1B: Live Function-Call Smoke Test
- **Execution**: Attempted one live `generate_content` request exposing only `get_analytics_summary`.
- **Result**: FAILED with a `403 PERMISSION_DENIED` error because the Vertex AI API (Agent Platform API) is not enabled on the target project (`civic-intelligence-hackathon`).
## Phase 7.1C.2A: Gemini Developer API Provider Configuration
- **Provider Abstraction**: Provider selection is entirely configuration-driven (`provider_mode`), supporting both Vertex AI (`vertex_ai`) and Gemini Developer API (`developer_api`).
- **Development**: Targets the Gemini Developer API (`developer_api`) with an API key, using `gemini-3.8-flash`. Billing is not required for the current Developer API Free Tier path where Google permits free-tier usage (though free-tier quotas still apply). No billing configuration is being added in this phase.
- **Future/Production**: Targets Google Cloud Vertex AI (`vertex_ai`) using Application Default Credentials (ADC) and a specifically configured model (e.g. `gemini-3.1-pro-preview`).
- **Unchanged Boundary**: Regardless of the provider mode, the application preserves the exact same tool definitions, schemas, and `CopilotExecutor` deterministic boundary.

## Phase 7.1C.2C: Fix Gemini Function Schema Serialization
- **Declaration Adapter Fix**: The Gemini function declaration adapter uses the SDK's JSON Schema path (`parameters_json_schema`) so the Pydantic-generated schema can be represented correctly without weakening validation constraints (e.g., properly preserving `additionalProperties` which the Developer API expects inside the JSON schema representation, not the typed `parameters` representation).

## Phase 7.1C.2E: Switch Development Gemini Model to Flash-Lite
- **Development**: The development model was explicitly changed to `gemini-3.1-flash-lite` after receiving a temporary `503 UNAVAILABLE` (high-demand) response from `gemini-3.8-flash`. This error was upstream and did not indicate a code/schema failure. The `developer_api` provider, model configurability, and Free Tier path remain intact.
- **Future/Production**: The `vertex_ai` provider path remains completely intact and configured to `gemini-3.1-pro-preview` using ADC when billing and explicit configuration are activated.

## Phase 7.1C.3B: Reusable Gemini Copilot Service
- **Service Layer**: The verified manual loop is encapsulated within `GeminiCopilotService` (acting as the application-level entry point) and `GeminiModelAdapter`.
- **Raw Content Preservation**: The adapter natively retains the raw SDK `Content` object for the model turn, ensuring elements such as `thought_signature` are faithfully transmitted to the API in subsequent requests.
- **Execution Integrity**: The orchestration loops tightly restrict tool execution strictly through `CopilotExecutor`.
- **Offline Testing**: The service is exhaustively verified through mocked dependency injection, guaranteeing zero unsolicited live API requests during unit testing.

## Phase 7.2A: Copilot HTTP API Boundary
- **Endpoint**: A single narrow read-only boundary at `POST /api/copilot/chat`.
- **Pydantic Contracts**: Strongly-typed `CopilotChatRequest` and `CopilotChatResponse`.
- **No Orchestration Leakage**: The HTTP route does not duplicate orchestration logic; it merely delegates to `GeminiCopilotService` and reformats the exact returned history into safe, client-facing metadata (like tool names and deterministic provenance).
- **Security**: The API explicitly hides internal model thoughts/thought signatures, internal stack traces, SDK credential payloads, and prevents infinite loops (handled downstream by the service bounds). It does not introduce arbitrary execution.
# #   P h a s e   7 . 1 C . 3 B :   R e u s a b l e   G e m i n i   C o p i l o t   S e r v i c e 
 
 -   * * S e r v i c e   L a y e r * * :   T h e   v e r i f i e d   m a n u a l   l o o p   i s   e n c a p s u l a t e d   w i t h i n   G e m i n i C o p i l o t S e r v i c e   ( a c t i n g   a s   t h e   a p p l i c a t i o n - l e v e l   e n t r y   p o i n t )   a n d   G e m i n i M o d e l A d a p t e r . 
 
 -   * * R a w   C o n t e n t   P r e s e r v a t i o n * * :   T h e   a d a p t e r   n a t i v e l y   r e t a i n s   t h e   r a w   S D K   \ C o n t e n t \   o b j e c t   f o r   t h e   m o d e l   t u r n ,   e n s u r i n g   e l e m e n t s   s u c h   a s   \ 	 h o u g h t _ s i g n a t u r e \   a r e   f a i t h f u l l y   t r a n s m i t t e d   t o   t h e   A P I   i n   s u b s e q u e n t   r e q u e s t s . 
 
 -   * * E x e c u t i o n   I n t e g r i t y * * :   T h e   o r c h e s t r a t i o n   l o o p s   t i g h t l y   r e s t r i c t   t o o l   e x e c u t i o n   s t r i c t l y   t h r o u g h   C o p i l o t E x e c u t o r . 
 
 -   * * O f f l i n e   T e s t i n g * * :   T h e   s e r v i c e   i s   e x h a u s t i v e l y   v e r i f i e d   t h r o u g h   m o c k e d   d e p e n d e n c y   i n j e c t i o n ,   g u a r a n t e e i n g   z e r o   u n s o l i c i t e d   l i v e   A P I   r e q u e s t s   d u r i n g   u n i t   t e s t i n g . 
 
 
