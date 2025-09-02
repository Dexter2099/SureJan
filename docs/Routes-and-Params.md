Change control: If templates affecting this surface change, update this file in the same PR.

Route | Params | Defaults | Notes
---|---|---|---
/ | sort=hot|new|top, t=24h|7d|all | sort=hot, t unset | Home feed; time filter only when sort=top
/r/<slug> | sort=hot|new|top, t=24h|7d|all | sort=hot, t unset | Time filter only when sort=top
/p/<id> | — | — | Post detail; 404 allowed if missing
/submit | — | — | Submit post
/mod/astro | — | — | Minimal mod list (reports/high-score)
/methods | — | — | AstroShield v1 + safety write-up
/posts | — | — | AstroShield flagged posts
