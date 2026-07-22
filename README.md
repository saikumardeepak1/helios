# Helios

AI Agent Observability Platform — tracing, cost analytics, and security monitoring for production AI agents.

## Why Helios

Teams shipping AI agents can't answer basic operational questions: why a run failed, what it's costing, what tools it called, or whether it leaked sensitive data. Helios gives you a drop-in SDK and a dashboard to answer all of that.

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [Technical Design Document](docs/TDD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)

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
# start the full stack (postgres, redis, api, web)
docker compose -f infra/docker-compose.yml up --build

# api: http://localhost:8000 (docs at /docs)
# web: http://localhost:3000
```

### Running services individually

```bash
# API
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Web
cd apps/web
npm install
npm run dev
```

### Running tests

```bash
# API
cd apps/api && source .venv/bin/activate && pytest -q --cov=app

# Web
cd apps/web && npm run test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch/PR workflow.

## License

MIT — see [LICENSE](LICENSE).
