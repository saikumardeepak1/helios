# Technical Design Document: Helios

## Status
Draft v1.0 — Foundation phase. Companion to [PRD.md](PRD.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Overview
Helios is a multi-package repository with three deployable units — an API service, a web dashboard, and a background worker — sharing one Postgres database and one Redis instance, plus a Python SDK package published for external agent consumption.

## 2. Repository layout
```
helios/
  apps/
    api/                FastAPI backend (ingestion, auth, dashboard REST API, worker entrypoint)
      app/
        api/             route modules
        models/          SQLAlchemy models
        schemas/         Pydantic schemas
        services/        business logic (ingestion, cost calc, detectors, risk scoring)
        core/            config, security, db session
        workers/         RQ job definitions
      alembic/           migrations
      tests/
    web/                 Next.js dashboard
      app/               App Router routes
      components/
      lib/
      tests/
  packages/
    sdk-python/          helios-sdk: pip-installable agent instrumentation client
  infra/
    docker-compose.yml
  docs/
  .github/workflows/
```

## 3. Backend design

### 3.1 Tech stack
Python 3.12, FastAPI, SQLAlchemy 2.0 (async engine, asyncpg driver), Alembic, Pydantic v2, RQ + Redis for background jobs, `passlib`/`bcrypt` for password hashing, `python-jose` for JWT.

### 3.2 Services layered under `app/services/`
- `ingestion_service`: validates and persists incoming trace/span payloads, enqueues a `analyze_run` job.
- `cost_service`: looks up per-model pricing, computes cost per span and rolls up to run/agent/org.
- `pii_service`: regex/pattern-based PII scan over prompt/completion/tool-call text.
- `injection_service`: pattern + heuristic scan for prompt injection signatures.
- `risk_service`: combines detector outputs into a 0-100 risk score and creates `Alert` rows above threshold.
- `auth_service`: API key issuance/verification, JWT session issuance/verification.

### 3.3 API surface (high level, detailed OpenAPI generated at `/docs`)
- `POST /v1/ingest/traces` — API-key authenticated, accepts a run's trace/span payload.
- `POST /v1/auth/login`, `POST /v1/auth/refresh` — JWT session auth for dashboard users.
- `GET /v1/agents`, `GET /v1/runs`, `GET /v1/runs/{id}` — trace explorer data, JWT authenticated.
- `GET /v1/cost/summary` — cost analytics, JWT authenticated.
- `GET /v1/alerts`, `GET /v1/alerts/{id}` — security dashboard data, JWT authenticated.
- `GET /health` — unauthenticated liveness check.

### 3.4 Async processing
Ingestion writes the raw run/spans synchronously (fast, so the SDK call returns quickly) and enqueues an `analyze_run(run_id)` RQ job. That job runs cost calculation and both security detectors, then risk scoring, then writes any `Alert` rows. This keeps ingestion latency low and independent of detector cost.

### 3.5 Auth design
Two independent auth dependencies in FastAPI:
- `require_api_key`: reads `Authorization: Bearer hel_live_...`, looks up the hashed key, resolves to an `Organization`. Used on ingestion routes.
- `require_session`: reads a JWT from `Authorization: Bearer <jwt>`, resolves to a `User` scoped to an `Organization`. Used on dashboard routes.

API keys are generated with a `hel_live_` prefix, shown once at creation, stored as a salted hash. JWTs are short-lived access tokens with a refresh-token rotation flow.

## 4. Frontend design
Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui components, TanStack Query for server state, Recharts for charts. Server components fetch dashboard summary data; client components handle interactive filtering (trace explorer search, date range pickers).

## 5. Data model
See [ARCHITECTURE.md](ARCHITECTURE.md) for the entity relationship diagram. Core tables: `organizations`, `users`, `api_keys`, `agents`, `runs`, `spans`, `tool_calls`, `cost_records`, `alerts`.

## 6. Testing strategy
- **Unit tests**: services (`cost_service`, `pii_service`, `injection_service`, `risk_service`) tested in isolation with fixture payloads.
- **Integration tests**: API routes tested against a real (test) Postgres via `httpx.AsyncClient`, using pytest fixtures that spin up a transactional session per test.
- **Frontend unit tests**: component tests via Vitest + Testing Library.
- **API contract tests**: OpenAPI schema validated against example requests/responses in CI.
- Coverage tracked via `pytest-cov`, reported in CI job summary.

## 7. CI/CD
GitHub Actions, one workflow (`ci.yml`) with parallel jobs: `api-test` (ruff, mypy, pytest), `web-test` (eslint, tsc, vitest, next build), `docker-build` (build all Dockerfiles to verify they build cleanly). All required to pass before merge.

## 8. App-level observability
Helios dogfoods structured logging on itself, independent of the OpenTelemetry-style ingestion it offers customers for their agents.

- **JSON logs everywhere**: `app/core/logging.py#configure_logging` replaces the root logger's handler with one JSON line per record (`timestamp`, `level`, `logger`, `message`, plus `correlation_id` when set) — both the API process and the RQ worker call it at startup, so `docker compose logs` produces machine-parseable output for either.
- **Correlation IDs, not manually threaded**: a `contextvars.ContextVar` (`correlation_id_var`) holds the current request or job's id. `CorrelationIdMiddleware` sets it from an inbound `X-Request-ID` header (generating one if absent) for the duration of each API request and echoes it back on the response; `analyze_run` generates a `job-<hex>` id and sets it for the duration of that job. Every log line emitted anywhere during that request or job — across services, without passing an id parameter through every function signature — carries the same value, so `grep`-ing one id reconstructs the full story of one request or one background job.
- **Implementation note**: the correlation id is injected via `logging.setLogRecordFactory`, not a `logging.Filter` on a handler. A handler-level filter only fires for log calls that propagate through that specific handler; a submodule logger with its own directly-attached handler (which is exactly how both RQ's own logging and pytest's `caplog` work) would never see it. Replacing the record factory stamps the field onto every `LogRecord` at creation time, before any filter or handler runs, so it's independent of the logger hierarchy or which handler ends up processing it — including in tests.

## 9. Deployment
Docker Compose is the primary deployment target for v1: `docker-compose.yml` defines `api`, `worker`, `web`, `postgres`, `redis`. Documented in [deployment guide](../README.md#deployment) once written. Environment configuration via `.env` (see `.env.example`).

## 10. Tradeoffs and future improvements
- RQ over Celery: simpler ops, adequate for the job volume expected at this scale; would reconsider for very high ingestion throughput.
- Rule-based detectors over ML classifiers for PII/injection: explainable and dependency-light for v1; documented as a future upgrade path.
- Single-tenant-per-organization row scoping instead of schema-per-tenant: simpler migrations, sufficient isolation for v1's threat model.
