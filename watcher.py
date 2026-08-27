#!/usr/bin/env python3
"""Cinemark Dallas IMAX 70MM watcher with ntfy alerts.

Efficiency/safety goals:
- keep the GitHub Actions cadence at 10 minutes
- after the first baseline, scan only a few frontier/probe date pages
- cache discovered showtimes in state.json
- rotate through a bounded number of seat maps per run
- require a real selectable seat before sending a "tickets available" alert
- back off automatically on Cinemark 403/429 responses

No login, checkout automation, CAPTCHA bypass, or seat holding is performed.
"""
from __future__ import annotations

import argparse
import email.utils
import html as html_lib
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"
BASE = "https://www.cinemark.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
HREF_RE = re.compile(r'href=["\']([^"\']*TicketSeatMap/\?[^"\']+)["\']', re.I)
BUTTON_RE = re.compile(r"<button\b[^>]*>", re.I)
ATTR_RE = re.compile(r'([:\w-]+)\s*=\s*["\']([^"\']*)["\']', re.I)


class CinemarkBackoff(RuntimeError):
    def __init__(self, message: str, seconds: int):
        super().__init__(message)
        self.seconds = seconds


@dataclass(frozen=True)
class Seat:
    row: str
    number: int
    row_index: int
    col: int
    available: bool

    @property
    def label(self) -> str:
        return f"{self.row}{self.number}"


@dataclass(frozen=True)
class Showtime:
    theater_id: str
    showtime_id: str
    movie_id: str
    iso: str

    @property
    def day(self) -> str:
        return self.iso[:10]

    @property
    def url(self) -> str:
        q = urllib.parse.urlencode(
            {
                "TheaterId": self.theater_id,
                "ShowtimeId": self.showtime_id,
                "CinemarkMovieId": self.movie_id,
                "Showtime": self.iso,
                "CnkAction": "share",
            }
        )
        return f"{BASE}/TicketSeatMap/?{q}"


