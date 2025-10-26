# Action 012-01: Tooling Baseline & CI Guardrails

**Spec**: `specs/012-modernize-frontend/spec.md`  
**Plan Milestone**: `specs/012-modernize-frontend/plan.md` → M1  
**Status**: Planned  
**Owner**: Dashboard Engineering  
**Created**: 2025-10-22  
**Due Date**: 2025-10-25

---

## Objective
Establish consistent local + CI tooling so future phases run against a stable quality gate baseline. Capture bundle sizing and environment configuration before refactors start.

## Tasks
1. Add lint, typecheck, unit, e2e, and production build scripts to `package.json`.
2. Update CI workflow to execute full suite on PRs that touch dashboard code.
3. Capture bundle baseline metrics (`docs/perf/bundle-baseline.json` and summary Markdown).
4. Publish `frontend/.env.example` and ignore local env files.

## Verification
- `npm run lint`
- `npm run typecheck`
- `npm run test:unit`
- `npm run test:ui`
- `npm run build:prod`
- CI workflow run URL confirming successful execution.
- Attached `docs/perf/bundle-baseline.json` (before metrics).

## Evidence Checklist
- [ ] Command outputs / CI screenshots
- [ ] Bundle baseline artifacts committed
- [ ] .env example and documentation updates
- [ ] QA sign-off (Tooling) – reviewer: QA Automation

## Notes
- Coordinate with DevOps before altering CI workflow to avoid clashes with existing jobs.
- If bundle baseline collection fails, record troubleshooting steps in `notes/`.
