# Reading Logs (Fly)

Search for:
- `DisallowedHost` → host/Cloudflare mismatch
- `TemplateDoesNotExist: errors/500.html` → missing error template
- `django.db.utils` at startup → migration loop/schema drift
- `ImportError` in core/posts/comments → refactor path issues

Commands:

```
fly logs -a surejan --recent 200
fly status
```

