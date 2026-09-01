# P1 no-billing deployment

This is the preferred deployment. It uses three free services:

- Cloudflare Workers Free: one Cron Trigger at `*/10 * * * *` UTC.
- GitHub Actions: standard hosted runners are free for this public repository.
- Healthchecks.io Hobbyist: one check with a 10-minute period and 5-minute grace.

The Cloudflare Worker does not scrape Cinemark or receive the ntfy topic. It
only sends an authenticated workflow dispatch. The GitHub workflow verifies a
shared HMAC, rejects stale/off-grid dispatches, runs the watcher, commits state,
and sends the success heartbeat. A manual workflow or notification test cannot
send that heartbeat.

## One-time setup

1. Merge this implementation into `main`. Native GitHub cron is intentionally
   removed from `watch.yml` so it cannot overlap the external trigger.

2. In GitHub, create a **fine-grained personal access token** restricted to:

   - Repository: `RaoRakurty/IMAX-70MM-Watcher` only
   - Repository permission: **Actions — Read and write**
   - Short expiration with a reminder to rotate it

   Do not grant Contents write. The workflow's own `GITHUB_TOKEN` persists
   `state.json`; the Cloudflare token can only dispatch/manage Actions.

3. Generate one random HMAC secret locally. Do not paste it into chat or commit
   it:

   ```bash
   openssl rand -hex 32
   ```

   Add that same value as:

   - GitHub repository secret `DISPATCH_HMAC_SECRET`
   - Cloudflare Worker secret `DISPATCH_HMAC_SECRET`

4. Create a free Healthchecks.io check with period **10 minutes**, grace
   **5 minutes**, timezone UTC, and verified email alerting. Add its ping URL as
   GitHub repository secret `HC_PING_URL`. Keep the existing `NTFY_TOPIC`
   secret. Never store these values in workflow inputs or repository files.

5. Create a Cloudflare Free account. From the repository root, authenticate and
   deploy the Worker:

   ```bash
   npx wrangler login
   npx wrangler secret put GITHUB_ACTIONS_TOKEN --config free_scheduler/wrangler.toml
   npx wrangler secret put DISPATCH_HMAC_SECRET --config free_scheduler/wrangler.toml
   npx wrangler deploy --config free_scheduler/wrangler.toml
   ```

   Enter secret values only into Wrangler's secure prompts. The checked-in
   `wrangler.toml` installs the UTC ten-minute Cron Trigger.

## Proof and acceptance

Wait for the next natural `:00`, `:10`, `:20`, `:30`, `:40`, or `:50` UTC slot.
Do not click **Run workflow** for cadence proof. The automatic run Summary must
contain **Signed automatic run**, its scheduled slot, successful scan and state
persistence, plus timestamped movie observations such as:

```text
10:40 AM CDT — ODYSSEY — tickets unavailable — no notification sent
10:50 AM CDT — ODYSSEY — tickets unavailable — no notification sent
11:00 AM CDT — ODYSSEY — tickets available — notification sent
```

Those lines are illustrative only. Production output always uses actual scan
times, ticket scope, seat counts, and ntfy acknowledgements.

P1 stays open until all of the following pass:

1. A manual ntfy test arrives on the phone.
2. Three consecutive natural signed slots complete successfully, ten minutes
   apart, with Healthchecks Up.
3. Temporarily disable the Cloudflare Cron Trigger and confirm the independent
   missed-run email after the 10+5-minute threshold; re-enable it and confirm
   recovery. Exclude this drill from cadence measurement.
4. Observe a clean 24 hours: 144 distinct signed slots, no slot missing, no
   dispatch more than 5 minutes late, and no successful-completion gap over
   15 minutes.

Cloudflare acceptance of a GitHub dispatch proves only that the workflow was
queued. Healthchecks proves the workflow completed successfully. GitHub run
Summaries provide the per-movie ticket and notification evidence.

## Rollback

Disable the Cron Trigger in Cloudflare or set `crons = []` in `wrangler.toml`
and redeploy. Wait for any active GitHub run to finish before changing the
workflow. Do not enable both this trigger and the old GitHub schedule.
