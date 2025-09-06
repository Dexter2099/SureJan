# ADR 0001: Governance of Video Previews

**Context**
- Past merges caused drift (legacy CSP keys, mixed fetch paths).
- Feature depends on strict alignment: CSP, flags, outbound client.

**Decision**
- Adopt a single provider map as SSOT for hosts and flags.
- CSP directives computed exclusively from that map.
- All network fetches routed through shared HTTP client.
- CI enforces drift checks (CSP schema, snapshot parity, requests.get ban, env schema).

**Consequences**
- Changes to preview behavior require updating provider map + CSP snapshot in same PR.
- Faster, more predictable releases.
