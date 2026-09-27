# Civic Demand Intelligence (Frontend)

The frontend for the **Civic Demand Intelligence** platform: a policymaker intelligence workspace designed to process and map citizen signals against deterministic infrastructure evidence.

## Features

- **Policymaker Intelligence Workspace**: A unified dashboard for evaluating citizen demand against official development gaps.
- **Interactive Hotspot Map**: Leaflet-based geospatial visualization of infrastructure hotspots.
- **Analytics Summary**: High-level convergence scoring and unmet demand aggregation.
- **Village Lookup**: LGD (Local Government Directory) code-based precise geography resolution.
- **VillageContext Synchronization**: Seamless state sharing between map selection, analytics panels, and AI interactions.
- **Civic Copilot**: A grounded chat interface for policymakers to query evidence ledgers.
- **Live vs Mock Demonstration Flow**: Distinct paths for deterministic mock data versus real-time (controlled) synthetic signal ingestion.
- **Unmet Demand / Convergence / Priority Views**: Detailed breakdowns of calculated need versus existing policy priorities.
- **Evidence Ledger Presentation**: Read-only rendering of official infrastructure data.
- **Provenance Indicators**: Visual tags distinguishing synthetic demo signals from real/official data.

## Technology Stack

- **Next.js**
- **React**
- **TypeScript**
- **Leaflet / React Leaflet**
- **Vitest**

## Current MVP Architecture

This frontend is a strictly bounded presentation layer. It **does not** perform authoritative civic calculations, manage databases, or directly interface with generative AI. It exclusively consumes backend APIs for all priority assessments, convergence logic, and Copilot orchestrations.

## Local Development

Start the local development server:

```bash
npm run dev
```

Run the unit and component test suite:

```bash
npm run test
```

Run the linter:

```bash
npm run lint
```

## Production Build

Generate the production build:

```bash
npm run build
```

To start the built application:

```bash
npm run start
```

## Environment Configuration

The frontend currently uses exactly one environment variable for API routing:

- `NEXT_PUBLIC_API_URL`: The base URL for backend API requests (defaults to `http://localhost:8000` if unset).

*No credentials, API keys, or secret values are required or processed by the frontend.*

## Current MVP Limitations

This repository represents a **hackathon prototype**. Please note the following boundaries:

- **Synthetic Demo Signals**: Signals generated during the Live Demo flow are entirely synthetic. This system is not ingesting real citizen grievances.
- **Deterministic Official Evidence**: The infrastructure gap data presented is static, snapshot-based official evidence. There is no real-time government database synchronization.
- **MVP Scope**: This is a bounded prototype intended for demonstration. It is not a production-ready or live deployment.
- **Ephemeral Runtime State**: State generated during demonstrations relies on ephemeral local storage and is not permanently persisted.
