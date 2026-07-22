# Product Requirements Document: Helios

## Status
Draft v1.0 — Foundation phase

## Summary
Helios is an observability and governance platform for AI agents. Teams that deploy LLM-based agents in production currently have no reliable way to answer basic operational questions: why did this agent run fail, how much is this feature costing per day, is this agent leaking PII, and is someone trying to jailbreak it. Helios gives engineering and security teams a single place to trace agent executions, monitor cost and latency, and catch security risks before they become incidents.

## Problem statement
Organizations deploying AI agents lack visibility into:
- **Failures** — why a given agent run produced a bad or broken result
- **Hallucinations** — when an agent's output diverges from its inputs/tools in ways that indicate fabrication
- **Costs** — per-agent, per-feature, per-day token and dollar spend
- **Tool usage** — which tools an agent called, with what arguments, and what came back
- **Latency** — where time is spent inside a multi-step agent run
- **Security risks** — PII exposure, prompt injection attempts, and other risky behavior

Today teams either build ad hoc logging around each agent (inconsistent, expensive to maintain) or fly blind.

## Goals
1. Give any team a drop-in SDK that instruments an agent in a few lines and starts streaming structured traces to Helios.
2. Provide a trace explorer that lets an engineer reconstruct exactly what an agent run did, step by step, including every tool call and its inputs/outputs.
3. Track token usage and cost per agent, per organization, with a cost dashboard that surfaces spend trends.
4. Detect security-relevant events in agent input/output — PII, prompt injection attempts — and raise scored alerts.
5. Be self-hostable via Docker Compose with a documented deployment path.

## Non-goals (v1)
- Multi-region / high-availability deployment topology.
- Fine-tuning or model-hosting features — Helios observes agents, it does not run them.
- Full SIEM-grade security correlation (Sentinel, a separate system in this lab, owns broader security operations).
- Non-Python SDKs (JS/TS SDK is a plausible v2 addition, not v1).

## Target users
- **Platform/backend engineers** who own the agents in production and need to debug failures fast.
- **Engineering leadership / finance** who need reliable cost attribution for AI features.
- **Security engineers** who need to know when an agent mishandled sensitive data or was targeted by a prompt injection attempt.

## Core features

### Tracing
- Agent execution tracing: full run → step → tool-call hierarchy.
- Prompt tracking: every prompt sent to a model, versioned per run.
- Tool call visualization: arguments in, result out, latency per call.
- Execution replay: reconstruct a run's timeline from stored spans.
- Latency tracking: per-span and per-run duration breakdown.
- Token tracking: prompt/completion tokens per call, rolled up per run.
- Cost analytics: token counts converted to cost using per-model pricing tables, rolled up per agent/org/day.

### Security
- PII detection: scan prompts/completions/tool payloads for common PII patterns (emails, phone numbers, SSNs, credit cards).
- Prompt injection detection: heuristic + pattern-based scan for injection attempts in user-supplied input.
- Sensitive data monitoring: flag spans that touch data marked sensitive.
- Risk scoring: combine detector signals into a per-run risk score.
- Alert generation: create an `Alert` record when risk crosses a threshold, visible in the security dashboard.

### Dashboard
- Agent health: recent run success/failure rate, latency trend.
- Failure analysis: filterable list of failed runs with root-cause spans surfaced.
- Trace explorer: search/filter runs, drill into a single run's full timeline.
- Cost explorer: spend by agent, by day, by model.
- Usage analytics: run volume, tool-call volume over time.
- Security alerts: list and detail view for generated alerts, with the triggering span highlighted.

## Success criteria (v1)
- An agent can be fully instrumented with the Python SDK in under 10 lines of code.
- A trace ingested via the SDK is queryable in the trace explorer within 2 seconds (async pipeline latency).
- Cost dashboard numbers reconcile with token counts times the configured pricing table to the cent.
- PII/prompt-injection detectors run against every ingested run without blocking ingestion latency (async worker).
- Entire stack (`api`, `web`, `worker`, `postgres`, `redis`) starts with a single `docker compose up`.

## Open questions
- Exact model pricing table source (hardcoded config vs. pulled from a live pricing API) — starting hardcoded/configurable, revisit if a provider API is worth integrating.
- Whether risk scoring should be rule-based only for v1 or include a lightweight ML classifier — starting rule-based for explainability, ML classifier is a documented future improvement.
