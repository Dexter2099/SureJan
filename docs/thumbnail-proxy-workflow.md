# Thumbnail Proxy Workflow

## Policy
All video providers render as a **static thumbnail that links out**.  
No iframes, ever.

This ensures thumbnails are consistent, fast, and not subject to hotlink blocking by external providers.

---

## The Four-Step Workflow

### 1. Clean the video link
When a user pastes a video URL, we normalize it into its official “canonical” form.  
Example:  
```

https://rumble.com/v4sac50-time-of-deceit.html?playlist_id=watch-history

```
becomes
```

https://rumble.com/v4sac50-time-of-deceit.html

```
This makes the link stable and predictable.

---

### 2. Ask the video page what its thumbnail is
Every video page publishes metadata tags called **Open Graph (OG) tags**.  
One of these points to the correct thumbnail image.  
SureJan visits the page and reads this tag to discover the original thumbnail URL.

---

### 3. Copy that thumbnail into SureJan
Because providers like Rumble block hotlinking, SureJan downloads the thumbnail image **server-side**, stores it under our own `MEDIA_URL`, and serves it to users from our domain.  
This is also called **image proxying** or **server-side image caching**.

---

### 4. Show it as a simple image that links out
On the site, we always render:
- A **static image** from SureJan’s own storage.  
- Wrapped in a link that opens the original video page in a new tab.  

No embeds, no iframes, no third-party image URLs.

---

## Why This Matters
- **Reliability**: thumbnails always load, even when providers block hotlinking.  
- **Consistency**: one simple rendering path for all providers.  
- **Control**: stored locally, so we can set size, format, and expiration policies.  

---

## Future Work
Once the basic flow is working, we can add:
- Automatic re-fetching on a schedule (to refresh thumbnails).  
- Admin tools to re-fetch or inspect cache state.  
- Logs and counters for success/failure by provider.  
- Negative cache entries to avoid hammering providers on repeated failures.

