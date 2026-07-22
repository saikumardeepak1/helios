# Architecture: Helios

## System diagram

```mermaid
graph TB
    SDK["helios-sdk<br/>(instrumented agent)"] -->|"POST /v1/ingest/traces<br/>API key auth"| API

    subgraph Helios["Helios Platform"]
        API["FastAPI API service"]
        Worker["RQ worker<br/>(analyze_run job)"]
        Web["Next.js dashboard"]
        DB[(PostgreSQL)]
        Redis[(Redis<br/>queue)]

        API -->|"write run/spans"| DB
        API -->|"enqueue analyze_run"| Redis
        Redis -->|"job dequeue"| Worker
        Worker -->|"cost calc, PII scan,<br/>injection scan, risk score"| Worker
        Worker -->|"write cost_records, alerts"| DB
        Web -->|"JWT session auth<br/>REST queries"| API
        API -->|"read runs, cost, alerts"| DB
    end

    Analyst["Engineer / Security analyst"] -->|"browser"| Web
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| `helios-sdk` | Python package agents import to send trace/span data to the ingestion endpoint with minimal integration code |
| API service | Auth, ingestion, dashboard REST API, OpenAPI docs |
| Worker | Async analysis: cost rollup, PII detection, prompt injection detection, risk scoring, alert generation |
| Web dashboard | Trace explorer, cost explorer, security alerts, agent health views |
| PostgreSQL | System of record for all entities |
| Redis | Job queue between API and worker |

## Entity relationship (core tables)

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ API_KEY : has
    ORGANIZATION ||--o{ AGENT : owns
    AGENT ||--o{ RUN : produces
    RUN ||--o{ SPAN : contains
    SPAN ||--o{ TOOL_CALL : may_include
    RUN ||--o{ COST_RECORD : generates
    RUN ||--o{ ALERT : may_trigger

    ORGANIZATION {
        uuid id PK
        string name
        timestamp created_at
    }
    USER {
        uuid id PK
        uuid organization_id FK
        string email
        string hashed_password
        string role
    }
    API_KEY {
        uuid id PK
        uuid organization_id FK
        string prefix
        string hashed_key
        timestamp created_at
        timestamp revoked_at
    }
    AGENT {
        uuid id PK
        uuid organization_id FK
        string name
        string version
    }
    RUN {
        uuid id PK
        uuid agent_id FK
        string status
        timestamp started_at
        timestamp ended_at
        int risk_score
    }
    SPAN {
        uuid id PK
        uuid run_id FK
        uuid parent_span_id FK
        string kind
        json input
        json output
        int prompt_tokens
        int completion_tokens
        timestamp started_at
        timestamp ended_at
    }
    TOOL_CALL {
        uuid id PK
        uuid span_id FK
        string tool_name
        json arguments
        json result
    }
    COST_RECORD {
        uuid id PK
        uuid run_id FK
        string model
        numeric cost_usd
    }
    ALERT {
        uuid id PK
        uuid run_id FK
        string category
        string severity
        string detail
        timestamp created_at
    }
```

## Request flow: ingesting a trace

1. Instrumented agent calls `helios_client.log_run(...)` from `helios-sdk`.
2. SDK POSTs the run + spans to `/v1/ingest/traces` with its organization's API key.
3. API validates the key, persists `Run`/`Span`/`ToolCall` rows synchronously, returns 202 immediately.
4. API enqueues `analyze_run(run_id)` onto Redis.
5. Worker picks up the job: computes cost per span, runs PII/injection detectors over span input/output, computes a risk score, writes `CostRecord` and any `Alert` rows.
6. Dashboard queries reflect the enriched data on next poll/refetch.

## Deployment topology (v1)

Single-host Docker Compose: `api`, `worker`, `web`, `postgres`, `redis` containers on one Docker network, `web` and `api` exposed to the host. See the deployment guide in the root README once the scaffolding PR lands.
