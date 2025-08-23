# Deployment

```pwsh
git add -A
git commit -m "alpha: public signup + submit path"
$REV = (Get-Date).ToString("yyyyMMddHHmmss")
flyctl deploy -a surejan --remote-only --build-arg BUILD_REV=$REV
flyctl ssh console -a surejan -C "python manage.py migrate --noinput"
flyctl ssh console -a surejan -C "python manage.py seed_basics"
```

## Verify

```pwsh
flyctl logs -a surejan | Select-String -Pattern "ERROR|Traceback|favicon|collectstatic"
```
