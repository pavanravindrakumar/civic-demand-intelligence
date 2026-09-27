# Deployment Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Deployment Strategy

**Single monorepo, two deployable Cloud Run services.**

No microservices. No message queues. No Kubernetes. The MVP is stateless where possible and relies on managed Google Cloud services for everything persistent.

Deploy early (Day 1-2) to catch CORS, auth, and connectivity issues before they block development.

---

## 2. Architecture Diagram

```mermaid
graph TB
    subgraph "User Devices"
        CB[Citizen Browser\nMobile / Web]
        PB[Policymaker Browser\nDesktop]
    end

    subgraph "Google Cloud -- asia-south1"
        subgraph "Cloud Run"
            FE[civic-frontend\nNext.js\nPort 3000]
            BE[civic-backend\nFastAPI\nPort 8080]
        end

        subgraph "Data"
            BQ[(BigQuery\ncivic_intelligence dataset)]
            GCS[(Cloud Storage\ncivic-raw-data bucket\ncivic-audio bucket)]
        end

        subgraph "Managed Services"
            SM[Secret Manager]
            FA[Firebase Auth\n+ Hosting optional]
            MAPS[Google Maps Platform]
        end
    end

    subgraph "External APIs"
        GEMINI[Gemini API\n(GEMINI_MODEL env var)]
        STT[Google Cloud STT\nFallback only]
    end

    CB --> FE
    PB --> FE
    FE --> BE
    BE --> BQ
    BE --> GCS
    BE --> GEMINI
    BE --> SM
    FE --> FA
    FE --> MAPS
    FA --> BE
```

---

## 3. Service Definitions

### 3.1 civic-backend (FastAPI)

| Property | Value |
|----------|-------|
| Runtime | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Container | `Dockerfile.backend` |
| CPU | 1 vCPU |
| Memory | 512MB |
| Min instances | 0 (scale to zero) |
| Max instances | 3 (MVP) |
| Port | 8080 |
| Timeout | 60s per request |
| Region | asia-south1 |
| Auth | Unauthenticated for citizen endpoints; Firebase token for policymaker endpoints |

**API surface:**
```
POST /api/signals          -- Submit citizen signal (text or audio)
GET  /api/reports          -- List intelligence reports (auth required)
GET  /api/reports/{id}     -- Get specific report (auth required)
GET  /api/hotspots         -- Get hotspot list (auth required)
POST /api/copilot          -- Send Copilot query (auth required)
GET  /api/conflicts        -- Get evidence conflicts (auth required)
GET  /health               -- Health check (no auth)
```

### 3.2 civic-frontend (Next.js)

| Property | Value |
|----------|-------|
| Runtime | Node.js 20 |
| Framework | Next.js 14 App Router |
| Container | `Dockerfile.frontend` |
| CPU | 1 vCPU |
| Memory | 512MB |
| Min instances | 0 |
| Max instances | 3 |
| Port | 3000 |
| Region | asia-south1 |
| Auth | Firebase Auth (Google provider) |

**Alternative:** Deploy frontend to Firebase Hosting (static export) if Next.js SSR is not needed for policymaker routes. Evaluate after P3 UX.

---

## 4. Current Hackathon MVP Deployment

The current implementation deployed for the hackathon MVP utilizes a minimal, local-file based persistence layer.

### 4.1 Resource Model
- **Backend Cloud Run Service**: Runs the FastAPI backend.
- **Frontend Cloud Run Service**: Runs the Next.js frontend in standalone mode.
- **Container Image Registry**: Hosts the Docker images (e.g., GCR or Artifact Registry).
- **Gemini Provider**: Configured securely via environment variables (API key).
- **Static Datasets**: Normalized CSV and GeoJSON files are bundled directly into the backend Docker image.
- **Dynamic State**: Uses local `.jsonl` files in `data/local_development/` to hold generated demo state.

