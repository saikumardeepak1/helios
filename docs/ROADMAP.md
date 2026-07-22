# Roadmap: Helios

Tracked as GitHub milestones and issues on this repository. This doc is the human-readable mirror.

## Milestone 1: Foundation
- Project scaffolding & CI/CD pipeline
- Database schema design (Postgres + Alembic)
- API authentication (API keys + JWT sessions)
- Frontend app shell & design system setup

## Milestone 2: Core Observability
- OTLP-style trace ingestion endpoint
- Agent/run/span data storage service
- Python SDK for agent instrumentation (`helios-sdk`)
- Trace explorer UI (list + detail + replay view)
- Latency & token/cost tracking pipeline
- Cost analytics dashboard

## Milestone 3: Security & Governance
- PII detection service
- Prompt injection detection service
- Risk scoring engine
- Alert generation & security dashboard

## Milestone 4: Platform Hardening
- Structured logging & app-level observability (dogfooding OpenTelemetry)
- Test coverage: unit + integration + API tests
- Deployment guide & production Docker Compose hardening
- API documentation (OpenAPI + docs site)

## Sequencing
Milestones are built roughly in order, but issues within a milestone may interleave where dependencies allow (e.g. the SDK and trace explorer UI can proceed in parallel once ingestion + data model land). Each issue ships as its own feature branch and PR — see `CONTRIBUTING.md` (added in the scaffolding PR) for the branch naming and PR conventions used in this repo.

## Explicitly out of scope for v1
- Multi-region/HA deployment
- Non-Python SDKs
- ML-based risk classifier (rule-based scoring only, documented as a future upgrade)
- Managed cloud hosting (Docker Compose self-host only)
