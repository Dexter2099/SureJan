# Migrations Ledger (authoritative history)

| App  | Number | Summary                               | Risk | Prod Applied? | Notes |
|------|--------|---------------------------------------|------|---------------|-------|
| core | 0031b  | Add slug field                        | High | ?             | Must precede data backfill |
| core | 0031a  | Populate slugs                        | Med  | ?             | Runs after 0031b |
| core | 0032   | Drop legacy image fields (if present) | High | ?             | Template reliance risk |
| ...  | ...    | ...                                   | ...  | ...           | ...   |

> Update on every migration PR. Never delete a migration without noting the replacement/alias plan here.

