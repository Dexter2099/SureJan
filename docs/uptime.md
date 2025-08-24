# Uptime monitoring

The `/healthz` endpoint performs basic checks for the database and cache.
Configure an external service such as UptimeRobot to poll it and alert if
it fails.

## Example (UptimeRobot)

1. Create a new **HTTPS** monitor with the URL
   `https://<APP>.fly.dev/healthz` (replace `<APP>` with the Fly app name).
2. Choose an interval (e.g. 5 minutes).
3. Select the notification channels (email, Slack, etc.).

Fly's internal health checks are defined in `fly.toml`, but an external
monitor provides visibility if the app becomes unreachable.
