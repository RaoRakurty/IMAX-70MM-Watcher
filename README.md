# Dallas Cinemark IMAX 70MM Seat Watcher

## P1 reliability migration — no-billing design

The production design uses a **Cloudflare Workers Free Cron Trigger** to invoke
this public repository's GitHub Action every ten minutes. GitHub performs the
scan, persists state, sends ntfy alerts, and pings Healthchecks.io only after a
fully successful automatic run. No Google Cloud project or billing account is
required. See [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md).

**Deployment and 24-hour live acceptance are still required before calling the
ten-minute cadence fixed.** The earlier Google Cloud implementation remains in
the repository as an optional alternative, documented in `DEPLOYMENT.md`.

Failed, skipped/backoff, incomplete, or unparseable checks now exit nonzero.
Health is sent only after validated observations for both movies and durable
state/notification processing. Manual runs and ntfy tests never count as
scheduler proof. A signed HMAC binds each automatic run to its UTC ten-minute
slot, and stale or forged dispatches fail before scanning.

Personal watcher configured for **Cinemark Dallas XD and IMAX** (TheaterId **207**) and these two targets:

- **The Odyssey IMAX 70MM** — CinemarkMovieId `104867`
- **Dune: Part Three IMAX 70MM** — CinemarkMovieId `109913`

It checks for **new dates/showtimes** and, on a bounded set of recent/frontier showtimes, checks for **preferred center-seat openings**. When it finds something, it publishes a **priority-5 ntfy notification** with the exact seat label and a **BOOK NOW** button that opens the exact Cinemark seat map.

It does **not** log in, hold seats, click checkout, or purchase tickets.

## Why this design

The high-value event is usually a newly released batch. Instead of hammering every seat map all day, the watcher:

1. Baselines the current known showtimes silently on its first run.
2. Rotates through each movie's active 30-day window in five-date batches.
3. Advances that window by 15 days every 15 days, retaining a 15-day overlap.
4. Always inspects a newly discovered showtime once, so the first ntfy alert can tell you the best preferred seat immediately.

GitHub's native cron previously showed multi-hour delays. The replacement uses
Cloudflare only for the trigger and an independent Healthchecks.io heartbeat.
Keep the ntfy topic, heartbeat URL, dispatch token, and HMAC secret private.

## Install on GitHub

1. Upload the contents of this folder, including `.github/workflows/watch.yml`.
2. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Create a secret named `NTFY_TOPIC` and set its value to your ntfy topic.
4. Open **Actions → IMAX 70MM seat watcher → Run workflow** once manually.
5. The first run creates a quiet baseline. It intentionally does **not** notify for everything already available.
6. Follow `FREE_DEPLOYMENT.md` to activate and validate the external ten-minute schedule.

### Test ntfy from your computer

macOS/Linux:

```bash
export NTFY_TOPIC='YOUR_TOPIC'
python3 watcher.py --test-notify
```

That sends a test notification with a link back to the Dallas Cinemark page.

## Seat preference

`config.json` currently uses:

```json
"party_size": 1,
"preferred_rows": ["H", "J", "G", "K"],
"ignored_rows": ["A", "B", "C", "D"],
"center_tolerance": 0.55
```

The watcher calculates the physical center of each row from the seat-map column
positions, so it does not assume that a particular seat number is the center.
Rows G/H/J/K receive prime-seat alerts, E/F can still produce a general newly
opened-seat alert, and A-D never alert.

If you need **two adjacent seats**, change both movie sections to:

```json
"party_size": 2
```

For stricter center seats, lower `center_tolerance` (for example `0.35`). For a wider acceptable zone, raise it toward `1.0`.

## Current discovery strategy

### Odyssey

The first window starts immediately on **Sep 1, 2026** and covers through
**Sep 30, 2026**. On Sep 16 it advances to Sep 16 through Oct 15.

### Dune: Part Three

The first window starts exactly on **Dec 17, 2026** and covers through
**Jan 15, 2027**. On Jan 1 it advances to Jan 1 through Jan 30. Date discovery
checks at most five pages per run, while known showtimes are cached and their
seat maps remain in the existing bounded rotation.

## Notification examples

Every run also prints a timestamped observation for each movie, including
checked-showtime scope and whether ntfy accepted a notification. These lines
appear in the GitHub run's **Summary** and logs, and in the cloud run record's
`status_lines`. The time is the actual observation time in America/Chicago,
not an assumed cron start. Dry runs, unpublished dates, and failed checks are
labelled explicitly. Existing availability does not cause a new notification
unless it meets the configured new-showtime/opening rules.

New batch/showtime:

> **NEW ODYSSEY IMAX 70MM**  
> Fri Sep 18, 7:15 PM — best preferred seat: H14. Tap BOOK NOW.

Cancellation/opening:

> **PRIME SEAT: DUNE**  
> Sat Dec 19, 7:00 PM — H14 just became available in preferred rows. Tap BOOK NOW.

Tapping the ntfy notification or **BOOK NOW** opens Cinemark's exact seat-selection URL for that showtime.

## Local dry run

A dry run fetches Cinemark but does not publish ntfy notifications or change `state.json`:

```bash
python3 watcher.py --dry-run
```

## Tests

The local watcher and unit tests use the Python standard library. The cloud
service additionally requires `pip install -r requirements.txt`.

```bash
python3 -m unittest discover -v
```

## Notes

- This relies on Cinemark's current server-rendered theater/showtime and seat-map HTML. If Cinemark changes the markup, the parser may need updating.
- The code deliberately inserts several seconds between requests and uses a bounded scan window.
- Do not reduce the interval. Ten minutes plus the built-in request pacing is responsive without excessive traffic.
- Keep the ntfy topic in a GitHub Secret rather than committing it to a public repository.
