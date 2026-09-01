#!/usr/bin/env python3
"""Cinemark Dallas IMAX 70MM watcher with ntfy alerts.

Efficiency/safety goals:
- expose validated scan results to a separately monitored 10-minute scheduler
- after the first baseline, scan only a few frontier/probe date pages
- cache discovered showtimes in state.json
- rotate through a bounded number of seat maps per run
- require a real selectable seat before sending a "tickets available" alert
- back off automatically on Cinemark 403/429 responses

No login, checkout automation, CAPTCHA bypass, or seat holding is performed.
"""
from __future__ import annotations

import argparse
import copy
import contextvars
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
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from html.parser import HTMLParser
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
DEADLINE = contextvars.ContextVar("scan_deadline", default=None)


class ScanError(RuntimeError):
    """A response cannot establish a valid positive or negative observation."""


def remaining_timeout(requested: float) -> float:
    deadline = DEADLINE.get()
    if deadline is None:
        return requested
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ScanError("Scan time budget exceeded")
    return min(requested, remaining)


def paced_sleep(seconds: float) -> None:
    if seconds >= remaining_timeout(seconds + 1):
        raise ScanError("Insufficient scan time budget for retry/pacing")
    time.sleep(seconds)


class PageFacts(HTMLParser):
    """Read public server-rendered markup; never execute scripts or hold seats."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict]] = []
        self.title = ""
        self.in_title = False
        self.listing_depth = 0
        self.listing_text = ""
        self.script_depth = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if dict(attrs).get("id") == "listOfMoviesOrTheaters":
            self.listing_depth = 1
        elif self.listing_depth and tag not in ("input", "img", "br", "hr", "meta", "link", "source", "wbr", "area", "base", "embed", "param", "track", "col"):
            self.listing_depth += 1
        if tag in ("script", "style"):
            self.script_depth += 1
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.listing_depth:
            self.listing_depth -= 1
        if tag in ("script", "style"):
            self.script_depth = max(0, self.script_depth-1)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.listing_depth and not self.script_depth:
            self.listing_text += data + " "


def validate_discovery(page: str, theater: dict, requested_day: date) -> str:
    """Return selected_date or date_not_published, never silently accept fallback.

    Cinemark can return today's listings for a future date outside its advertised
    calendar. That establishes only that the requested date is not published in
    this theater calendar, NOT that a seat map was checked or is sold out.
    """
    facts = PageFacts(page)
    if theater["name"].casefold() not in facts.title.casefold():
        raise ScanError("Theater page identity missing (blocked or changed markup)")
    calendars = [a for _, a in facts.tags if a.get("data-test") == "ShowdatesList"]
    offered = {a["data-datevalue"] for _, a in facts.tags if a.get("data-datevalue")}
    if len(calendars) != 1 or not offered:
        raise ScanError("Theater calendar missing or ambiguous")
    raw = calendars[0].get("data-showdates", "").split(" ")[0]
    try:
        selected = datetime.strptime(raw, "%m/%d/%Y").date().isoformat()
        for day in offered:
            parse_day(day)
    except ValueError as exc:
        raise ScanError("Unrecognized theater calendar dates") from exc
    if selected not in offered:
        raise ScanError("Selected date is not in the advertised calendar")
    links = []
    for tag, attrs in facts.tags:
        href = attrs.get("href", "")
        if tag != "a" or "/ticketseatmap/" not in href.lower():
            continue
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if (qs.get("TheaterId") or [""])[0] != str(theater["id"]):
            raise ScanError("Showtime link belongs to a different theater")
        iso = (qs.get("Showtime") or [""])[0]
        try:
            parsed_day = datetime.fromisoformat(iso).date().isoformat()
        except ValueError as exc:
            raise ScanError("Malformed showtime date") from exc
        if parsed_day != selected:
            raise ScanError("Showtime links do not match selected calendar date")
        links.append(href)
    # Require a recognizable listings container even for a legitimate empty day.
    if not any(a.get("id") == "listOfMoviesOrTheaters" for _, a in facts.tags):
        raise ScanError("Theater listings container missing")
    wanted = requested_day.isoformat()
    if selected != wanted and wanted not in offered:
        return "date_not_published"
    if not links and not re.search(r"\b(no showtimes available|there are no showtimes)\b", facts.listing_text, re.I):
        raise ScanError("Empty listings without an explicit no-showtimes response")
    if selected == wanted:
        return "selected_date"
    raise ScanError("Server did not return the requested advertised date")


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
            paced_sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=remaining_timeout(timeout)) as resp:
                if urllib.parse.urlparse(resp.url).hostname not in ("www.cinemark.com", "cinemark.com"):
                    raise ScanError("Unexpected redirect outside Cinemark")
                raw = resp.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ScanError("Unexpectedly large Cinemark response")
                body = raw.decode("utf-8", errors="replace")
            if gap:
                paced_sleep(gap + random.uniform(0, max(gap * 0.20, 0.25)))
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
        # Explicit unavailability/disabled must win over a contradictory CSS class.
        disabled = bool(re.search(r"\bdisabled(?:\s|=|>)", tag, re.I))
        available = not disabled and available_attr != "false" and (
            available_attr == "true" or "seatavailable" in cls.split()
        )
        seats.append(Seat(row, number, row_index, col, available))
    return seats


def validated_seats(page: str, showtime: Showtime) -> list[Seat]:
    facts = PageFacts(page)
    forms = [a for tag, a in facts.tags if tag == "form" and a.get("id") == "FormSeatMap"]
    if len(forms) != 1 or "reserve your seats" not in facts.title.lower():
        raise ScanError("Seat-map identity missing (blocked or changed markup)")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(forms[0].get("action", "")).query)
    expected = {"TheaterId": showtime.theater_id, "ShowtimeId": showtime.showtime_id,
                "CinemarkMovieId": showtime.movie_id, "Showtime": showtime.iso}
    if any(qs.get(key) != [str(value)] for key, value in expected.items()):
        raise ScanError("Seat-map form belongs to a different showtime/movie/theater")
    buttons = [a for tag, a in facts.tags if tag == "button" and a.get("info")]
    for attrs in buttons:
        parts = attrs["info"].split(",")
        if len(parts) < 5 or parts[4].strip() != showtime.showtime_id:
            raise ScanError("Seat belongs to another showtime or has changed markup")
        if attrs.get("available", "").lower() not in ("true", "false"):
            raise ScanError("Seat availability field missing")
    seats = seats_from_html(page)
    if not seats or len(seats) != len(buttons) or len({s.label for s in seats}) != len(seats):
        raise ScanError("Missing, malformed, or duplicate seats; not a sold-out result")
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


def publish_ntfy(topic: str, title: str, message: str, url: str, dry_run: bool, **_evidence) -> None:
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
    with urllib.request.urlopen(req, timeout=remaining_timeout(20)) as resp:
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
        start = max(today, parse_day(movie_state.get("bootstrap_next_date", movie_cfg["bootstrap_start"])))
        end = parse_day(movie_cfg["bootstrap_end"])
        return list(daterange(start, end))[:int(movie_cfg.get("max_date_pages_per_run", 5))]

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
    if not dates:
        raise ScanError("No future probe dates configured; update the movie date range")
    log(f"{movie_cfg['short_name']}: scanning {len(dates)} date page(s): " + ", ".join(str(d) for d in dates))
    observations = []
    for d in dates:
        url = f"{BASE}/theatres/{theater['slug']}?showDate={d.isoformat()}"
        page = fetch(url, gap, timeout)
        observation = validate_discovery(page, theater, d)
        observations.append({"date": d.isoformat(), "result": observation})
        if observation == "date_not_published":
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
    if first_run:
        movie_state["bootstrap_next_date"] = (dates[-1] + timedelta(days=1)).isoformat()
        movie_state["initialized"] = dates[-1] >= parse_day(movie_cfg["bootstrap_end"])
    movie_state["date_observations"] = observations
    return first_run, new_showtimes


def seed_configured_showtimes(movie_cfg: dict, movie_state: dict, theater: dict) -> None:
    """Keep user-verified direct seat-map showtimes in the normal polling rotation."""
    for seed in movie_cfg.get("seed_showtimes", []):
        sid = str(seed.get("showtime_id", ""))
        iso = str(seed.get("iso", ""))
        if not sid.isdigit():
            raise ScanError("Configured seed showtime ID is invalid")
        try:
            datetime.fromisoformat(iso)
        except ValueError as exc:
            raise ScanError("Configured seed showtime timestamp is invalid") from exc
        existing = movie_state["showtimes"].setdefault(
            sid,
            {
                "theater_id": str(theater["id"]),
                "iso": iso,
                "first_seen": datetime.now().isoformat(timespec="seconds"),
                "source": "configured_direct_seat_map",
            },
        )
        if existing.get("theater_id") != str(theater["id"]):
            raise ScanError("Configured seed showtime belongs to another theater")
        existing["iso"] = iso


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
    urgent = set(movie_state.get("pending_notification_checks", []))
    all_future = eligible_showtimes(movie_cfg, movie_state, today, new_ids | urgent)
    pending = set(movie_state.get("pending_seat_checks", [])) | new_ids | urgent
    new = [st for st in all_future if st.showtime_id in pending]
    recurring = [st for st in all_future if st.showtime_id not in pending]

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
    notify=publish_ntfy,
):
    seat_cfg = movie_cfg["seat_watch"]
    discovered_ids = {s.showtime_id for s in new_showtimes} | set(movie_state.get("pending_seat_checks", []))
    new_ids = set() if first_run else discovered_ids
    if not first_run:
        movie_state["pending_seat_checks"] = sorted(discovered_ids)
    selected = select_showtimes_to_poll(movie_cfg, movie_state, datetime.now(tz).date(), new_ids)
    log(f"{movie_cfg['short_name']}: polling {len(selected)} seat map(s)")
    gap = float(polling.get("request_gap_seconds", 6))
    timeout = int(polling.get("timeout_seconds", 25))
    available_count = 0
    alertable_count = 0
    preferred_count = 0

    for st in selected:
        page = fetch(st.url, gap, timeout)
        seats = validated_seats(page, st)

        selectable = [s for s in seats if s.available]
        available_count += len(selectable)
        ignored_rows = {str(row).upper() for row in seat_cfg.get("ignored_rows", [])}
        alertable = [s for s in selectable if s.row.upper() not in ignored_rows]
        alertable_count += len(alertable)
        # A listing is never availability, and explicitly ignored rows never alert.
        verified_inventory = bool(alertable)

        blocks = best_blocks(
            seats,
            [r.upper() for r in seat_cfg["preferred_rows"]],
            int(seat_cfg.get("party_size", 1)),
            float(seat_cfg.get("center_tolerance", 0.55)),
        )
        current = [b["signature"] for b in blocks]
        preferred_count += len(blocks)
        previous = set(movie_state.setdefault("seat_snapshots", {}).get(st.showtime_id, []))
        selectable_snapshots = movie_state.setdefault("selectable_snapshots", {})
        had_selectable_snapshot = st.showtime_id in selectable_snapshots
        previous_selectable = set(selectable_snapshots.get(st.showtime_id, []))
        current_selectable = sorted(s.label for s in alertable)
        was_verified = bool(movie_state.setdefault("verified_inventory", {}).get(st.showtime_id, False))
        # Existing verified inventory predates per-seat snapshots. Baseline it once
        # so a state migration cannot mislabel every old seat as newly opened.
        newly_selectable = [] if was_verified and not had_selectable_snapshot else [
            s for s in alertable if s.label not in previous_selectable
        ]
        is_new_showtime = st.showtime_id in discovered_ids

        if not first_run and verified_inventory and (is_new_showtime or not was_verified):
            if blocks:
                best = blocks[0]
                title = f"VERIFIED {movie_cfg['short_name']} IMAX 70MM"
                msg = (
                    f"{format_showtime(st.iso, tz)} — {', '.join(best['labels'])} is available "
                    f"in a preferred area. Tap BOOK NOW."
                )
            else:
                title = f"VERIFIED {movie_cfg['short_name']} IMAX 70MM"
                sample = ", ".join(s.label for s in alertable[:4])
                msg = (
                    f"{format_showtime(st.iso, tz)} — real selectable inventory verified"
                    + (f" ({sample}{'…' if len(alertable) > 4 else ''})" if sample else "")
                    + ". Tap BOOK NOW."
                )
            notify(topic, title, msg, st.url, dry_run, showtime_id=st.showtime_id,
                   signature=blocks[0]["signature"] if blocks else None)
        elif not first_run:
            newly_open = [b for b in blocks if b["signature"] not in previous]
            if newly_open:
                best = newly_open[0]
                title = f"PRIME SEAT: {movie_cfg['short_name']}"
                msg = (
                    f"{format_showtime(st.iso, tz)} — {', '.join(best['labels'])} just became "
                    f"available in preferred rows. Tap BOOK NOW."
                )
                notify(topic, title, msg, st.url, dry_run, showtime_id=st.showtime_id,
                       signature=best["signature"])
            elif newly_selectable:
                sample = ", ".join(s.label for s in newly_selectable[:4])
                title = f"SEAT OPENED: {movie_cfg['short_name']}"
                msg = (
                    f"{format_showtime(st.iso, tz)} — {sample} just became selectable"
                    + (f" (+{len(newly_selectable) - 4} more)" if len(newly_selectable) > 4 else "")
                    + ". Tap BOOK NOW."
                )
                notify(topic, title, msg, st.url, dry_run, showtime_id=st.showtime_id)

        movie_state["seat_snapshots"][st.showtime_id] = current
        movie_state["selectable_snapshots"][st.showtime_id] = current_selectable
        movie_state["verified_inventory"][st.showtime_id] = verified_inventory
        movie_state.setdefault("seat_checked_at", {})[st.showtime_id] = utcnow().isoformat()
        movie_state["pending_seat_checks"] = [sid for sid in movie_state.get("pending_seat_checks", []) if sid != st.showtime_id]
    movie_state["seat_maps_checked_this_run"] = len(selected)
    movie_state["selectable_seats_this_run"] = available_count
    movie_state["alertable_seats_this_run"] = alertable_count
    movie_state["preferred_blocks_this_run"] = preferred_count


def prune(movie_state: dict, today: date) -> None:
    expired = [sid for sid, m in movie_state.get("showtimes", {}).items() if parse_day(m["iso"][:10]) < today]
    for sid in expired:
        movie_state["showtimes"].pop(sid, None)
        movie_state.get("seat_snapshots", {}).pop(sid, None)
        movie_state.get("selectable_snapshots", {}).pop(sid, None)
        movie_state.get("verified_inventory", {}).pop(sid, None)
        movie_state.get("seat_checked_at", {}).pop(sid, None)
    movie_state["pending_seat_checks"] = [sid for sid in movie_state.get("pending_seat_checks", []) if sid not in expired]


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


def run_once(config: dict, state: dict, dry_run: bool = False) -> dict:
    """Stage per-movie observations and alerts; never publish before saving state.

    A failed movie rolls back its partial scan. A different movie may still
    succeed. Overall success requires every configured movie to be validated.
    """
    theater = config["theater"]
    polling = config.get("polling", {})
    tz = ZoneInfo(theater["timezone"])
    today = datetime.now(tz).date()
    topic = os.environ.get("NTFY_TOPIC", "")
    state["version"] = 3
    state.setdefault("movies", {})
    state.setdefault("outbox", [])
    result = {"started_at": utcnow().isoformat(), "status": "failed", "movies": {}}
    if not config.get("movies"):
        raise ScanError("At least one movie must be configured")

    if backoff_active(state):
        result.update(status="backoff", backoff_until=state["backoff_until"])
        for movie in config["movies"]:
            result["movies"][str(movie["movie_id"])] = {"status": "backoff"}
        result["finished_at"] = utcnow().isoformat()
        state["last_scan"] = result
        return result

    for movie_cfg in config["movies"]:
        mid = str(movie_cfg["movie_id"])
        previous_state = state["movies"].setdefault(
            mid,
            {
                "initialized": False,
                "showtimes": {},
                "seat_snapshots": {},
                "selectable_snapshots": {},
                "verified_inventory": {},
                "seat_poll_cursor": 0,
                "date_probe_cursor": 0,
            },
        )
        movie_state = copy.deepcopy(previous_state)
        staged_alerts = []

        def stage_alert(_topic, title, message, url, _dry_run, **evidence):
            staged_alerts.append({
                "id": uuid.uuid4().hex, "movie_id": mid,
                "title": title, "message": message, "url": url,
                "created_at": utcnow().isoformat(),
                **evidence,
            })
        # Migration-friendly defaults for an existing v1 state.json.
        movie_state.setdefault("showtimes", {})
        movie_state.setdefault("seat_snapshots", {})
        movie_state.setdefault("selectable_snapshots", {})
        movie_state.setdefault("verified_inventory", {})
        movie_state.setdefault("seat_poll_cursor", 0)
        movie_state.setdefault("date_probe_cursor", 0)
        movie_state["pending_notification_checks"] = sorted({
            a["showtime_id"] for a in state["outbox"]
            if a.get("movie_id") == mid and a.get("showtime_id")
        })
        seed_configured_showtimes(movie_cfg, movie_state, theater)
        prune(movie_state, today)

        try:
            remaining_timeout(1)
            first_run, new_showtimes = discover_movie(movie_cfg, movie_state, theater, polling, today)
            if first_run:
                log(f"{movie_cfg['short_name']}: baseline created; suppressing initial alerts")
            elif new_showtimes:
                log(f"{movie_cfg['short_name']}: discovered {len(new_showtimes)} new showtime(s)")
            poll_seats_and_alert(
                movie_cfg, movie_state, polling, tz, first_run, new_showtimes, topic, dry_run,
                notify=stage_alert,
            )
            checked_at = utcnow().isoformat()
            status = "success" if movie_state.get("initialized") else "initializing"
            evidence = {
                "status": status, "checked_at": checked_at,
                "date_pages_checked": len(movie_state["date_observations"]),
                "seat_maps_checked": movie_state.get("seat_maps_checked_this_run", 0),
                "selectable_seats": movie_state.get("selectable_seats_this_run", 0),
                "alertable_seats": movie_state.get("alertable_seats_this_run", 0),
                "preferred_blocks": movie_state.get("preferred_blocks_this_run", 0),
                "known_showtimes": len(movie_state["showtimes"]),
                "alerts_queued": len(staged_alerts),
                "dates_not_published": sum(d["result"] == "date_not_published" for d in movie_state["date_observations"]),
            }
            if status == "success":
                movie_state["last_success_at"] = checked_at
            movie_state["last_attempt"] = evidence
            state["movies"][mid] = movie_state
            state["outbox"].extend(staged_alerts)
            result["movies"][mid] = evidence
        except CinemarkBackoff as exc:
            set_backoff(state, exc)
            for target in config["movies"]:
                target_id = str(target["movie_id"])
                result["movies"].setdefault(target_id, {"status": "backoff"})
            result["backoff_until"] = state["backoff_until"]
            break
        except Exception as exc:
            log(f"WARN: {movie_cfg['short_name']} scan failed: {exc}")
            evidence = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)[:300]}
            previous_state["last_attempt"] = evidence
            result["movies"][mid] = evidence
    result["finished_at"] = utcnow().isoformat()
    result["status"] = "success" if all(m["status"] == "success" for m in result["movies"].values()) else "failed"
    state["last_scan"] = result
    return result


def flush_outbox(state: dict, persist, topic: str, dry_run: bool = False, delivery: dict | None = None) -> int:
    """At-least-once delivery. A crash after ntfy accepts can cause a duplicate.

    Saving before delivery prevents lost alerts; saving each acknowledgement
    suppresses duplicates in normal operation and when retrying other failures.
    Never claim exactly-once notification delivery across two independent APIs.
    """
    delivered = 0
    expired = 0
    unverified = 0
    for alert in list(state.get("outbox", [])):
        age = (utcnow() - datetime.fromisoformat(alert["created_at"])).total_seconds()
        if age > 15 * 60:
            state["outbox"].remove(alert)
            state["expired_alerts"] = int(state.get("expired_alerts", 0)) + 1
            # Re-observe an expired event before offering its inventory again.
            movie = state.get("movies", {}).get(alert.get("movie_id"), {})
            sid = alert.get("showtime_id")
            if sid in movie.get("showtimes", {}):
                movie["pending_seat_checks"] = sorted(set(movie.get("pending_seat_checks", [])) | {sid})
            persist(state)
            expired += 1
            continue
        if alert.get("showtime_id"):
            mid, sid = alert["movie_id"], alert["showtime_id"]
            movie = state.get("movies", {}).get(mid, {})
            scan = state.get("last_scan", {})
            checked_at = movie.get("seat_checked_at", {}).get(sid, "")
            scan_started = scan.get("started_at", "")
            fresh = (scan.get("movies", {}).get(mid, {}).get("status") == "success"
                     and checked_at and scan_started
                     and datetime.fromisoformat(checked_at) >= datetime.fromisoformat(scan_started))
            if not fresh:
                unverified += 1
                continue
            still_available = movie.get("verified_inventory", {}).get(sid, False)
            signature = alert.get("signature")
            if signature:
                still_available = signature in movie.get("seat_snapshots", {}).get(sid, [])
            if not still_available:
                state["outbox"].remove(alert)
                state["cancelled_alerts"] = int(state.get("cancelled_alerts", 0)) + 1
                persist(state)
                continue
        publish_ntfy(topic, alert["title"], alert["message"], alert["url"], dry_run)
        if not dry_run:
            if alert.get("kind") == "daily_status":
                state["last_daily_status_date"] = alert["daily_status_date"]
            elif delivery is not None:
                mid = alert.get("movie_id", "unknown")
                delivery[mid] = delivery.get(mid, 0) + 1
            state["outbox"].remove(alert)
            persist(state)
        delivered += 1
    if expired:
        raise ScanError(f"{expired} undelivered alert(s) expired; notification path needs investigation")
    if unverified:
        raise ScanError(f"{unverified} queued alert(s) need a fresh seat observation before delivery")
    return delivered


def status_lines(
    config: dict,
    result: dict,
    delivery: dict | None = None,
    dry_run: bool = False,
    include_notification: bool = True,
) -> list[str]:
    """Human audit lines. Never invent availability or notification delivery."""
    delivery = delivery or {}
    tz = ZoneInfo(config["theater"]["timezone"])
    fallback_time = result.get("finished_at", utcnow().isoformat())
    lines = []
    for movie in config["movies"]:
        mid = str(movie["movie_id"])
        observed = result.get("movies", {}).get(mid, {})
        when = datetime.fromisoformat(observed.get("checked_at", fallback_time)).astimezone(tz)
        prefix = f"{when:%Y-%m-%d %I:%M:%S %p %Z} — {movie['short_name']}"
        status = observed.get("status", "failed")
        if status != "success":
            availability = {"backoff": "CHECK SKIPPED: site backoff",
                            "initializing": "BASELINE IN PROGRESS"}.get(status, "CHECK FAILED: availability unknown")
        elif observed.get("seat_maps_checked", 0):
            if observed.get("selectable_seats", 0):
                alertable = observed.get("alertable_seats", observed["selectable_seats"])
                availability = (f"tickets available ({observed['selectable_seats']} selectable seats, "
                                f"{alertable} alert-eligible seats, "
                                f"{observed.get('preferred_blocks', 0)} preferred seat blocks across "
                                f"{observed['seat_maps_checked']} checked showtimes)")
            else:
                availability = f"tickets unavailable in {observed['seat_maps_checked']} checked showtimes"
        elif observed.get("known_showtimes", 0):
            availability = "showtimes known; seat maps not checked in this cycle"
        elif observed.get("dates_not_published", 0) == observed.get("date_pages_checked", -1):
            availability = "tickets not listed: requested dates not published in theater calendar"
        else:
            availability = "no matching showtimes found on checked dates"
        if not include_notification:
            lines.append(f"{prefix} — {availability}")
            continue
        if dry_run:
            notification = "DRY RUN — no notification sent"
        elif delivery.get(mid, 0):
            notification = f"notification sent ({delivery[mid]} accepted by ntfy)"
        elif result.get("notification_error"):
            notification = "notification delivery not confirmed"
        elif status == "success":
            notification = "no new qualifying alert — no notification sent"
        else:
            notification = "no notification sent"
        lines.append(f"{prefix} — {availability} — {notification}")
    return lines


def queue_daily_status(
    config: dict,
    state: dict,
    result: dict,
    dry_run: bool = False,
    now: datetime | None = None,
) -> bool:
    """Queue one honest local-day status after the configured notification time."""
    if dry_run or not result.get("movies"):
        return False
    tz = ZoneInfo(config["theater"]["timezone"])
    local_now = (now or utcnow()).astimezone(tz)
    after = config.get("polling", {}).get("daily_status_after")
    if not after:
        return False
    try:
        threshold = datetime.strptime(after, "%H:%M").time()
    except ValueError as exc:
        raise ScanError("polling.daily_status_after must use HH:MM") from exc
    day = local_now.date().isoformat()
    if local_now.time() < threshold or state.get("last_daily_status_date") == day:
        return False
    if any(a.get("kind") == "daily_status" and a.get("daily_status_date") == day
           for a in state.get("outbox", [])):
        return False
    state.setdefault("outbox", []).append({
        "id": f"daily-status:{day}",
        "kind": "daily_status",
        "daily_status_date": day,
        "title": "Daily IMAX ticket status",
        "message": "\n".join(status_lines(config, result, include_notification=False)),
        "url": f"{BASE}/theatres/{config['theater']['slug']}",
        "created_at": (now or utcnow()).isoformat(),
    })
    return True


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
    parser.add_argument("--max-seconds", type=int, default=270, help="Total scan budget, including retries")
    args = parser.parse_args()
    config = load_json(CONFIG_PATH)
    if args.test_notify:
        test_notify(config)
        return 0
    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    token = DEADLINE.set(time.monotonic() + args.max_seconds)
    try:
        result = run_once(config, state, dry_run=args.dry_run)
        persist = (lambda obj: None) if args.dry_run else (lambda obj: save_json(STATE_PATH, obj))
        queue_daily_status(config, state, result, args.dry_run)
        persist(state)
        delivery = {}
        try:
            flush_outbox(state, persist, os.environ.get("NTFY_TOPIC", ""), args.dry_run, delivery)
        except Exception as exc:
            result["notification_error"] = type(exc).__name__
            result["status"] = "failed"
        result["notifications_sent_by_movie"] = delivery
        result["status_lines"] = status_lines(config, result, delivery, args.dry_run)
        persist(state)
        for line in result["status_lines"]:
            print(line, flush=True)
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as summary:
                summary.write("## Actual watcher observations\n\n" + "\n\n".join(result["status_lines"]) + "\n")
        log(json.dumps(result, sort_keys=True))
        if args.dry_run:
            log("Dry run complete; state.json left unchanged; no health heartbeat sent")
        return 0 if result["status"] == "success" else 1
    finally:
        DEADLINE.reset(token)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise
