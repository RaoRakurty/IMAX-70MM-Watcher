#!/usr/bin/env python3
"""Cinemark Dallas IMAX 70MM watcher with ntfy alerts.

Designed for low-frequency personal monitoring:
- discovers target movie showtimes from Cinemark theater date pages
- detects newly added dates/showtimes
- polls only a bounded set of seat maps for preferred-seat cancellations
- scores central seats and sends a one-tap Cinemark booking link through ntfy

No login, checkout automation, or seat holding is performed.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
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
    attempts = [0, 30, 120]
    last_error: Exception | None = None
    for wait in attempts:
        if wait:
            log(f"Backing off {wait}s before retrying {url}")
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            if gap:
                time.sleep(gap + random.uniform(0, gap * 0.25))
            return body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            code = getattr(exc, "code", None)
            if code is not None and code not in (403, 429, 500, 502, 503, 504):
                raise
    raise RuntimeError(f"Failed to fetch after retries: {url}: {last_error}")


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
    # Cinemark's showtime is theater-local and does not carry an offset.
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
        "actions": [
            {"action": "view", "label": "BOOK NOW", "url": url, "clear": True}
        ],
    }
    req = urllib.request.Request(
        os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/") + "/",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "imax-seat-watcher/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"ntfy publish failed: HTTP {resp.status}")


def scan_dates_for_movie(movie_cfg: dict, movie_state: dict, today: date) -> list[date]:
    always = {parse_day(d) for d in movie_cfg.get("always_scan_dates", [])}
    if not movie_state.get("initialized"):
        start = parse_day(movie_cfg["bootstrap_start"])
        end = parse_day(movie_cfg["bootstrap_end"])
        return sorted(set(daterange(start, end)) | always)

    known_future_dates = sorted(
        {
            parse_day(v["iso"][:10])
            for v in movie_state.get("showtimes", {}).values()
            if parse_day(v["iso"][:10]) >= today
        }
    )
    if known_future_dates:
        frontier = max(known_future_dates)
    else:
        frontier = max(today, parse_day(movie_cfg.get("bootstrap_end", today.isoformat())))
    recent = int(movie_cfg.get("rescan_recent_days", 2))
    future = int(movie_cfg.get("frontier_days", 7))
    start = max(today, frontier - timedelta(days=recent))
    end = frontier + timedelta(days=future)
    return sorted(set(daterange(start, end)) | {d for d in always if d >= today})


def discover_movie(movie_cfg: dict, movie_state: dict, theater: dict, polling: dict, today: date):
    gap = float(polling.get("request_gap_seconds", 5))
    timeout = int(polling.get("timeout_seconds", 30))
    first_run = not movie_state.get("initialized")
    new_showtimes: list[Showtime] = []
    dates = scan_dates_for_movie(movie_cfg, movie_state, today)
    log(f"{movie_cfg['short_name']}: scanning {len(dates)} date pages")
    for d in dates:
        url = f"{BASE}/theatres/{theater['slug']}?showDate={d.isoformat()}"
        try:
            page = fetch(url, gap, timeout)
        except Exception as exc:  # keep the rest of the sweep useful
            log(f"WARN: date scan failed for {d}: {exc}")
            continue
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


def select_showtimes_to_poll(movie_cfg: dict, movie_state: dict, today: date, new_ids: set[str]) -> list[Showtime]:
    seat_cfg = movie_cfg["seat_watch"]
    within_days = int(seat_cfg.get("only_within_days", 35))
    cutoff = today + timedelta(days=within_days)
    future: list[Showtime] = []
    for sid, meta in movie_state.get("showtimes", {}).items():
        day = parse_day(meta["iso"][:10])
        if day < today:
            continue
        # Always inspect newly discovered showtimes once so the first alert can name the best seat.
        if day <= cutoff or sid in new_ids:
            future.append(
                Showtime(meta["theater_id"], sid, movie_cfg["movie_id"], meta["iso"])
            )

    # Bound recurring cancellation polling to the latest N distinct dates.
    recurring = [st for st in future if st.showtime_id not in new_ids and parse_day(st.day) <= cutoff]
    dates = sorted({st.day for st in recurring})
    keep_n = int(seat_cfg.get("latest_dates_to_poll", 3))
    keep_dates = set(dates[-keep_n:]) if keep_n else set()
    selected = [st for st in recurring if st.day in keep_dates]
    selected.extend(st for st in future if st.showtime_id in new_ids)
    # de-dupe by showtime id
    return sorted({st.showtime_id: st for st in selected}.values(), key=lambda x: x.iso)


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
    # On the very first baseline, do not fetch every just-discovered seat map.
    # Only baseline the bounded recurring set. Later runs inspect each truly new showtime once.
    new_ids = set() if first_run else discovered_ids
    selected = select_showtimes_to_poll(movie_cfg, movie_state, datetime.now(tz).date(), new_ids)
    log(f"{movie_cfg['short_name']}: polling {len(selected)} seat maps")
    gap = float(polling.get("request_gap_seconds", 5))
    timeout = int(polling.get("timeout_seconds", 30))

    for st in selected:
        try:
            page = fetch(st.url, gap, timeout)
            seats = seats_from_html(page)
        except Exception as exc:
            log(f"WARN: seat map failed for {st.showtime_id}: {exc}")
            continue
        if not seats:
            log(f"WARN: no seats parsed for {st.showtime_id}; Cinemark markup may have changed")
            continue
        blocks = best_blocks(
            seats,
            [r.upper() for r in seat_cfg["preferred_rows"]],
            int(seat_cfg.get("party_size", 1)),
            float(seat_cfg.get("center_tolerance", 0.55)),
        )
        current = [b["signature"] for b in blocks]
        previous = set(movie_state.setdefault("seat_snapshots", {}).get(st.showtime_id, []))
        current_set = set(current)
        is_new_showtime = st.showtime_id in discovered_ids

        if not first_run and is_new_showtime:
            if blocks:
                best = blocks[0]
                title = f"NEW {movie_cfg['short_name']} IMAX 70MM"
                msg = (
                    f"{format_showtime(st.iso, tz)} — best preferred seat: "
                    f"{', '.join(best['labels'])}. Tap BOOK NOW."
                )
            else:
                title = f"NEW {movie_cfg['short_name']} IMAX 70MM"
                msg = f"{format_showtime(st.iso, tz)} — new showtime posted. Tap to inspect seats."
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


def prune(movie_state: dict, today: date) -> None:
    expired = [sid for sid, m in movie_state.get("showtimes", {}).items() if parse_day(m["iso"][:10]) < today]
    for sid in expired:
        movie_state["showtimes"].pop(sid, None)
        movie_state.get("seat_snapshots", {}).pop(sid, None)


def run_once(config: dict, state: dict, dry_run: bool = False) -> None:
    theater = config["theater"]
    polling = config.get("polling", {})
    tz = ZoneInfo(theater["timezone"])
    today = datetime.now(tz).date()
    topic = os.environ.get("NTFY_TOPIC", "")
    state.setdefault("version", 1)
    state.setdefault("movies", {})

    for movie_cfg in config["movies"]:
        mid = str(movie_cfg["movie_id"])
        movie_state = state["movies"].setdefault(
            mid, {"initialized": False, "showtimes": {}, "seat_snapshots": {}}
        )
        prune(movie_state, today)
        first_run, new_showtimes = discover_movie(movie_cfg, movie_state, theater, polling, today)
        if first_run:
            log(f"{movie_cfg['short_name']}: baseline created; suppressing initial alerts")
        elif new_showtimes:
            log(f"{movie_cfg['short_name']}: discovered {len(new_showtimes)} new showtime(s)")
        poll_seats_and_alert(
            movie_cfg, movie_state, polling, tz, first_run, new_showtimes, topic, dry_run
        )


def test_notify(config: dict) -> None:
    topic = os.environ.get("NTFY_TOPIC", "")
    url = f"{BASE}/theatres/{config['theater']['slug']}"
    publish_ntfy(
        topic,
        "IMAX watcher test",
        "ntfy is connected. Future alerts will include exact preferred seats and a BOOK NOW button.",
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
