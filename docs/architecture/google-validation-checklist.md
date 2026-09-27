# Google Service Validation Checklist

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24
>
> This document lists all Google-specific assumptions that must be verified
> before or during implementation. Do NOT treat these as confirmed facts.

---

## How to Use This Document

For each item:
1. Mark `[x] VERIFIED` when confirmed in official documentation or tested
2. Mark `[!] BLOCKED` if verification reveals a blocking constraint
3. Add the verified value or documentation link

---

## Gemini API Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| G-01 | `gemini-2.0-flash` supports `response_schema` / `response_mime_type: application/json` | [ ] Pending | Critical -- structured output is foundational |
| G-02 | `gemini-2.0-flash` supports multimodal audio input (not just text) | [ ] Pending | Required for voice feature |
| G-03 | Audio can be passed via GCS URI (`Part.from_uri`) without downloading to backend | [ ] Pending | Assumed in architecture; verify |
| G-04 | `gemini-2.0-flash` supports Hindi, Telugu, Tamil, Kannada audio with adequate accuracy | [ ] Pending | Verify with test recordings |
| G-05 | Function calling (tool declarations) works with `gemini-2.0-flash` | [ ] Pending | Required for Copilot |
| G-06 | Structured output schema via Pydantic `response_schema` parameter works as documented | [ ] Pending | Test with CivicNeedExtraction schema |
| G-07 | Google AI Studio API key works for production load (not just prototyping) | [ ] Pending | Check rate limits and quota |
| G-08 | `temperature=0.1` is a valid configuration for `gemini-2.0-flash` | [ ] Pending | Confirm API accepts temperature param |
| G-09 | Token limits: 1M context window applies to `gemini-2.0-flash` (not only Pro) | [ ] Pending | Verify for Flash model |
| G-10 | Free tier / paid tier quotas sufficient for hackathon demo load | [ ] Pending | Check: requests per minute, tokens per day |
| G-11 | Audio file size limits for multimodal input | [ ] Pending | Architecture assumes 5MB max |
| G-12 | Supported audio formats (WAV, MP3, OGG) for multimodal input | [ ] Pending | Verify supported MIME types |
| G-13 | `google-genai` Python SDK version compatible with `response_schema` | [ ] Pending | Check PyPI version >= 0.3.x |

---

## BigQuery Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| B-01 | BigQuery sandbox (free tier) supports all table operations needed | [ ] Pending | Check: partitioned tables, CLUSTER BY, JSON columns |
| B-02 | `asia-south1` region supports all required BigQuery features | [ ] Pending | Some features are US-only |
| B-03 | Cloud Run service account can connect to BigQuery without VPC | [ ] Pending | Direct API connection assumed |
| B-04 | Parameterized queries work as expected with Python `google-cloud-bigquery` client | [ ] Pending | Test with complex JOINs |
| B-05 | BigQuery STRUCT / JSON column types supported in `asia-south1` | [ ] Pending | Used for `report_json` and `assumptions` |
| B-06 | BigQuery Data Editor role grants INSERT without SELECT * on all tables | [ ] Pending | Confirm IAM boundaries |
| B-07 | Query response time < 2s for hotspot aggregation queries on MVP data volume | [ ] Pending | Performance assumption |
| B-08 | Partitioned tables by DATE work with TIMESTAMP partition column | [ ] Pending | Schema uses TIMESTAMP for partition |

---

## Cloud Run Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| C-01 | Cloud Run supports Python 3.11 Docker containers in `asia-south1` | [ ] Pending | Verify region availability |
| C-02 | Cloud Run min-instances=0 (scale to zero) is available in free tier | [ ] Pending | Needed for cost management |
| C-03 | Cloud Run cold start < 5s for Python FastAPI container | [ ] Pending | Performance assumption |
| C-04 | Cloud Run can access Secret Manager at runtime without additional config | [ ] Pending | Service account permission assumed |
| C-05 | Cloud Run environment variables can be set from Secret Manager references | [ ] Pending | Verify Cloud Run --set-secrets flag |
| C-06 | Two Cloud Run services in same project can call each other via HTTPS | [ ] Pending | Frontend calling backend |
| C-07 | Maximum request timeout of 60s is sufficient for Gemini extraction | [ ] Pending | Gemini latency is variable |
| C-08 | Docker image size < 500MB for fast deploy | [ ] Pending | Python dependencies can be large |

