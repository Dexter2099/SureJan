# Deployment

```bash
git add -A
git commit -m "alpha: public signup + header auth + submit CTA + seeds"
# PowerShell
$REV = (Get-Date).ToString("yyyyMMddHHmmss")
flyctl deploy -a surejan --remote-only --build-arg BUILD_REV=$REV
flyctl ssh console -a surejan -C "python manage.py migrate --noinput"
flyctl ssh console -a surejan -C "python manage.py seed_basics"
flyctl logs -a surejan | Select-String -Pattern "ERROR|Traceback|favicon|collectstatic"
```

## Smoke checklist

* `/accounts/signup/` → create user, header shows username.
* `/r/news/` → "Submit" visible (logged-in), post appears in feed.
* Vote/comment work; anonymous users get redirected to login for writes.
