# Risk Register 012 – Frontend Modernization & Deployment Hardening

| ID | Description | Impact | Likelihood | Mitigation | Owner | Status |
|----|-------------|--------|------------|------------|-------|--------|
| R1 | Removing legacy DOM client breaks undocumented consumers relying on `scripts/main.ts` | High | Medium | Survey stakeholders, archive client with clear re-enable instructions, keep fallback branch until GA | Dashboard Eng | Open |
| R2 | Supabase rate limits hit during new data-layer rollout, causing dashboard outages | High | Low | Test against staging with throttled mocks, add exponential backoff + telemetry to detect spikes | Data Platform | Open |
| R3 | Environment-variable migration misses production config, leading to runtime failures | High | Medium | Add build-time validation, update DevOps runbooks, stage with feature flag before production | DevOps | Open |
| R4 | Bundle size guard fails during heavy refactor, regressing performance | Medium | Medium | Capture baseline, add CI bundle-size action, require perf review on diffs >50 KB | Dashboard Eng | Open |
| R5 | Shared filter provider introduces stale caches causing outdated option lists | Medium | Medium | Implement TTL + background revalidation, add Playwright regression covering new landings scenario | Dashboard Eng | Open |
| R6 | Manual QA checklist skipped under schedule pressure | Medium | Low | Make QA tasks mandatory in action docs, block release until evidence attached | QA Lead | Open |
