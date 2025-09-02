Change control: If testing policy changes, update this file in the same PR.

# Testing Policy (V2)
- We **do not use UI smoke tests** (route/selector/logo/empty-state smokes).
- CI may run `pytest` with **0 tests** and still pass.
- Verification for UI flows is **manual** or via targeted unit/integration tests added case-by-case.
- Future E2E (Playwright/Cypress) can be added post-V2 if needed.
