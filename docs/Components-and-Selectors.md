Change control: If templates affecting this surface change, update this file in the same PR.

component | purpose | root_selector | required_testid | variants
post-card | displays a post row | .post-card | data-testid="post-card" | post-card--locked
header-bar | global header | header.header-bar | data-testid="header-bar" | header--compact
sort-tabs | sort control | #sort-tabs | — | —
sidebar-cta | submit CTA | .sidebar-cta | data-testid="sidebar-submit" | —
anti-astro | link to /methods | a[href="/methods"] | data-testid="sidebar-astro" | —
empty-state | empty feed/community | .empty-state | data-testid="empty-state" | empty--posts
submit-form | create post | form | data-testid="submit-form" | —