def log(msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def save_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def parse_day(s: str) -> date:
    return date.fromisoformat(s)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_retry_after(value: str | None, fallback: int) -> int:
    if not value:
        return fallback
    try:
        return max(int(value), 60)
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(int((dt - utcnow()).total_seconds()), 60)
    except Exception:
        return fallback


def fetch(url: str, gap: float, timeout: int) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        },
    )
    # Retry transient 5xx/network failures only. 403/429 trigger a long persisted backoff
    # instead of repeatedly hammering Cinemark from the same Actions runner pool.
    waits = [0, 20, 60]
    last_error: Exception | None = None
    for wait in waits:
        if wait:
            log(f"Transient error; retrying after {wait}s")
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            if gap:
                time.sleep(gap + random.uniform(0, max(gap * 0.20, 0.25)))
            return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                retry = parse_retry_after(exc.headers.get("Retry-After"), 6 * 3600)
                raise CinemarkBackoff(f"Cinemark returned HTTP 429 for {url}", retry) from exc
            if exc.code == 403:
                raise CinemarkBackoff(
                    f"Cinemark returned HTTP 403 for {url}", 12 * 3600
                ) from exc
            if exc.code not in (500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
    raise RuntimeError(f"Failed to fetch after transient retries: {url}: {last_error}")


def showtimes_from_html(page_html: str, target_movie_id: str) -> list[Showtime]:
    found: dict[str, Showtime] = {}
    for raw_href in HREF_RE.findall(page_html):
        href = html_lib.unescape(raw_href)
        parsed = urllib.parse.urlparse(href)
        qs = urllib.parse.parse_qs(parsed.query)
        movie_id = (qs.get("CinemarkMovieId") or [""])[0]
        if movie_id != str(target_movie_id):
            continue
        tid = (qs.get("TheaterId") or [""])[0]
        sid = (qs.get("ShowtimeId") or [""])[0]
        iso = (qs.get("Showtime") or [""])[0]
        if tid and sid and iso:
            found[sid] = Showtime(tid, sid, movie_id, iso)
    return sorted(found.values(), key=lambda s: s.iso)


def seats_from_html(page_html: str) -> list[Seat]:
    seats: list[Seat] = []
    for tag in BUTTON_RE.findall(page_html):
        attrs = {k.lower(): html_lib.unescape(v) for k, v in ATTR_RE.findall(tag)}
        info = attrs.get("info")
        if not info:
            continue
        parts = [p.strip() for p in info.split(",")]
        if len(parts) < 4:
            continue
        row = parts[0].upper()
        try:
            number = int(parts[1])
            row_index = int(parts[2])
            col = int(parts[3])
        except ValueError:
            continue
        cls = attrs.get("class", "").lower()
        available_attr = attrs.get("available", "").lower()
        available = available_attr == "true" or "seatavailable" in cls
        seats.append(Seat(row, number, row_index, col, available))
    return seats


def best_blocks(
    seats: list[Seat], preferred_rows: list[str], party_size: int, center_tolerance: float
) -> list[dict]:
    if party_size < 1:
        return []
    preferred = {row: i for i, row in enumerate(preferred_rows)}
    by_row: dict[str, list[Seat]] = {}
    for seat in seats:
        if seat.row in preferred:
            by_row.setdefault(seat.row, []).append(seat)

    candidates: list[dict] = []
    for row, row_seats in by_row.items():
        all_cols = [s.col for s in row_seats]
        if not all_cols:
            continue
        lo, hi = min(all_cols), max(all_cols)
        center = (lo + hi) / 2.0
        half_span = max((hi - lo) / 2.0, 1.0)
        avail_by_col = {s.col: s for s in row_seats if s.available}
        for start_col in sorted(avail_by_col):
            cols = list(range(start_col, start_col + party_size))
            if not all(c in avail_by_col for c in cols):
                continue
            block = [avail_by_col[c] for c in cols]
            block_center = sum(cols) / len(cols)
            normalized = abs(block_center - center) / half_span
            if normalized > center_tolerance:
                continue
            labels = [s.label for s in block]
            signature = "+".join(labels)
            score = preferred[row] * 100 + normalized * 10
            candidates.append(
                {
                    "signature": signature,
                    "labels": labels,
                    "row": row,
                    "center_distance": round(normalized, 3),
                    "score": round(score, 3),
                }
            )
    candidates.sort(key=lambda c: (c["score"], c["signature"]))
    return candidates


def format_showtime(iso: str, tz: ZoneInfo) -> str:
    dt = datetime.fromisoformat(iso).replace(tzinfo=tz)
    return dt.strftime("%a %b %-d, %-I:%M %p")


def publish_ntfy(topic: str, title: str, message: str, url: str, dry_run: bool) -> None:
    if dry_run:
        log(f"DRY RUN NTFY: {title} | {message} | {url}")
        return
    if not topic:
        raise RuntimeError("NTFY_TOPIC is not set")
    payload = {
        "topic": topic,
        "title": title,
        "message": message,
        "priority": 5,
        "tags": ["ticket", "movie_camera"],
        "click": url,
        "actions": [{"action": "view", "label": "BOOK NOW", "url": url, "clear": True}],
    }
    req = urllib.request.Request(
        os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/") + "/",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "imax-seat-watcher/2.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"ntfy publish failed: HTTP {resp.status}")


def known_future_dates(movie_state: dict, today: date) -> list[date]:
    return sorted(
        {
            parse_day(v["iso"][:10])
            for v in movie_state.get("showtimes", {}).values()
            if parse_day(v["iso"][:10]) >= today
        }
    )


def scan_dates_for_movie(movie_cfg: dict, movie_state: dict, today: date) -> list[date]:
    """Return a small set of date pages worth probing this run.

    First run: full bootstrap range to establish a baseline.
    Steady state with known showtimes: current frontier plus the next few dates.
    Pre-sale/no-known-showtimes: a small configured set of probe dates.
    """
    if not movie_state.get("initialized"):
        start = parse_day(movie_cfg["bootstrap_start"])
        end = parse_day(movie_cfg["bootstrap_end"])
        return list(daterange(start, end))

    known = known_future_dates(movie_state, today)
    max_pages = int(movie_cfg.get("max_date_pages_per_run", 5))
    if known:
        frontier = max(known)
        lookbehind = int(movie_cfg.get("frontier_lookbehind_days", 1))
        lookahead = int(movie_cfg.get("frontier_lookahead_days", 3))
        candidates = [
            frontier + timedelta(days=offset)
            for offset in range(-lookbehind, lookahead + 1)
            if frontier + timedelta(days=offset) >= today
        ]
    else:
        candidates = [
            parse_day(d)
            for d in movie_cfg.get(
                "pre_sale_probe_dates",
                [movie_cfg.get("bootstrap_start", today.isoformat())],
            )
            if parse_day(d) >= today
        ]

    # Optionally rotate extra explicit probe dates without making every run scan them all.
    extras = [
        parse_day(d)
        for d in movie_cfg.get("extra_probe_dates", [])
        if parse_day(d) >= today
    ]
    if extras and len(candidates) < max_pages:
        cursor = int(movie_state.get("date_probe_cursor", 0)) % len(extras)
        need = max_pages - len(candidates)
        rotated = extras[cursor:] + extras[:cursor]
        candidates.extend(rotated[:need])
        movie_state["date_probe_cursor"] = (cursor + need) % len(extras)

    return sorted(set(candidates))[:max_pages]


def discover_movie(movie_cfg: dict, movie_state: dict, theater: dict, polling: dict, today: date):
    gap = float(polling.get("request_gap_seconds", 6))
    timeout = int(polling.get("timeout_seconds", 25))
    first_run = not movie_state.get("initialized")
    new_showtimes: list[Showtime] = []
    dates = scan_dates_for_movie(movie_cfg, movie_state, today)
    log(f"{movie_cfg['short_name']}: scanning {len(dates)} date page(s): " + ", ".join(str(d) for d in dates))
    for d in dates:
        url = f"{BASE}/theatres/{theater['slug']}?showDate={d.isoformat()}"
        page = fetch(url, gap, timeout)
        for st in showtimes_from_html(page, movie_cfg["movie_id"]):
            if st.showtime_id not in movie_state["showtimes"]:
                movie_state["showtimes"][st.showtime_id] = {
                    "theater_id": st.theater_id,
                    "iso": st.iso,
                    "first_seen": datetime.now().isoformat(timespec="seconds"),
                }
                new_showtimes.append(st)
            else:
                movie_state["showtimes"][st.showtime_id]["iso"] = st.iso
    movie_state["initialized"] = True
    return first_run, new_showtimes


def eligible_showtimes(movie_cfg: dict, movie_state: dict, today: date, new_ids: set[str]) -> list[Showtime]:
    seat_cfg = movie_cfg["seat_watch"]
    within_days = int(seat_cfg.get("only_within_days", 120))
    cutoff = today + timedelta(days=within_days)
    future: list[Showtime] = []
    for sid, meta in movie_state.get("showtimes", {}).items():
        day = parse_day(meta["iso"][:10])
        if day < today:
            continue
        if day <= cutoff or sid in new_ids:
            future.append(Showtime(meta["theater_id"], sid, movie_cfg["movie_id"], meta["iso"]))
    return sorted(future, key=lambda s: s.iso)


def select_showtimes_to_poll(movie_cfg: dict, movie_state: dict, today: date, new_ids: set[str]) -> list[Showtime]:
    """Poll every new showtime once, then rotate through a bounded recurring set."""
    seat_cfg = movie_cfg["seat_watch"]
    all_future = eligible_showtimes(movie_cfg, movie_state, today, new_ids)
    new = [st for st in all_future if st.showtime_id in new_ids]
    recurring = [st for st in all_future if st.showtime_id not in new_ids]

    # Focus recurring checks on the latest N distinct dates (the extension frontier).
    keep_dates_n = int(seat_cfg.get("latest_dates_to_poll", 2))
    recurring_dates = sorted({st.day for st in recurring})
    keep_dates = set(recurring_dates[-keep_dates_n:]) if keep_dates_n else set()
    recurring = [st for st in recurring if st.day in keep_dates]

    # Rotate through at most max_seat_maps_per_run so every run stays short.
    max_maps = int(seat_cfg.get("max_seat_maps_per_run", 8))
    remaining = max(max_maps - len(new), 0)
    rotated: list[Showtime] = []
    if recurring and remaining:
        cursor = int(movie_state.get("seat_poll_cursor", 0)) % len(recurring)
        ordered = recurring[cursor:] + recurring[:cursor]
        rotated = ordered[:remaining]
        movie_state["seat_poll_cursor"] = (cursor + len(rotated)) % len(recurring)

    # A flood of brand-new showtimes should still be bounded; the rest will be picked up
    # as recurring on subsequent 10-minute runs.
    selected = (new + rotated)[:max_maps]
    return sorted({st.showtime_id: st for st in selected}.values(), key=lambda s: s.iso)


def poll_seats_and_alert(
    movie_cfg: dict,
    movie_state: dict,
    polling: dict,
    tz: ZoneInfo,
    first_run: bool,
    new_showtimes: list[Showtime],
    topic: str,
    dry_run: bool,
):
    seat_cfg = movie_cfg["seat_watch"]
    discovered_ids = {s.showtime_id for s in new_showtimes}
    new_ids = set() if first_run else discovered_ids
    selected = select_showtimes_to_poll(movie_cfg, movie_state, datetime.now(tz).date(), new_ids)
    log(f"{movie_cfg['short_name']}: polling {len(selected)} seat map(s)")
    gap = float(polling.get("request_gap_seconds", 6))
    timeout = int(polling.get("timeout_seconds", 25))

    for st in selected:
        page = fetch(st.url, gap, timeout)
        seats = seats_from_html(page)
        if not seats:
            log(f"WARN: no seats parsed for {st.showtime_id}; skipping alert")
            continue

        selectable = [s for s in seats if s.available]
        # Critical false-positive guard: a date/showtime listing is not availability.
        # A new-showtime alert requires at least one actual selectable seat.
        verified_inventory = bool(selectable)

        blocks = best_blocks(
            seats,
            [r.upper() for r in seat_cfg["preferred_rows"]],
            int(seat_cfg.get("party_size", 1)),
            float(seat_cfg.get("center_tolerance", 0.55)),
        )
        current = [b["signature"] for b in blocks]
        previous = set(movie_state.setdefault("seat_snapshots", {}).get(st.showtime_id, []))
        is_new_showtime = st.showtime_id in discovered_ids

        if not first_run and is_new_showtime and verified_inventory:
            if blocks:
                best = blocks[0]
                title = f"VERIFIED {movie_cfg['short_name']} IMAX 70MM"
                msg = (
                    f"{format_showtime(st.iso, tz)} — {', '.join(best['labels'])} is available "
                    f"in a preferred area. Tap BOOK NOW."
                )
            else:
                title = f"VERIFIED {movie_cfg['short_name']} IMAX 70MM"
                sample = ", ".join(s.label for s in selectable[:4])
                msg = (
                    f"{format_showtime(st.iso, tz)} — real selectable inventory verified"
                    + (f" ({sample}{'…' if len(selectable) > 4 else ''})" if sample else "")
                    + ". Tap BOOK NOW."
                )
            publish_ntfy(topic, title, msg, st.url, dry_run)
        elif not first_run:
            newly_open = [b for b in blocks if b["signature"] not in previous]
            if newly_open:
                best = newly_open[0]
                title = f"PRIME SEAT: {movie_cfg['short_name']}"
                msg = (
                    f"{format_showtime(st.iso, tz)} — {', '.join(best['labels'])} just became "
                    f"available in preferred rows. Tap BOOK NOW."
                )
                publish_ntfy(topic, title, msg, st.url, dry_run)

        movie_state["seat_snapshots"][st.showtime_id] = current
        movie_state.setdefault("verified_inventory", {})[st.showtime_id] = verified_inventory


def prune(movie_state: dict, today: date) -> None:
    expired = [sid for sid, m in movie_state.get("showtimes", {}).items() if parse_day(m["iso"][:10]) < today]
    for sid in expired:
        movie_state["showtimes"].pop(sid, None)
        movie_state.get("seat_snapshots", {}).pop(sid, None)
        movie_state.get("verified_inventory", {}).pop(sid, None)


def backoff_active(state: dict) -> bool:
    raw = state.get("backoff_until")
    if not raw:
        return False
    try:
        until = datetime.fromisoformat(raw)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
    except ValueError:
        state.pop("backoff_until", None)
        return False
    if utcnow() >= until:
        state.pop("backoff_until", None)
        return False
    log(f"Global Cinemark backoff active until {until.isoformat()}; making zero Cinemark requests")
    return True


def set_backoff(state: dict, exc: CinemarkBackoff) -> None:
    until = utcnow() + timedelta(seconds=exc.seconds)
    state["backoff_until"] = until.isoformat()
    state["backoff_reason"] = str(exc)
    log(f"BACKOFF: {exc}. Pausing Cinemark requests until {until.isoformat()}")


def run_once(config: dict, state: dict, dry_run: bool = False) -> None:
    theater = config["theater"]
    polling = config.get("polling", {})
    tz = ZoneInfo(theater["timezone"])
    today = datetime.now(tz).date()
    topic = os.environ.get("NTFY_TOPIC", "")
    state["version"] = 2
    state.setdefault("movies", {})

    if backoff_active(state):
        return

    for movie_cfg in config["movies"]:
        mid = str(movie_cfg["movie_id"])
        movie_state = state["movies"].setdefault(
            mid,
            {
                "initialized": False,
                "showtimes": {},
                "seat_snapshots": {},
                "verified_inventory": {},
                "seat_poll_cursor": 0,
                "date_probe_cursor": 0,
            },
        )
        # Migration-friendly defaults for an existing v1 state.json.
        movie_state.setdefault("showtimes", {})
        movie_state.setdefault("seat_snapshots", {})
        movie_state.setdefault("verified_inventory", {})
        movie_state.setdefault("seat_poll_cursor", 0)
        movie_state.setdefault("date_probe_cursor", 0)
        prune(movie_state, today)

        try:
            first_run, new_showtimes = discover_movie(movie_cfg, movie_state, theater, polling, today)
            if first_run:
                log(f"{movie_cfg['short_name']}: baseline created; suppressing initial alerts")
            elif new_showtimes:
                log(f"{movie_cfg['short_name']}: discovered {len(new_showtimes)} new showtime(s)")
            poll_seats_and_alert(
                movie_cfg, movie_state, polling, tz, first_run, new_showtimes, topic, dry_run
            )
        except CinemarkBackoff as exc:
            set_backoff(state, exc)
            return
        except Exception as exc:
            # One movie failing should not corrupt prior state or spam ntfy. Log and continue.
            log(f"WARN: {movie_cfg['short_name']} scan failed: {exc}")


def test_notify(config: dict) -> None:
    topic = os.environ.get("NTFY_TOPIC", "")
    url = f"{BASE}/theatres/{config['theater']['slug']}"
    publish_ntfy(
        topic,
        "IMAX watcher test",
        "ntfy is connected. Future alerts require verified selectable Cinemark inventory.",
        url,
        False,
    )
    print("Test notification sent.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not send ntfy alerts")
    parser.add_argument("--test-notify", action="store_true", help="Send an ntfy test and exit")
    args = parser.parse_args()
    config = load_json(CONFIG_PATH)
    state = load_json(STATE_PATH)
    if args.test_notify:
        test_notify(config)
        return 0
    run_once(config, state, dry_run=args.dry_run)
    if not args.dry_run:
        save_json(STATE_PATH, state)
    else:
        log("Dry run complete; state.json left unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise
