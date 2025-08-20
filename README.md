# SureJan

## Critical User Stories

1. **Browse the front page & communities (old-reddit layout)**
   - As a visitor, I can browse the Home feed or a Community feed and switch tabs: best, hot, new, rising, controversial, top.
   - **Acceptance criteria**
     - Subreddit bar across the top lists at least News and Brisbane.
     - Each feed shows post title, score, community, author, age, comment count; pagination (25 per page).
     - Sort tabs re-query the feed correctly; selected tab is highlighted.
     - Not logged in users can read everything but cannot vote/post/comment.
2. **Sign up / log in and see my username + points**
   - As a user, I can create an account, log in/out, and see my username top-right with points (karma-like).
   - **Acceptance criteria**
     - Sign-up: unique username + password.
     - Log in/out rounds trip correctly; username displays top-right.
     - Points displayed (sum of post/comment scores authored by the user; negative points have no consequence yet).
3. **Create posts and discuss (threaded comments)**
   - As a logged-in user, I can create link or text posts in a community and comment in a threaded view on the post page.
   - **Acceptance criteria**
     - "Submit" supports URL or text; community must be selectable/valid.
     - Post page shows OP, body (basic Markdown), and a nested comment tree.
     - Compose comment box + reply to a specific comment; timestamps show "x minutes ago".
     - Basic formatting: links, code, bold/italic (no images needed for MVP).
4. **Vote on posts & comments (instant feedback)**
   - As a logged-in user, I can upvote/downvote posts and comments and see the score update immediately.
   - **Acceptance criteria**
     - One vote per user per item; clicking the same arrow again removes my vote.
     - Scores update without full page reload (HTMX/Ajax).
     - My own points update on next page load (or after a short refresh).
     - Simple rate-limit: max N votes/minute (to prevent spam).
5. **Profiles & history**
   - As a user, I can click my username to view my profile: posts, comments, and points.
   - **Acceptance criteria**
     - Profile has tabs: Overview, Posts, Comments.
     - Each list paginated; items link back to the original thread/community.
     - Anyone can view anyone’s profile (public by default).

**Admin-only note for MVP setup:** seed two communities (News, Brisbane) via a management command or admin page.

