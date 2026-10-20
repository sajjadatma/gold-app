# Jewelry Brand Studio Engineering Rules

Build MVP1 autonomously.

## Priority

1. Correct MVP behavior
2. Security and tenant isolation
3. Simplicity
4. Tests
5. Maintainability
6. Performance only when needed

## No overengineering

Implement only current MVP acceptance criteria.

Do not build infrastructure, abstractions, frameworks, generic systems, or future-facing features unless required now.

Prefer the smallest working solution.

## Questions

Do not ask routine questions.

Choose the strongest reasonable recommendation and continue.

Ask only before dangerous, destructive, costly, secret-bearing, production, or irreversible external operations.

## Architecture

Preserve Full Stack FastAPI Template conventions.

Use a modular monolith.

One background worker only.

No microservices.

## Agents

Use one primary agent.

Do not spawn subagents.

## AI

Keep external provider adapters thin.

Fake providers must support tests.

Validate structured AI output before persistence.

## Git

Target:
https://github.com/sajjadatma/gold-app.git

Branch:
main

At the end of every completed stage:

- verify tests
- inspect diff
- commit
- push normally to origin/main
- update docs/progress.md

Never force-push or rewrite published history without human approval.

## Testing

Do not weaken/delete tests to make a build green.

When OpenAPI changes, regenerate the frontend client.

## Security

Never read or expose secrets unless explicitly required and approved.

Never commit credentials.

Treat uploads as untrusted.

Protect tenant boundaries.

## Completion

Continue stage by stage until the MVP Definition of Done is satisfied.
