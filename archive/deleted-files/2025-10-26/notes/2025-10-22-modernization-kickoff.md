# Meeting Notes – Frontend Modernization Kickoff

**Date**: 2025-10-22  
**Attendees**: Dashboard Eng, Data Platform, QA Automation, DevOps  
**Facilitator**: Dashboard Eng Tech Lead

## Agenda
- Review objectives from `specs/012-modernize-frontend/spec.md`
- Confirm milestone dates and action owners
- Identify immediate risks and dependencies

## Discussion Highlights
- Supabase duplicate fetches confirmed as top pain; Data Platform provided staging credentials for testing.
- DevOps requested two-week notice before switching Vercel output to `dist/`.
- QA Automation will expand Playwright suite to cover provider caching; needs hooks delivered by Phase 2.
- Agreement to archive (not delete) legacy DOM client until after production validation.

## Decisions
- Adopt feature flag `USE_REAL_DATA_PROVIDER` to guard rollout (owner: Dashboard Eng).
- Bundle-size GitHub Action to run on every PR touching `src/**`.
- Manual QA checklist stored in `docs/qa/modernization-checklist.md` (owner: QA Automation).

## Action Items
- [ ] Dashboard Eng: Prepare action doc `actions/012-01-tooling.md` and open GitHub issue (#TBD).
- [ ] DevOps: Draft Vercel deploy change plan referencing `dist/` (due 2025-11-05).
- [ ] QA Automation: Outline additional Playwright scenarios (due 2025-10-29).

## Next Steps
- Weekly sync every Wednesday with notes committed under `notes/`.
- Track progress on project board `Modernization (Spec 012)`.
