# Route Contracts (stable external behavior)

| Path | Method | View (module.fn) | Template | Auth | Notes |
|------|--------|------------------|----------|------|-------|
| `/` | GET | posts.views.feed | posts/feed.html | Opt | Hot/New/Top |
| `/c/<slug>/` | GET | communities.views.detail | communities/detail.html | Opt | Community feed |
| `/c/<slug>/submit` | GET | posts.views.submit_get | posts/submit.html | Req | Show form |
| `/c/<slug>/submit` | POST | posts.views.submit_post | (302 redirect) | Req | Create Post |
| `/p/<id-or-slug>/` | GET | posts.views.detail | posts/detail.html | Opt | Astro-chip renders |
| `/p/<id-or-slug>/comment` | POST | comments.views.create | (fragment/redirect) | Req | HTMX/standard |
| `/vote/post/<id>` | POST | votes.views.vote_post | (JSON/fragment/204) | Req | value ∈ {+1,-1,0} |
| `/healthz` | GET | health.views.ok | (plain 200) | No | Used by Fly |
| errors 400/403/404/413/429/500 | ANY | config.urls.handlers | templates/errors/*.html | — | Must exist |