---

## Cloud Storage Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| S-01 | Object lifecycle rules with 24-hour TTL work for audio bucket | [ ] Pending | Critical for privacy compliance |
| S-02 | Gemini API can access GCS objects via signed URL or Service Account | [ ] Pending | Assumed for audio processing |
| S-03 | Signed URL generation works from Cloud Run service account | [ ] Pending | Required for audio upload flow |
| S-04 | GCS `asia-south1` multiregional bucket is available | [ ] Pending | Data residency requirement |

---

## Firebase Authentication Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| F-01 | Firebase Auth Google OAuth provider works with Cloud Run frontend URL | [ ] Pending | Domain authorization required |
| F-02 | Firebase Admin SDK works from Cloud Run backend with service account | [ ] Pending | Token verification from backend |
| F-03 | Custom claims (role=policymaker) can be set via Firebase Admin SDK | [ ] Pending | Role-based access requirement |
| F-04 | Firebase Auth ID tokens expire after 1 hour (standard) | [ ] Pending | Confirm default behavior |
| F-05 | Firebase project can be in same GCP project as Cloud Run | [ ] Pending | Confirm setup approach |

---

## Google Maps Platform Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| M-01 | Maps JavaScript API supports district-level pins without polygon data | [ ] Pending | Using lat/lng points only |
| M-02 | Geocoding API can resolve Indian district names to lat/lng centroids | [ ] Pending | Test: "West Godavari, Andhra Pradesh" |
| M-03 | Maps API key can be restricted to specific domains (Cloud Run URL) | [ ] Pending | Security requirement |
| M-04 | Maps JavaScript API free tier (monthly $200 credit) sufficient for MVP | [ ] Pending | Verify usage estimate |
| M-05 | Maps API available in `asia-south1` without additional configuration | [ ] Pending | Regional availability |

---

## Secret Manager Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| SM-01 | Secret Manager available in `asia-south1` | [ ] Pending | Verify regional availability |
| SM-02 | Secrets can be versioned and accessed by version alias | [ ] Pending | Deployment best practice |
| SM-03 | Cloud Run can access secrets with default service account | [ ] Pending | Or explicit SA grant needed |

---

## Pricing and Quota Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| P-01 | Gemini API free tier supports ~500 extraction calls/day | [ ] Pending | Check AI Studio quotas |
| P-02 | BigQuery free tier (1TB queries/month) sufficient for MVP | [ ] Pending | Estimate: ~50MB queries for demo |
| P-03 | Cloud Run free tier (2M requests/month) sufficient | [ ] Pending | MVP will be well under this |
| P-04 | Cloud Storage free tier (5GB) sufficient for raw data + audio | [ ] Pending | LGD + JJM CSVs estimated ~200MB |
| P-05 | Total GCP cost for 6-day MVP < $50 USD | [ ] Pending | Budget assumption |

---

## Deployment and Regional Assumptions

| # | Assumption | Status | Notes |
|---|-----------|--------|-------|
| D-01 | All required services available in `asia-south1` (Mumbai) | [ ] Pending | Critical for data residency |
| D-02 | Cloud Run supports custom domains with SSL certificates | [ ] Pending | Submission requires live URL |
| D-03 | GitHub Actions can deploy to Cloud Run via Workload Identity Federation | [ ] Pending | CI/CD assumption |
| D-04 | Docker builds on GitHub Actions (ubuntu-latest) produce amd64 images compatible with Cloud Run | [ ] Pending | Architecture compatibility |

---

## Verification Approach

For critical items (G-01, G-02, G-05, B-01, C-01):
- Test with a minimal proof-of-concept script on Day 1
- Document the exact API call that works
- Record any constraints discovered (e.g., audio format limitations)

For quota items (P-01 through P-05):
- Check official pricing pages (not cached documentation)
- Set up billing alerts in GCP console before Day 1

---

*Architecture V1 -- 2026-09-24*
