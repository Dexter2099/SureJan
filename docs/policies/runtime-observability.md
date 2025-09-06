Make a a persistent "runtime observability contract" so that prod never drifts from spec without you knowing.

---

# Runtime Observability Contract (SureJan v3)

### 1. Response Fingerprinting

Every HTTP response must include:

* `X-SJ-Version` → current app version.
* `X-SJ-Flags` → which providers are enabled (YT/X/Rumble).
* `X-SJ-CSP-Hash` → digest of CSP config.
* `X-SJ-Providers-Hash` → digest of provider map.

**Why:** instantly spot config drift with a single `curl` or browser DevTools check.

---

### 2. Structured Logging

All fetch/render operations log structured events:

* `event=preview.fetch` → `provider`, `source=oembed|og|default`, `status`, `duration_ms`, `cache=hit|miss`.
* `event=render` → `path`, `status`, `duration_ms`, `preview_calls`.

**Why:** identify if pages are slow due to live remote fetches, cache misses, or CSP blocks.

---

### 3. CSP Violation Reporting

* Enable `/_csp-report` endpoint.
* Log `{directive, blocked_uri, document_uri, user_agent}`.
* No external frame origins: `frame-src` is always `'self'`.

**Why:** catch real-world CSP breaks in prod (e.g. twimg host not whitelisted).

---

### 4. Health Probes

* `/healthz` → basic readiness.
* `/healthz/media` → optional: test fetch from known YT/X/Rumble once per day (flag-gated).

**Why:** verifies external providers reachable from prod.

---

### 5. Metrics

Track counters and histograms:

* Preview fetches: successes vs failures per provider/source.
* Cache ratio: hits vs misses.
* Latency: `preview.fetch.duration_ms`, `render.duration_ms`.

**Why:** quantify impact of caching and detect regressions.

---

### 6. No Negative Caching

* Error responses (4xx/5xx) must include `Cache-Control: no-store`.

**Why:** prevents persistent “stale 403” problems that mask fixes.

---

### How this helps

* **Diagnose:** Slow loads? Check logs (`preview.fetch.duration_ms`), or headers (`X-SJ-Flags`, `X-SJ-CSP-Hash`) to confirm drift.
* **Track:** Headers + logs show what code path ran and with which config.
* **Prevent:** CI gates + CSP snapshot parity stop merges from drifting; runtime headers/logs prove prod matches spec.

