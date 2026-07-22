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

Local development setup lands in the `feature/project-scaffolding` PR — this section will be filled in with `docker compose up` instructions once that merges.

## License

MIT — see [LICENSE](LICENSE).
