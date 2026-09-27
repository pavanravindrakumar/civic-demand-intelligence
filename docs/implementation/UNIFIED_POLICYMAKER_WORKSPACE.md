# Unified Policymaker Decision Workspace

## 1. Information Architecture
The dashboard serves as a unified civic-planning intelligence product, abandoning fragmented components in favor of a coherent decision-support workspace.

The hierarchy is strictly maintained:
1. **Header / Product Identity:** Sets context ("Civic Demand Intelligence").
2. **Executive Analytics Summary:** Top-level metrics across the dataset (e.g. statewide).
3. **Geographic Intelligence (Hotspot Map):** Visualizes the gap.
4. **Selected-Location Decision Workspace:** Integrates `VillageLookup` and `PriorityDecisionPanel`.
5. **Copilot:** Right-hand semantic query assistant.
6. **Demo / Synthetic Mode:** Bounded testing/demo environment placed securely aside in the sidebar.

## 2. Shared "Selected Village" State
To eliminate competing selection states, the dashboard uses a lightweight React Context (`VillageContext.tsx`).
- **State Definition:** Maintains `selectedLgdCode` and `selectedVillageContext` (metadata cache).
- **Producers:** `HotspotMapClient` (on click) and `VillageLookup` (on explicit search).
- **Consumers:** `WorkspaceSelection` (which mounts the `PriorityDecisionPanel`) and `CopilotChat`.
- **Performance:** Context prevents duplicate API calls by lifting the LGD Code selection above the heavy visualizations.

## 3. Map → Decision Flow
When a polygon is clicked on the Leaflet map:
1. `setSelectedLgdCode` and `setSelectedVillageContext` trigger.
2. The map's internal "Selected Detail Panel" updates instantly with the cached geospatial metadata.
3. The `WorkspaceSelection` component at the root observes `selectedLgdCode` and renders the `PriorityDecisionPanel` below the map.
4. The `PriorityDecisionPanel` independently executes the read-only fetch to the `/api/priority/assessments` endpoint.

## 4. Priority → Evidence Flow
The `PriorityDecisionPanel` answers the critical question: *"Why did this village surface?"*
- **Explicit factors:** Displays Infrastructure Gap, Validated Citizen Demand, and Exposure Proxy directly from the frozen backend calculation.
- **Evidence Ledger:** Exposed via an "Inspect Evidence" drill-down embedded *within* the decision panel to prevent losing the geographic context.

## 5. Copilot Context
The Copilot remains the grounded natural-language interface.
- It consumes `VillageContext` to dynamically construct UI prompts (e.g., "What is the status for village X?").
- **API Boundary:** The underlying `POST /api/copilot/chat` contract remains unchanged; context injection happens purely as user-initiated text formulation.

## 6. Demo Separation & Provenance
The `DemoPanel` exists entirely within the unified grid but is constrained.
- It relies on strict UI badging (`SYNTHETIC DEMO SIGNAL` vs `REAL / OFFICIAL JJM/LGD`).
- Triggers the synthetic `/api/demo/scenarios/run` backend.
- Automatically selects the target LGD Code (`275084`) and scrolls to the workspace for evaluation without corrupting the natural data layer.
- Empty states (where priority = null) accurately report "No combined priority score available" rather than defaulting to `0`.

## 7. Zero-Mutation Principle
The frontend remains exclusively a read-only projection of the intelligence pipeline.
- No React-side Priority Engine overrides.
- No live Gemini inferences inside the browser.
- No new BigQuery aggregations.
- No PII or underlying thought-reasoning leakage.
