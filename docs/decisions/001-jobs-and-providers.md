# ADR 001 — One queue, thin providers, eager test mode

**Status:** accepted

## Context

MVP1 needs async jobs, interchangeable external vendors, and a test suite that
never depends on paid services.

## Decision

- Use Redis + one `arq` worker. No generic workflow engine.
- Keep provider adapters as small functions/classes in `app/providers/`.
- Default to deterministic fakes. `TASKS_EAGER=true` runs the same job functions
  inline for tests and local demos; production sets it to false.
- Brand import analysis stays synchronous because supported imports are bounded.

## Consequences

The whole MVP is testable without credentials, while production can enable real
storage, AI, and Instagram via environment variables. Duplicate work is avoided:
job functions are shared between eager and queued execution.
