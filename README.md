# Dallas Cinemark IMAX 70MM Seat Watcher

Personal watcher configured for **Cinemark Dallas XD and IMAX** (TheaterId **207**) and these two targets:

- **The Odyssey IMAX 70MM** — CinemarkMovieId `104867`
- **Dune: Part Three IMAX 70MM** — CinemarkMovieId `109913`

It checks for **new dates/showtimes** and, on a bounded set of recent/frontier showtimes, checks for **preferred center-seat openings**. When it finds something, it publishes a **priority-5 ntfy notification** with the exact seat label and a **BOOK NOW** button that opens the exact Cinemark seat map.

It does **not** log in, hold seats, click checkout, or purchase tickets.

## Why this design

The high-value event is usually a newly released batch. Instead of hammering every seat map all day, the watcher:

1. Baselines the current known showtimes silently on its first run.
2. Rechecks only the newest date frontier plus a few strategic dates where extra screenings are likely to be added.
3. Polls seat maps only for the latest few dates when the movie is within the configured time horizon.
4. Always inspects a newly discovered showtime once, so the first ntfy alert can tell you the best preferred seat immediately.

The default GitHub Action runs every **10 minutes**. GitHub scheduled jobs can occasionally start late, so this is not a hard real-time guarantee. A public repository is the simplest way to avoid burning through private-repository Actions minutes; keep the ntfy topic in a repository Secret.

## Install on GitHub

1. Create a new GitHub repository (private is fine) and upload the contents of this folder, including `.github/workflows/watch.yml`.
2. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Create a secret named `NTFY_TOPIC` and set its value to your ntfy topic.
4. Open **Actions → IMAX 70MM seat watcher → Run workflow** once manually.
5. The first run creates a quiet baseline. It intentionally does **not** notify for everything already available.
6. Run it manually a second time if you want to verify normal operation, or wait for the 10-minute schedule.

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
"preferred_rows": ["H", "J", "G", "K", "F", "E"],
"center_tolerance": 0.55
```

The watcher calculates the physical center of each row from the seat-map column positions, so it does not assume that a particular seat number is the center. The row list is ordered best-first, with H/J favored before nearby rows.

If you need **two adjacent seats**, change both movie sections to:

```json
"party_size": 2
```

For stricter center seats, lower `center_tolerance` (for example `0.35`). For a wider acceptable zone, raise it toward `1.0`.

## Current discovery strategy

### Odyssey

The initial baseline covers **Aug 27 through Sep 16, 2026**. After that, the watcher follows the newest known date and looks **7 days beyond it**, while also rescanning Sep 14–16 to catch added showtimes on the current final dates.

### Dune: Part Three

The initial baseline covers **Dec 14, 2026 through Jan 3, 2027**. It always rescans opening weekend (Dec 17–20) plus Dec 25, because extra 70MM screenings can be added to already-on-sale dates.

## Notification examples

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

No third-party Python packages are required.

```bash
python3 -m unittest -v test_watcher.py
```

## Notes

- This relies on Cinemark's current server-rendered theater/showtime and seat-map HTML. If Cinemark changes the markup, the parser may need updating.
- The code deliberately inserts several seconds between requests and uses a bounded scan window.
- Do not reduce the interval aggressively. A 10-minute GitHub schedule plus the built-in request pacing is already much more responsive than manually checking while avoiding excessive traffic.
- Keep the ntfy topic in a GitHub Secret rather than committing it to a public repository.
