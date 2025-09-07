# Thumbnail Diagnosis Checklist

Use this checklist when thumbnails fail to appear or update.

1. **Verify Fly.io app and image parity**
   - Run `fly status` and ensure you're targeting the correct app (`surejan.fly.dev` vs `surejan.app`).
   - Confirm the deployed image matches the one you expect to run.

2. **Confirm secrets and config flags**
   - `fly secrets list` should include `ALLOWED_HOSTS`, `MEDIA_URL`, `IMAGE_PROXY_ENABLED`, and `EXTERNAL_HTTP_UA` with correct values.

3. **Inspect generated \<img> URLs**
   - Use browser dev tools to check if thumbnails load from the proxy under your `MEDIA_URL` or directly from external hosts.

4. **Tail logs during post creation**
   - Run `fly logs` while creating a post and watch for `og_found` and `cache_remote_image` entries.
   - Missing events often mean the proxy path didn't execute.

5. **Clear caches or redeploy**
   - If stale responses persist after fixes, clear relevant caches or redeploy the app.

See related docs: [Thumbnail Proxy Workflow](thumbnail-proxy-workflow.md) and [Rumble thumbnail caching](rumble-thumbnail-cache.md).
