Change control: If templates affecting this surface change, update this file in the same PR.

# Routes and Params

Authoritative map of core routes and their accepted parameters.

| Route | Path params | Query params | Description |
|-------|-------------|--------------|-------------|
| `/` | – | `tab`, `range`, `page` | Home feed |
| `/r/<slug>/` | `slug` | `tab`, `range`, `page` | Community feed |
| `/r/<community>/comments/<pk>/<slug>/` | `community`, `pk`, `slug` | – | Post detail + comments |
| `/p/<pk>/` | `pk` | – | Post detail by id |
| `/submit/` | – | – | Submit post form |
| `/mod/astro/` | – | – | Astro alerts for moderators |
| `/methods/` | – | – | Transparency methods |
| `/transparency/posts` | – | `page`, `sort` | Flagged posts list |
| `/mission/` | – | – | Mission page |
| `/anti-astroturf/` | – | – | Anti-astroturf info |
