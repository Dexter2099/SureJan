Change control: If templates affecting this surface change, update this file in the same PR.

Route | Params | Defaults | Notes
/ | sort, t | sort=hot; if sort=top and t unset → t=all | Home feed
/r/<slug> | sort, t | same as / | Community feed
/r/<community>/comments/<pk>/<slug> | — | — | Post detail (nested under community)
/p/<id> | — | — | Post detail (legacy id-only, 404 allowed if missing)
/submit | — | — | Submit post (GET/POST)
/mod/astro | — | — | Mod list (red items first)
/methods | — | — | AstroShield v1 + safety write-up

Allowed t (Top only): `24h | 7d | all`