### 4.2 Persistence Limitation (Single-Instance Requirement)
- The Cloud Run filesystem is **ephemeral**. Restarting or replacing the instance will remove the dynamic local JSONL state, meaning the demo dataset must be recreated by running the pipeline again.
- **CRITICAL**: The backend Cloud Run service MUST be deployed with **`max instances = 1`**.
- **Why?** Dynamic JSONL state is local to a specific instance container and is not shared across instances. Multi-instance deployment is NOT supported for this MVP as it would cause split-brain data anomalies (e.g., frontend fetching map data from an instance that didn't run the demo scenario).
- This is a deliberate, temporary constraint designed specifically for a controlled hackathon demo presentation.

---

## 5. Future Scalable Production Architecture

*(The following sections describe the intended future architecture incorporating BigQuery, Cloud Storage, and Firebase. These are NOT required for the current Hackathon MVP.)*

### 5.1 BigQuery Configuration (Future)

```
Project: [GCP project ID]
Dataset: civic_intelligence
Location: asia-south1

Tables: (see data-architecture.md for full schemas)
  lgd_states, lgd_districts, lgd_blocks, lgd_villages
  lgd_historical_mapping
  citizen_signals, civic_needs, need_links
  evidence_jjm_village, evidence_jjm_district
  evidence_mission_antyodaya, evidence_census_2011
  gap_assessments, priority_assessments
  intelligence_reports, evidence_ledger
  evidence_conflicts

IAM:
  civic-backend-sa@[project].iam.gserviceaccount.com
    roles/bigquery.dataEditor (for inference tables)
    roles/bigquery.dataViewer (for evidence tables -- read-only)
    roles/bigquery.jobUser

  ingest-sa@[project].iam.gserviceaccount.com
    roles/bigquery.dataEditor (for all tables -- ingestion only)
```

---

### 5.2 Cloud Storage Configuration

```
Buckets:
  civic-raw-data-[env]      (multi-regional: asia)
    Purpose: LGD, JJM, Mission Antyodaya CSV snapshots
    Access: ingest-sa only
    Lifecycle: No deletion (snapshots are permanent record)

  civic-audio-[env]         (regional: asia-south1)
    Purpose: Citizen voice submissions
    Access: civic-backend-sa (write); Gemini API (signed URL read)
    Lifecycle: Delete objects after 24 hours (privacy policy)

Retention:
  civic-audio: TTL 24h lifecycle rule on all objects
  civic-raw-data: No lifecycle deletion (data governance)
```

---

### 5.3 Secret Manager Configuration

```
Secrets (all in asia-south1):
  gemini-api-key             (accessed by civic-backend-sa)
  firebase-admin-sdk-json    (accessed by civic-backend-sa)
  maps-api-key               (accessed by civic-frontend)
  bigquery-credentials       (accessed by civic-backend-sa)
```

---

### 5.4 Firebase Authentication (Future)

```
Provider: Google OAuth
Authorized domains:
  - [cloud-run-frontend-url].run.app
  - [custom-domain if configured]

Custom claims:
  role: "policymaker" | "admin"
  (set via Firebase Admin SDK during user provisioning)

Session management:
  - ID tokens expire after 1 hour (Firebase default)
  - Frontend refreshes token automatically
  - Backend always validates token server-side (no caching)
```

---

## 6. Deployment Sequence (Current Hackathon MVP)

1. Build backend image:
   ```bash
   docker build -f Dockerfile.backend -t gcr.io/[project]/civic-backend .
   ```

2. Push backend image to registry:
   ```bash
   docker push gcr.io/[project]/civic-backend
   ```

3. Deploy backend (CRITICAL: max instances = 1):
   ```bash
   gcloud run deploy civic-backend \
     --image gcr.io/[project]/civic-backend \
     --max-instances=1 \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=[KEY],ALLOWED_ORIGINS=http://localhost:3000,DEMO_LIVE_GEMINI_ENABLED=true"
   ```

4. Obtain the generated Backend URL (e.g., `https://civic-backend-[hash].run.app`).

5. Build frontend using the backend URL:
   ```bash
   docker build --build-arg NEXT_PUBLIC_API_URL=[BACKEND_URL] -f Dockerfile.frontend -t gcr.io/[project]/civic-frontend ./frontend
   ```

6. Deploy frontend:
   ```bash
   docker push gcr.io/[project]/civic-frontend
   gcloud run deploy civic-frontend \
     --image gcr.io/[project]/civic-frontend \
     --allow-unauthenticated
   ```

7. Obtain the generated Frontend URL.

8. Update backend `ALLOWED_ORIGINS` to correctly route CORS loopback:
   ```bash
   gcloud run services update civic-backend \
     --update-env-vars="ALLOWED_ORIGINS=[FRONTEND_URL]"
   ```

9. Perform end-to-end smoke test via the UI to verify demo scenario execution.
```

---

## 7. Environment Configuration

```bash
# civic-backend env (Cloud Run environment variables)
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET=civic_intelligence
GCS_RAW_BUCKET=civic-raw-data-prod
GCS_AUDIO_BUCKET=civic-audio-prod
GEMINI_API_KEY=<from Secret Manager>
GEMINI_MODEL=gemini-3.8-flash    # configurable -- do not hardcode in application code
FIREBASE_PROJECT_ID=your-firebase-project
ENVIRONMENT=production

# civic-frontend env (build-time or runtime)
NEXT_PUBLIC_BACKEND_URL=https://civic-backend-[hash]-uc.a.run.app
NEXT_PUBLIC_FIREBASE_CONFIG=<firebase web config JSON>
NEXT_PUBLIC_MAPS_API_KEY=<from Secret Manager via server>
NEXT_PUBLIC_ENVIRONMENT=production
```

---

## 8. Health Checks and Monitoring

**Backend health check:**
```
GET /health
Response: {"status": "ok", "bigquery": "ok", "gemini": "reachable", "version": "1.0.0"}
Cloud Run: Liveness probe on /health (30s interval)
```

**Monitoring:**
- Cloud Run: CPU, memory, request latency, error rate (built-in Cloud Monitoring)
- BigQuery: Query latency via Cloud Monitoring
- Gemini API: Track response times and error rates in application logs
- Cloud Logging: All structured logs from backend (JSON format)

---

## 9. Failure Isolation

| Component | Failure Impact | Mitigation |
|-----------|---------------|-----------|
| Gemini API down | Signal extraction fails | Store signals; batch retry; UI "AI unavailable" |
| BigQuery unavailable | Reports cannot be generated | Return cached reports; show "data may be stale" |
| Cloud Storage (audio) down | Voice submissions fail | Prompt text fallback immediately |
| Firebase Auth down | Policymaker login fails | Citizen portal remains fully functional |
| Maps API quota | Map pins fail to load | Fall back to tabular hotspot list (always rendered) |
| Backend Cloud Run | API unavailable | Frontend shows offline state; no data loss |
| Frontend Cloud Run | Dashboard unavailable | Backend API still accepts signals |

---

## 10. Demo Reliability

For the hackathon demo, maintain a **read-only demo mode**:

1. Pre-generate 3-5 Intelligence Reports for West Godavari and YSR Kadapa
2. Store these as fixtures that render without live API calls
3. Provide a `?demo=true` URL parameter that loads fixture data
4. Demo mode clearly labeled: "[DEMO MODE -- Pre-loaded Intelligence Reports]"

This ensures the demo works even if Gemini or BigQuery has latency issues during the live presentation.

---

## 11. CI/CD (Minimal for MVP)

```
GitHub Actions:
  on: push to main
  steps:
    1. Run backend tests (pytest)
    2. Build backend Docker image
    3. Push to GCR
    4. Deploy to Cloud Run (civic-backend)
    5. Run frontend lint + build
    6. Build frontend Docker image
    7. Push to GCR
    8. Deploy to Cloud Run (civic-frontend)
    9. Smoke test: GET /health
```

---

## 12. Observability and Diagnostics (Phase 10B-2C)

**Structured Logging**: All backend application logs are structured as JSON via `python-json-logger` for reliable machine ingestion in production, falling back to simple console formatting during local development.

**Request Correlation**: All logs during an API request are tagged with a unified `request_id`, propagated via `contextvars`, ensuring trace visibility without requiring external distributed tracing (like OpenTelemetry) for the MVP.

**Safe Error Logging**:
- Gemini API errors are caught, returning a generic, safe client message ("The AI provider is currently unavailable.") while logging the specific `error_type` internally. No raw exceptions or strings are logged.
- Internal repository persistence errors log their safe class name and error type rather than exposing file paths or raw exception traces.
- Copilot safety bounds (like max loop execution) emit a structured safety event log.

**JSONL Corruption Resilience**: Data repositories parsing `.jsonl` files (e.g., `EvidenceLedgerRepository`) swallow parsing exceptions, skip the malformed line, and log a structural warning with the line number to ensure a single broken row does not crash the application.

**Authentication Note**: The application currently operates without active Firebase Auth JWT verification during MVP and development iterations, prioritizing offline demo usability.

---

*Architecture V1 -- 2026-09-24*
