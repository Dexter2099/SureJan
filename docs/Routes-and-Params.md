Change control: If templates affecting this surface change, update this file in the same PR.

Route | Params | Defaults | Notes
---|---|---|---
/ | sort, t | sort=hot, t=24h | Front page feed
/r/<slug> | sort=hot|new|top, t=24h|7d|30d|all | sort=hot, t=24h | Community feed
/p/<id> | — | — | Post detail; 404 allowed if not found
/submit | — | — | GET form, POST create
/methods | — | — | Static info page
