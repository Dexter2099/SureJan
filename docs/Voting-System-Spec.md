# SureJan V3 — Voting System Spec & Runbook (Immutable Votes: Posts + Comments + Anti‑Astro)

**Goal:** Immutable, auditable voting for **posts and comments** that plays perfectly with **Anti‑AstroTurf**. Users get exactly **one** vote per target, ever. System is **POST‑only**, **race‑safe**, uses a **single writer** (Service Recompute), and ships with health checks for Fly.

---

## Golden rules

1. **Immutability:** Once a user casts **up (+1)** or **down (−1)** on a post/comment, that vote **cannot be changed or revoked**.
2. **Allowed states & transitions:**

   * States per user×target: `0` (no vote yet) → `+1` **or** `−1`.
   * **No other transitions** allowed; repeat attempts return **409 Conflict** (or 200 with no‑op).
3. **Single writer (Service Recompute):** Views call a service that writes the vote row **once** and then sets `score = SUM(value)` for that target. No model signals adjust score.
4. **HTTP posture:** **POST‑only**; `v ∈ {+1, −1}` must be in **POST body**.
5. **UI contract:** Each item has a single score span: `#post-{id}-score` / `#comment-{id}-score`. First successful vote may disable the buttons.
6. **Concurrency:** Apply in `transaction.atomic()` with `select_for_update()` on the user’s vote row.
7. **Prod safety:** Serve **local** HTMX; add CSRF header via static helper; **require Postgres** on Fly; ship a votes consistency check.

---

## Data model

* **Vote** (one table for both targets):

  * `user` FK
  * `post` FK (nullable) **xor** `comment` FK (nullable)
  * `value`: `SmallIntegerField` with choices `−1`, `0`, `+1` (`0` = not yet voted)
  * `created_at`, `updated_at`
* **Constraints:**

  * XOR target (`post` set xor `comment` set)
  * Unique `(user, post)` (partial) and `(user, comment)` (partial)
  * `value` in `{−1, 0, +1}`
* **Optional hardening:** DB trigger to reject `UPDATE Vote.value` when `OLD.value != 0` (immutability at DB layer). Keep service‑level guarding regardless.

---

## Service Recompute (single source of truth)

**Posts** (comments are identical, substituting `comment` for `post`):

```python
# core/services/votes.py
from django.db import transaction
from django.db.models import Sum
from core.models import Vote, Post

class AlreadyVoted(Exception):
    pass

def cast_vote_post_once(user, post: Post, want: int) -> int:
    assert want in (-1, 1)
    with transaction.atomic():
        row, _ = Vote.objects.select_for_update().get_or_create(
            user=user, post=post, defaults={"value": 0}
        )
        if row.value != 0:  # immutable after first non‑zero
            raise AlreadyVoted
        row.value = want
        row.save(update_fields=["value", "updated_at"])  # append‑only semantics

        total = Vote.objects.filter(post=post).aggregate(t=Sum("value"))["t"] or 0
        post.score = total
        post.save(update_fields=["score"])  # single writer

        # Anti‑Astro hook (non‑blocking)
        try:
            from core import anti_astroturf as aa
            aa.on_vote(user=user, target=post, value=want, immutable=True)
        except Exception:
            pass
        return total
```

---

## Views (POST‑only)

```python
# core/views.py
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseConflict
from django.shortcuts import get_object_or_404, render
from core.models import Post, Comment
from core.services.votes import cast_vote_post_once, AlreadyVoted

@login_required
@require_POST
def vote_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    try:
        want = int(request.POST.get("v"))
        assert want in (-1, 1)
    except Exception:
        return HttpResponseBadRequest("Invalid vote")
    try:
        cast_vote_post_once(request.user, post, want)
    except AlreadyVoted:
        return HttpResponse(status=409)  # immutable
    return HttpResponse(f"<span id='post-{post.pk}-score'>{post.score}</span>")
```

*(Add the analogous `vote_comment` that calls `cast_vote_comment_once`.)*

---

## Templates (HTMX; disable on success)

```django
<div class="post-vote" id="post-{{ post.pk }}-vote">
  <button aria-label="Upvote"
          hx-post="{% url 'vote_post' post.pk %}"
          hx-vals='{"v":1}'
          hx-target="#post-{{ post.pk }}-vote"
          hx-swap="outerHTML"
          hx-on::after-request="this.closest('.post-vote').querySelectorAll('button').forEach(b=>b.disabled=true)">▲</button>

  <span id="post-{{ post.pk }}-score">{{ post.score }}</span>

  <button aria-label="Downvote"
          hx-post="{% url 'vote_post' post.pk %}"
          hx-vals='{"v":-1}'
          hx-target="#post-{{ post.pk }}-vote"
          hx-swap="outerHTML"
          hx-on::after-request="this.closest('.post-vote').querySelectorAll('button').forEach(b=>b.disabled=true)">▼</button>
</div>
```

*(Comments mirror the above with `vote_comment` and `#comment-…-score`.)*

---

## HTMX + CSRF + CSP (prod‑safe)

* Serve local `htmx.min.js` and static `htmx-csrf.js` to attach `X-CSRFToken`.
* Keep CSP `script-src 'self'`. No inline scripts required.

---

## Fly deploy basics

* `DATABASE_URL` required in prod; release phase runs `migrate`.
* Optional: management command `votes_consistency` to check/repair `score = SUM(votes)`.

---

## Tests (immutability version)

1. **First vote applies:** 0→+1 or 0→−1 updates `score` correctly.
2. **Second attempt conflicts:** same user targeting same item returns **409** and **does not** change `score`.
3. **POST‑only:** GET → 405.
4. **Consistency:** stored `score == SUM(Vote.value)` for both posts and comments after operations.
5. **Concurrency:** two near‑simultaneous first votes by the **same user** on the same target → exactly one persists; other sees 409 (row lock wins).

---

## Troubleshooting

* **“User can still change vote”** → Ensure the view raises 409 when `row.value != 0`; remove any legacy toggle code.
* **“Buttons remain clickable”** → Add the `hx-on::after-request` disable (above), or server‑side return a non‑interactive block.
* **“Scores drift”** → Run `votes_consistency --fix`.
* **“Nothing happens”** → Check HTMX loaded locally + CSRF header set; confirm no CSP violations.
