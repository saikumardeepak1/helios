# Helios

AI Agent Observability Platform — tracing, cost analytics, and security monitoring for production AI agents.

## Why Helios

Teams shipping AI agents can't answer basic operational questions: why a run failed, what it's costing, what tools it called, or whether it leaked sensitive data. Helios gives you a drop-in SDK and a dashboard to answer all of that.

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [Technical Design Document](docs/TDD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- **API reference** — interactive, generated from the running API: Swagger UI at `/docs`, ReDoc at `/redoc` (e.g. http://localhost:8000/docs once the stack is up). Every route has a description and every schema has an example payload — there's no separately maintained API doc to go stale.

## Status

Early development. See [Roadmap](docs/ROADMAP.md) and the [issue tracker](https://github.com/saikumardeepak1/helios/issues) for current progress.

## Project structure

```
apps/api/           FastAPI backend
apps/web/            Next.js dashboard
packages/sdk-python/ Python agent instrumentation SDK
infra/               Docker Compose and deployment config
docs/                Planning and architecture docs
```

## Getting started

Requires Docker, Python 3.12+, and Node 20+.

```bash
cp apps/api/.env.example apps/api/.env
# edit apps/api/.env — at minimum, set a real JWT_SECRET (see the comment in that file)

docker compose -f infra/docker-compose.yml up --build

# api: http://localhost:8000 (docs at /docs)
# web: http://localhost:3000
```

That brings up `postgres`, `redis`, a one-shot `migrate` service (applies Alembic migrations, then exits — `api` and `worker` both wait for it to finish before starting), `api`, `worker`, and `web`.

### Running services individually

```bash
# API
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Worker (needs Postgres + Redis reachable, and migrations already applied)
cd apps/api && source .venv/bin/activate
python -m app.workers.worker

# Web
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

### Running tests

```bash
# API
cd apps/api && source .venv/bin/activate && pytest -q --cov=app

# Web
cd apps/web && npm run test          # unit/component tests
cd apps/web && npm run test:e2e      # Playwright E2E (builds and serves the app itself)

# SDK
cd packages/sdk-python && source .venv/bin/activate && pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch/PR workflow.

## Deployment

The `docker-compose.yml` in `infra/` is the primary deployment target for v1 — a single-host stack suitable for a small/medium production workload. It is not a multi-region or auto-scaling setup; see [docs/ROADMAP.md](docs/ROADMAP.md) for what's explicitly out of scope.

### 1. Configure environment

```bash
cp apps/api/.env.example apps/api/.env
```

Edit `apps/api/.env` and set:
- **`JWT_SECRET`** — a real random secret (`python -c "import secrets; print(secrets.token_urlsafe(32))"`). The example value is public (it's in this repo's git history); deploying with it means anyone can forge session tokens.
- Anything else you want to change from the defaults (token expiry, etc).

`DATABASE_URL` and `REDIS_URL` in `.env` are for running the API outside Docker — `docker-compose.yml` overrides both to point at the `postgres`/`redis` service hostnames automatically, so you don't need to edit those for a Compose deployment.

If you're deploying `postgres`'s data past local testing, also change `POSTGRES_PASSWORD` in `infra/docker-compose.yml` from the default `helios`.

### 2. Bring up the stack

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

Service startup order (enforced by `depends_on` + healthchecks, not just sleep/retry):
1. `postgres` and `redis` start; each service downstream waits for their healthcheck to pass.
2. `migrate` runs `alembic upgrade head` once and exits 0.
3. `api` and `worker` both wait for `migrate` to complete successfully before starting — this is what guarantees the worker never processes a job against tables that don't exist yet on a fresh deploy.
4. `web` starts once `api`'s container exists (it calls the API from the browser at runtime, not at web-server startup, so it doesn't need to wait for `api`'s healthcheck).

Check everything is healthy:

```bash
docker compose -f infra/docker-compose.yml ps
curl http://localhost:8000/health
```

### 3. Building the web image for a non-localhost API

`NEXT_PUBLIC_API_URL` is inlined into the browser bundle at **build time**, not read at container start. If the API won't be reachable at `http://localhost:8000` from your users' browsers, rebuild with the real URL:

```bash
docker compose -f infra/docker-compose.yml build --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com web
```

(and update the `NEXT_PUBLIC_API_URL` build arg in `infra/docker-compose.yml` to match, so future rebuilds don't silently drop back to `localhost`.)

### 4. Logs

Both `api` and `worker` emit structured JSON logs (one object per line: `timestamp`, `level`, `logger`, `message`, and `correlation_id` when available) — see [docs/TDD.md §8](docs/TDD.md) for how correlation ids tie one request or one background job's logs together.

```bash
docker compose -f infra/docker-compose.yml logs -f api worker
```

### 5. Backups

The only stateful volume is `postgres_data`. Back up Postgres the way you'd back up any Postgres instance (`pg_dump`, a managed Postgres provider's snapshotting, etc.) — nothing Helios-specific is required.

### What this setup doesn't cover

- TLS termination — put a reverse proxy (nginx, Caddy, a cloud load balancer) in front of `api` and `web` for anything beyond local testing.
- Horizontal scaling — `worker` can be scaled with `docker compose up --scale worker=3`, since RQ workers just compete for jobs on the same queue; `api` can be scaled similarly behind a load balancer, but that's untested past this repo's own CI.
- Managed/HA Postgres and Redis — the compose file runs single-instance containers, fine for the workload this is designed for, not for high-availability requirements.

## License

MIT — see [LICENSE](LICENSE).
