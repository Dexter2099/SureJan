# Flow — Vote on Post/Comment

- Entry: `POST /vote/post/<id>` (or comment variant), Auth required.
- Service: `cast_vote(user, target, value)` upserts unique (user,target).
- Net score = sum(value); repeat same vote → idempotent (no change).

