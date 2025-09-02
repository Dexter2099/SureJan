Change control: If templates affecting this surface change, update this file in the same PR.

Route | Params | Defaults | Notes
/ | sort, t | sort=hot; if sort=top and t unset → t=all | Home feed
/r/<slug> | sort, t | same as / | Community feed
/p/<id> | — | — | Post detail
/submit | — | — | Submit post
/mod/astro | — | — | Mod list
/methods | — | — | Methods page
Allowed t: 24h|7d|all (only valid with sort=top)
