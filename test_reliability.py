"""Offline regression tests: synthetic HTML matching inspected public markup.

No test contacts Cinemark, ntfy, Healthchecks, or a cloud account.
"""
import copy
import io
import json
import time
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import watcher as w
from cloud_service import Runner, Settings, handler_for, scheduled_slot, validate_heartbeat_url
from state_store import FirestoreStore, LeaseLost

DAY = date.today() + timedelta(days=1)
ISO = DAY.isoformat() + "T19:15:00"
ST = w.Showtime("207", "123", "104867", ISO)
THEATER = {"id": "207", "name": "Cinemark Dallas XD and IMAX",
           "slug": "tx-dallas/cinemark-dallas-xd-and-imax", "timezone": "America/Chicago"}


def listing(day=DAY, movie="104867", sid="123", selected=None, offered=None):
    selected = selected or day
    offered = offered or [selected]
    return (f'<title>{THEATER["name"]}</title>'
            f'<div data-test="ShowdatesList" data-showdates="{selected:%m/%d/%Y} 12:00:00 AM"></div>'
            + "".join(f'<a data-datevalue="{d.isoformat()}">date</a>' for d in offered)
            + f'<div id="listOfMoviesOrTheaters"><a href="/TicketSeatMap/?TheaterId=207&amp;'
              f'ShowtimeId={sid}&amp;CinemarkMovieId={movie}&amp;Showtime={selected}T19:15:00">go</a></div>')


def seat_map(st=ST, available=True, row="H", available_numbers=None):
    action = st.url.replace("&", "&amp;")
    return (f'<title>Cinemark - Reserve Your Seats</title><form id="FormSeatMap" action="{action}">'
            + "".join(f'<button info="{row},{n},8,{n},{st.showtime_id}" '
                      f'available="{str(n in available_numbers if available_numbers is not None else available)}" '
                      f'class="seatBlock">seat</button>' for n in range(10, 15)) + '</form>')


def config(two=True):
    cfg = copy.deepcopy(w.load_json(w.CONFIG_PATH))
    cfg["polling"] = {"request_gap_seconds": 0, "timeout_seconds": 1}
    # Keep synthetic fixtures independent of production priority and date limits.
    cfg["movies"].sort(key=lambda movie: movie["movie_id"])
    cfg["movies"] = cfg["movies"][:2 if two else 1]
    for movie in cfg["movies"]:
        movie.pop("seed_showtimes", None)
        movie.pop("monitoring_end", None)
        movie.update(monitoring_start=str(DAY), monitoring_window_days=1,
                     monitoring_window_shift_days=1,
                     max_date_pages_per_run=5,
                     bootstrap_start=str(DAY), bootstrap_end=str(DAY),
                     pre_sale_probe_dates=[str(DAY)], extra_probe_dates=[],
                     frontier_lookbehind_days=0, frontier_lookahead_days=0)
    return cfg


def state(two=True, with_showtime=False):
    result = {"movies": {m["movie_id"]: {"initialized": True, "showtimes": {}, "seat_snapshots": {}}
                          for m in config(two)["movies"]}}
    if with_showtime:
        result["movies"][ST.movie_id]["showtimes"][ST.showtime_id] = {
            "theater_id": ST.theater_id, "iso": ST.iso}
    return result


class MemoryStore:
    def __init__(self, initial=None):
        self.state = copy.deepcopy(initial or {})
        self.owner = None
        self.saves = []

    def acquire(self, owner):
        if self.owner is not None:
            return None
        self.owner = owner
        return copy.deepcopy(self.state)

    def save(self, owner, state):
        if self.owner != owner:
            raise LeaseLost()
        self.state = copy.deepcopy(state)
        self.saves.append(copy.deepcopy(state))

    def release(self, owner, state):
        self.save(owner, state)
        self.owner = None


SETTINGS = Settings("test-project", "projects/test-project/locations/us-central1/jobs/imax-watcher",
                    "test-topic", "https://hc-ping.com/00000000-0000-0000-0000-000000000001")


class ValidationTests(unittest.TestCase):
    def test_real_date_identity(self):
        self.assertEqual(w.validate_discovery(listing(), THEATER, DAY), "selected_date")

    def test_unpublished_date_not_current_inventory(self):
        page = listing(day=DAY, selected=DAY-timedelta(days=1))
        self.assertEqual(w.validate_discovery(page, THEATER, DAY), "date_not_published")

    def test_unpublished_date_with_empty_fallback_is_not_failure(self):
        page = listing(day=DAY, selected=DAY-timedelta(days=1))
        page = page.split('<div id="listOfMoviesOrTheaters">')[0] + '<div id="listOfMoviesOrTheaters"></div>'
        self.assertEqual(w.validate_discovery(page, THEATER, DAY), "date_not_published")

    def test_ignored_advertised_date_fails(self):
        page = listing(selected=DAY-timedelta(days=1), offered=[DAY, DAY-timedelta(days=1)])
        with self.assertRaises(w.ScanError):
            w.validate_discovery(page, THEATER, DAY)

    def test_challenge_is_not_empty_inventory(self):
        with self.assertRaises(w.ScanError):
            w.validate_discovery('<title>Verify you are human</title>', THEATER, DAY)

    def test_changed_calendar_fails(self):
        with self.assertRaises(w.ScanError):
            w.validate_discovery(listing().replace("ShowdatesList", "Changed"), THEATER, DAY)

    def test_empty_placeholder_is_not_no_inventory(self):
        page = listing().split('<div id="listOfMoviesOrTheaters">')[0] + '<div id="listOfMoviesOrTheaters"></div>'
        with self.assertRaises(w.ScanError):
            w.validate_discovery(page, THEATER, DAY)

    def test_explicit_no_showtimes_valid(self):
        page = listing().split('<div id="listOfMoviesOrTheaters">')[0] + '<div id="listOfMoviesOrTheaters">No showtimes available</div>'
        self.assertEqual(w.validate_discovery(page, THEATER, DAY), "selected_date")

    def test_wrong_theater_fails(self):
        with self.assertRaises(w.ScanError):
            w.validate_discovery(listing().replace("TheaterId=207", "TheaterId=999"), THEATER, DAY)

    def test_wrong_link_date_fails(self):
        with self.assertRaises(w.ScanError):
            w.validate_discovery(listing().replace(ISO, "2000-01-01T10:00:00"), THEATER, DAY)

    def test_after_midnight_showtime_belongs_to_previous_business_day(self):
        spillover = DAY + timedelta(days=1)
        late_link = (f'<a href="/TicketSeatMap/?TheaterId=207&amp;ShowtimeId=124&amp;'
                     f'CinemarkMovieId=104867&amp;Showtime={spillover}T02:45:00">late</a>')
        page = listing().replace("</a></div>", f"</a>{late_link}</div>")
        self.assertEqual(w.validate_discovery(page, THEATER, DAY), "selected_date")

    def test_sold_out_map_valid(self):
        seats = w.validated_seats(seat_map(available=False), ST)
        self.assertTrue(seats)
        self.assertFalse(any(s.available for s in seats))

    def test_wrong_seatmap_fails(self):
        with self.assertRaises(w.ScanError):
            w.validated_seats(seat_map().replace("ShowtimeId=123", "ShowtimeId=456"), ST)

    def test_empty_map_is_not_sold_out(self):
        with self.assertRaises(w.ScanError):
            w.validated_seats("<html>No seats parsed</html>", ST)

    def test_seat_from_other_showtime_fails(self):
        with self.assertRaises(w.ScanError):
            w.validated_seats(seat_map().replace(",123", ",456"), ST)

    def test_missing_availability_fails(self):
        with self.assertRaises(w.ScanError):
            w.validated_seats(seat_map().replace('available="True"', ''), ST)

    def test_explicit_false_wins(self):
        seat = w.seats_from_html('<button info="H,11,8,11,123" available="False" class="seatAvailable">')[0]
        self.assertFalse(seat.available)

    def test_disabled_wins(self):
        seat = w.seats_from_html('<button disabled info="H,11,8,11,123" available="True">')[0]
        self.assertFalse(seat.available)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_two_valid_negative_observations(self):
        s = state()
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            result = w.run_once(config(), s)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["movies"]), 2)
        self.assertTrue(all(m.get("last_success_at") for m in s["movies"].values()))

    def test_failure_not_swallowed_and_old_snapshot_preserved(self):
        s = state(with_showtime=True)
        original = copy.deepcopy(s["movies"][ST.movie_id]["showtimes"])
        with patch.object(w, "fetch", side_effect=TimeoutError("failed")):
            result = w.run_once(config(), s)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(s["movies"][ST.movie_id]["showtimes"], original)
        self.assertNotIn("last_success_at", s["movies"][ST.movie_id])

    def test_one_movie_failure_does_not_hide_other_result(self):
        with patch.object(w, "fetch", side_effect=[TimeoutError(), listing(movie="999")]):
            result = w.run_once(config(), state())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["movies"]["109913"]["status"], "success")

    def test_backoff_does_not_fetch_or_succeed(self):
        s = state()
        s["backoff_until"] = (w.utcnow()+timedelta(hours=1)).isoformat()
        with patch.object(w, "fetch") as fetch:
            result = w.run_once(config(), s)
        fetch.assert_not_called()
        self.assertEqual(result["status"], "backoff")

    def test_429_backoff_persisted(self):
        s = state()
        with patch.object(w, "fetch", side_effect=w.CinemarkBackoff("HTTP 429", 600)) as fetch:
            result = w.run_once(config(), s)
        self.assertEqual(fetch.call_count, 1)
        self.assertIn("backoff_until", s)
        self.assertNotEqual(result["status"], "success")

    def test_alert_staged_not_sent_and_normal_dedup(self):
        s = state(two=False)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map()]), patch.object(w, "publish_ntfy") as notify:
            self.assertEqual(w.run_once(config(False), s)["status"], "success")
        notify.assert_not_called()
        self.assertEqual(len(s["outbox"]), 1)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map()]):
            w.run_once(config(False), s)
        self.assertEqual(len(s["outbox"]), 1)

    def test_no_partial_alert_on_invalid_seatmap(self):
        s = state(two=False)
        with patch.object(w, "fetch", side_effect=[listing(), "markup changed"]):
            result = w.run_once(config(False), s)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(s["outbox"], [])
        self.assertEqual(s["movies"][ST.movie_id]["showtimes"], {})

    def test_deadline_prevents_network(self):
        token = w.DEADLINE.set(time.monotonic()-1)
        try:
            with patch.object(w, "fetch") as fetch:
                result = w.run_once(config(), state())
            fetch.assert_not_called()
            self.assertEqual(result["status"], "failed")
        finally:
            w.DEADLINE.reset(token)

    def test_bootstrap_bounded(self):
        cfg = config(False)["movies"][0]
        cfg.update(monitoring_window_days=30, monitoring_window_shift_days=15,
                   bootstrap_end=str(DAY + timedelta(days=29)))
        self.assertEqual(len(w.scan_dates_for_movie(cfg, {}, DAY)), 5)

    def test_monitoring_window_is_30_days_and_shifts_after_15(self):
        cfg = {"monitoring_start": "2026-12-17", "monitoring_window_days": 30,
               "monitoring_window_shift_days": 15}
        self.assertEqual(w.monitoring_window(cfg, date(2026, 12, 17)),
                         (date(2026, 12, 17), date(2027, 1, 15)))
        self.assertEqual(w.monitoring_window(cfg, date(2026, 12, 31)),
                         (date(2026, 12, 17), date(2027, 1, 15)))
        self.assertEqual(w.monitoring_window(cfg, date(2027, 1, 1)),
                         (date(2027, 1, 1), date(2027, 1, 30)))

    def test_dune_window_starts_december_17(self):
        movie = next(m for m in w.load_json(w.CONFIG_PATH)["movies"] if m["short_name"] == "DUNE")
        self.assertEqual(w.monitoring_window(movie, date(2026, 9, 1)),
                         (date(2026, 12, 17), date(2027, 1, 15)))

    def test_odyssey_window_starts_immediately(self):
        movie = next(m for m in w.load_json(w.CONFIG_PATH)["movies"] if m["short_name"] == "ODYSSEY")
        self.assertEqual(w.monitoring_window(movie, date(2026, 9, 1)),
                         (date(2026, 9, 1), date(2026, 9, 17)))

    def test_showtime_selection_stays_inside_active_window(self):
        cfg = config(False)["movies"][0]
        cfg.update(monitoring_window_days=30, monitoring_window_shift_days=15)
        movie_state = {"showtimes": {
            "before": {"theater_id": "207", "iso": (DAY - timedelta(days=1)).isoformat() + "T10:00:00"},
            "inside": {"theater_id": "207", "iso": (DAY + timedelta(days=29)).isoformat() + "T10:00:00"},
            "after": {"theater_id": "207", "iso": (DAY + timedelta(days=30)).isoformat() + "T10:00:00"},
        }}
        selected = w.eligible_showtimes(cfg, movie_state, DAY, {"before", "inside", "after"})
        self.assertEqual([st.showtime_id for st in selected], ["inside"])

    def test_showtime_that_already_started_today_is_not_polled(self):
        cfg = config(False)["movies"][0]
        movie_state = {"showtimes": {
            "past": {"theater_id": "207", "iso": DAY.isoformat() + "T08:00:00"},
            "future": {"theater_id": "207", "iso": DAY.isoformat() + "T19:15:00"},
        }}
        now = datetime.fromisoformat(DAY.isoformat() + "T12:00:00").replace(
            tzinfo=w.ZoneInfo("America/Chicago"))
        selected = w.eligible_showtimes(cfg, movie_state, DAY, {"past", "future"}, now=now)
        self.assertEqual([st.showtime_id for st in selected], ["future"])

    def test_unwanted_early_and_late_showtimes_are_not_polled(self):
        cfg = config(False)["movies"][0]
        cfg["seat_watch"].update(earliest_showtime="09:00", latest_showtime="22:59")
        movie_state = {"showtimes": {
            "0245": {"theater_id": "207", "iso": DAY.isoformat() + "T02:45:00"},
            "0800": {"theater_id": "207", "iso": DAY.isoformat() + "T08:00:00"},
            "0900": {"theater_id": "207", "iso": DAY.isoformat() + "T09:00:00"},
            "2259": {"theater_id": "207", "iso": DAY.isoformat() + "T22:59:00"},
            "2300": {"theater_id": "207", "iso": DAY.isoformat() + "T23:00:00"},
        }}
        selected = w.eligible_showtimes(cfg, movie_state, DAY, set(movie_state["showtimes"]))
        self.assertEqual([st.showtime_id for st in selected], ["0900", "2259"])

    def test_configured_seed_showtime_is_pinned_ahead_of_rotation(self):
        cfg = config(False)["movies"][0]
        cfg["seed_showtimes"] = [{"showtime_id": "pinned", "iso": DAY.isoformat() + "T15:15:00"}]
        cfg["seat_watch"]["max_seat_maps_per_run"] = 1
        movie_state = {"showtimes": {
            "other": {"theater_id": "207", "iso": DAY.isoformat() + "T10:00:00"},
            "pinned": {"theater_id": "207", "iso": DAY.isoformat() + "T15:15:00"},
        }, "pending_seat_checks": [], "seat_poll_cursor": 0}
        selected = w.select_showtimes_to_poll(cfg, movie_state, DAY, set())
        self.assertEqual([st.showtime_id for st in selected], ["pinned"])

    def test_shifted_window_restarts_date_rotation_at_current_date(self):
        cfg = config(False)["movies"][0]
        cfg.update(monitoring_window_days=30, monitoring_window_shift_days=15,
                   max_date_pages_per_run=5)
        shifted_day = DAY + timedelta(days=15)
        movie_state = {"initialized": True, "date_probe_cursor": 20,
                       "active_window_start": DAY.isoformat()}
        self.assertEqual(w.scan_dates_for_movie(cfg, movie_state, shifted_day),
                         [shifted_day + timedelta(days=n) for n in range(5)])

    def test_configured_showtime_seeded_for_direct_polling(self):
        movie = config(False)["movies"][0]
        movie["seed_showtimes"] = [{"showtime_id": "644486", "iso": "2026-12-17T15:15:00"}]
        movie_state = {"showtimes": {}}
        w.seed_configured_showtimes(movie, movie_state, THEATER)
        self.assertEqual(movie_state["showtimes"]["644486"]["theater_id"], "207")
        self.assertEqual(movie_state["showtimes"]["644486"]["iso"], "2026-12-17T15:15:00")

    def test_date_page_observation_is_timestamped(self):
        movie = config(False)["movies"][0]
        movie_state = {"initialized": True, "showtimes": {}}
        checked = datetime(2026, 9, 1, 14, 5, tzinfo=timezone.utc)
        with patch.object(w, "fetch", return_value=listing(movie="999")), \
                patch.object(w, "utcnow", return_value=checked):
            w.discover_movie(movie, movie_state, THEATER,
                             {"request_gap_seconds": 0, "timeout_seconds": 1}, DAY)
        self.assertEqual(movie_state["date_checked_at"][DAY.isoformat()], checked.isoformat())

    def test_ignored_rows_never_alert(self):
        movie = config(False)["movies"][0]
        movie["seat_watch"].update(ignored_rows=["A", "B", "C", "D"], preferred_rows=["G", "H", "J", "K"])
        movie_state = state(False, True)["movies"][ST.movie_id]
        notify = Mock()
        with patch.object(w, "fetch", return_value=seat_map(row="D")):
            w.poll_seats_and_alert(movie, movie_state, {"request_gap_seconds": 0, "timeout_seconds": 1},
                                   w.ZoneInfo("America/Chicago"), False, [], "test", False, notify)
        notify.assert_not_called()
        self.assertEqual(movie_state["selectable_seats_this_run"], 5)
        self.assertEqual(movie_state["alertable_seats_this_run"], 0)

    def test_nonpreferred_seat_reopening_alerts(self):
        movie = config(False)["movies"][0]
        movie["seat_watch"].update(ignored_rows=["A", "B", "C", "D"], preferred_rows=["G", "H", "J", "K"])
        movie_state = state(False, True)["movies"][ST.movie_id]
        args = (movie, movie_state, {"request_gap_seconds": 0, "timeout_seconds": 1},
                w.ZoneInfo("America/Chicago"), False, [], "test", False)
        with patch.object(w, "fetch", return_value=seat_map(row="E", available_numbers={10})):
            w.poll_seats_and_alert(*args, notify=Mock())
        notify = Mock()
        with patch.object(w, "fetch", return_value=seat_map(row="E", available_numbers={10, 11})):
            w.poll_seats_and_alert(*args, notify=notify)
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[1], "SEAT OPENED: ODYSSEY")

    def test_existing_inventory_is_baselined_when_per_seat_snapshot_is_added(self):
        movie = config(False)["movies"][0]
        movie_state = state(False, True)["movies"][ST.movie_id]
        movie_state["verified_inventory"] = {ST.showtime_id: True}
        notify = Mock()
        with patch.object(w, "fetch", return_value=seat_map(row="E", available_numbers={10, 11})):
            w.poll_seats_and_alert(movie, movie_state, {"request_gap_seconds": 0, "timeout_seconds": 1},
                                   w.ZoneInfo("America/Chicago"), False, [], "test", False, notify)
        notify.assert_not_called()
        self.assertEqual(movie_state["selectable_snapshots"][ST.showtime_id], ["E10", "E11"])

    def test_new_showtime_overflow_preserved(self):
        cfg = config(False)["movies"][0]
        cfg["seat_watch"]["max_seat_maps_per_run"] = 1
        s = state(False, True)["movies"][ST.movie_id]
        s["showtimes"]["124"] = {"theater_id": "207", "iso": ISO}
        s["pending_seat_checks"] = ["123", "124"]
        xs = w.select_showtimes_to_poll(cfg, s, DAY, {"123", "124"})
        self.assertEqual(len(xs), 1)
        self.assertEqual(len(s["pending_seat_checks"]), 2)

    def test_outbox_failure_keeps_alert(self):
        s = {"outbox": [{"id": "x", "created_at": w.utcnow().isoformat(), "title": "test", "message": "msg", "url": ST.url}]}
        with patch.object(w, "publish_ntfy", side_effect=RuntimeError()):
            with self.assertRaises(RuntimeError):
                w.flush_outbox(s, Mock(), "test")
        self.assertEqual(len(s["outbox"]), 1)

    def test_queued_alert_rechecked_before_delivery(self):
        s = state(two=False)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map()]):
            w.run_once(config(False), s)
        with patch.object(w, "publish_ntfy") as notify:
            w.flush_outbox(s, Mock(), "test")
        notify.assert_called_once()

    def test_inventory_gone_cancels_old_queued_alert(self):
        s = state(two=False)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map()]):
            w.run_once(config(False), s)
        self.assertEqual(len(s["outbox"]), 1)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map(available=False)]):
            w.run_once(config(False), s)
        with patch.object(w, "publish_ntfy") as notify:
            w.flush_outbox(s, Mock(), "test")
        notify.assert_not_called()
        self.assertEqual(s["outbox"], [])
        self.assertEqual(s["cancelled_alerts"], 1)

    def test_failed_recheck_does_not_send_old_available_alert(self):
        s = state(two=False)
        with patch.object(w, "fetch", side_effect=[listing(), seat_map()]):
            w.run_once(config(False), s)
        with patch.object(w, "fetch", side_effect=TimeoutError()):
            w.run_once(config(False), s)
        with patch.object(w, "publish_ntfy") as notify, self.assertRaises(w.ScanError):
            w.flush_outbox(s, Mock(), "test")
        notify.assert_not_called()
        self.assertEqual(len(s["outbox"]), 1)

    def test_outbox_ack_saved(self):
        s = {"outbox": [{"id": "x", "created_at": w.utcnow().isoformat(), "title": "test", "message": "msg", "url": ST.url}]}
        persist = Mock()
        with patch.object(w, "publish_ntfy"):
            self.assertEqual(w.flush_outbox(s, persist, "test"), 1)
        self.assertEqual(s["outbox"], [])
        persist.assert_called_once()

    def test_expired_alerts_do_not_block_fresh_alert(self):
        stale = {"id": "old", "created_at": (w.utcnow()-timedelta(hours=1)).isoformat(),
                 "title": "stale", "message": "msg", "url": ST.url}
        fresh = dict(stale, id="new", created_at=w.utcnow().isoformat(), title="fresh")
        s = {"outbox": [stale, dict(stale, id="old2"), fresh]}
        with patch.object(w, "publish_ntfy") as notify:
            with self.assertRaises(w.ScanError):
                w.flush_outbox(s, Mock(), "test")
        self.assertEqual(notify.call_count, 1)
        self.assertEqual(notify.call_args.args[1], "fresh")
        self.assertEqual(s["outbox"], [])
        self.assertEqual(s["expired_alerts"], 2)

    def test_test_notify_never_loads_state_or_scans(self):
        with patch("sys.argv", ["watcher.py", "--test-notify"]), patch.object(w, "test_notify") as notify, patch.object(w, "run_once") as scan:
            self.assertEqual(w.main(), 0)
        notify.assert_called_once()
        scan.assert_not_called()

    def test_daily_status_queued_once_and_acknowledged(self):
        cfg = config(False)
        cfg["polling"]["daily_status_after"] = "09:00"
        result = {"finished_at": "2026-09-01T14:05:00+00:00", "movies": {
            ST.movie_id: {"status": "success", "checked_at": "2026-09-01T14:05:00+00:00",
                          "seat_maps_checked": 1, "selectable_seats": 3,
                          "alertable_seats": 0, "preferred_blocks": 0}
        }}
        s = {"outbox": []}
        now = datetime(2026, 9, 1, 14, 5, tzinfo=timezone.utc)
        self.assertTrue(w.queue_daily_status(cfg, s, result, now=now))
        self.assertFalse(w.queue_daily_status(cfg, s, result, now=now))
        persist = Mock()
        with patch.object(w, "publish_ntfy"), patch.object(w, "utcnow", return_value=now):
            self.assertEqual(w.flush_outbox(s, persist, "test"), 1)
        self.assertEqual(s["last_daily_status_date"], "2026-09-01")
        self.assertFalse(w.queue_daily_status(cfg, s, result, now=now))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(state())
        self.heartbeat = Mock()
        self.runner = Runner(config(), SETTINGS, self.store, self.heartbeat)
        self.slot = w.utcnow().replace(minute=(w.utcnow().minute//10)*10, second=0, microsecond=0).isoformat()
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_success_after_durable_observations(self):
        def beat(url):
            self.assertEqual(self.store.state["last_run"]["status"], "success")
            self.assertTrue(all(v.get("last_success_at") for v in self.store.state["movies"].values()))
        self.runner.heartbeat = Mock(side_effect=beat)
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            code, result = self.runner.execute(self.slot)
        self.assertEqual(code, 200)
        self.assertTrue(result["heartbeat_sent"])
        self.assertIsNone(self.store.owner)

    def test_duplicate_never_refreshes_heartbeat(self):
        with patch.object(w, "fetch", return_value=listing(movie="999")) as fetch:
            self.runner.execute(self.slot)
            calls = fetch.call_count
            code, result = self.runner.execute(self.slot)
            self.assertEqual(fetch.call_count, calls)
        self.heartbeat.assert_called_once()
        self.assertEqual(result["status"], "duplicate")

    def test_failed_scan_no_heartbeat(self):
        with patch.object(w, "fetch", side_effect=TimeoutError()):
            code, result = self.runner.execute(self.slot)
        self.assertEqual(code, 503)
        self.heartbeat.assert_not_called()
        self.assertEqual(result["status"], "failed")

    def test_manual_scan_never_heartbeat(self):
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            code, result = self.runner.execute(None, "manual")
        self.assertEqual(code, 200)
        self.assertEqual(result["trigger"], "manual")
        self.heartbeat.assert_not_called()

    def test_storage_failure_no_heartbeat(self):
        self.store.save = Mock(side_effect=RuntimeError("storage down"))
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            with self.assertRaises(RuntimeError):
                self.runner.execute(self.slot)
        self.heartbeat.assert_not_called()

    def test_notification_failure_no_heartbeat(self):
        with patch.object(w, "fetch", return_value=listing(movie="999")), patch.object(w, "flush_outbox", side_effect=RuntimeError()):
            code, _ = self.runner.execute(self.slot)
        self.assertEqual(code, 503)
        self.heartbeat.assert_not_called()

    def test_monitor_failure_is_failed_run(self):
        self.heartbeat.side_effect = RuntimeError("secret URL must not be logged")
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            code, result = self.runner.execute(self.slot)
        self.assertEqual(code, 503)
        self.assertEqual(result["status"], "heartbeat_failed")
        self.assertNotIn("secret URL", json.dumps(self.store.state))

    def test_overlapping_check_refused(self):
        self.store.owner = "other"
        code, _ = self.runner.execute(self.slot)
        self.assertEqual(code, 409)
        self.heartbeat.assert_not_called()

    def test_valid_scheduler_envelope(self):
        now = datetime(2026, 9, 1, 10, 0, 10, tzinfo=timezone.utc)
        headers = {"X-CloudScheduler-JobName": SETTINGS.scheduler_job,
                   "X-CloudScheduler-ScheduleTime": "2026-09-01T10:00:00Z"}
        self.assertEqual(scheduled_slot(headers, SETTINGS.scheduler_job, now), "2026-09-01T10:00:00+00:00")

    def test_invalid_scheduler_envelopes(self):
        now = datetime(2026, 9, 1, 10, 0, 10, tzinfo=timezone.utc)
        for timestamp in ("", "bad", "2026-09-01T09:40:00Z", "2026-09-01T10:10:00Z", "2026-09-01T10:00:05Z", "2026-09-01T10:00:00"):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                scheduled_slot({"X-CloudScheduler-JobName": SETTINGS.scheduler_job,
                                "X-CloudScheduler-ScheduleTime": timestamp}, SETTINGS.scheduler_job, now)

    def test_ping_secret_url_validation(self):
        validate_heartbeat_url(SETTINGS.heartbeat_url)
        for url in ("http://hc-ping.com/abc", "https://evil.example/abc", SETTINGS.heartbeat_url+"/fail"):
            with self.assertRaises(ValueError):
                validate_heartbeat_url(url)

    def test_http_readiness_and_manual_route(self):
        # Exercise the real HTTP parser/handler via an in-memory socket. No
        # network permission, port availability, or external services required.
        class Socket:
            def __init__(self, request):
                self.request = request
                self.response = b""
            def makefile(self, *args):
                return io.BytesIO(self.request)
            def sendall(self, data):
                self.response += data

        def request(method, path):
            sock = Socket(f"{method} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n".encode())
            handler_for(self.runner)(sock, ("127.0.0.1", 0), None)
            headers, body = sock.response.split(b"\r\n\r\n", 1)
            return int(headers.split(b" ")[1]), json.loads(body)

        self.assertEqual(request("GET", "/health")[0], 200)
        self.assertEqual(request("POST", "/run")[0], 400)
        with patch.object(w, "fetch", return_value=listing(movie="999")):
            code, body = request("POST", "/check")
        self.assertEqual(code, 200)
        self.assertEqual(body["trigger"], "manual")
        self.heartbeat.assert_not_called()


class HumanOutputTests(unittest.TestCase):
    def observation(self, **kwargs):
        data = {"status": "success", "checked_at": "2026-09-01T15:40:00+00:00",
                "seat_maps_checked": 2, "selectable_seats": 0, "preferred_blocks": 0}
        data.update(kwargs)
        return {"movies": {ST.movie_id: data}}

    def test_real_local_time_and_unavailable(self):
        line = w.status_lines(config(False), self.observation())[0]
        self.assertIn("10:40:00 AM CDT", line)
        self.assertIn("tickets unavailable in 2 checked showtimes", line)
        self.assertIn("no notification sent", line)

    def test_available_and_confirmed_notification(self):
        line = w.status_lines(config(False), self.observation(selectable_seats=3), {ST.movie_id: 1})[0]
        self.assertIn("tickets available", line)
        self.assertIn("notification sent (1 accepted by ntfy)", line)

    def test_available_already_known_not_new_notification(self):
        line = w.status_lines(config(False), self.observation(selectable_seats=3))[0]
        self.assertIn("tickets available", line)
        self.assertIn("no new qualifying alert", line)

    def test_failure_never_unavailable(self):
        line = w.status_lines(config(False), self.observation(status="failed"))[0]
        self.assertIn("CHECK FAILED", line)
        self.assertNotIn("tickets unavailable", line)

    def test_dry_run_never_sent(self):
        line = w.status_lines(config(False), self.observation(selectable_seats=3), dry_run=True)[0]
        self.assertIn("DRY RUN — no notification sent", line)

    def test_unpublished_not_seat_availability(self):
        line = w.status_lines(config(False), self.observation(seat_maps_checked=0,
                              dates_not_published=5, date_pages_checked=5))[0]
        self.assertIn("dates not published", line)
        self.assertNotIn("tickets unavailable", line)

    def test_known_showtimes_without_seat_check_unknown(self):
        line = w.status_lines(config(False), self.observation(seat_maps_checked=0, known_showtimes=4))[0]
        self.assertIn("seat maps not checked", line)

    def test_backoff_never_unavailable(self):
        line = w.status_lines(config(False), self.observation(status="backoff"))[0]
        self.assertIn("CHECK SKIPPED", line)
        self.assertNotIn("tickets unavailable", line)


class FirestoreAdapterTests(unittest.TestCase):
    def setUp(self):
        # Exercise the real adapter's transaction logic without cloud credentials.
        self.doc = {}
        self.tx = Mock()
        self.store = object.__new__(FirestoreStore)
        self.store.ref = "state-doc"
        self.store._transaction = lambda operation: operation(self.tx, copy.deepcopy(self.doc))
        self.tx.set.side_effect = lambda ref, data, merge: self.doc.update(data)
        self.tx.create.side_effect = lambda ref, data: self.doc.update(data)

    def test_acquire_and_busy(self):
        self.assertEqual(self.store.acquire("one"), {})
        self.assertIsNone(self.store.acquire("two"))

    def test_save_and_release(self):
        self.store.acquire("one")
        self.store.save("one", {"version": 3})
        self.assertEqual(json.loads(self.doc["state_json"]), {"version": 3})
        self.store.release("one", {"version": 3})
        self.assertIsNotNone(self.store.acquire("two"))

    def test_expired_owner_cannot_overwrite(self):
        self.store.acquire("one")
        self.doc["lease_until"] = w.utcnow()-timedelta(seconds=1)
        self.store.acquire("two")
        with self.assertRaises(LeaseLost):
            self.store.save("one", {})

    def test_seed_once_preserves_backoff_not_health(self):
        s = state()
        s["backoff_until"] = (w.utcnow()+timedelta(hours=1)).isoformat()
        s["movies"][ST.movie_id]["last_success_at"] = "old"
        self.store.seed(s)
        seeded = json.loads(self.doc["state_json"])
        self.assertIn("backoff_until", seeded)
        self.assertNotIn("last_success_at", seeded["movies"][ST.movie_id])
        with self.assertRaises(ValueError):
            self.store.seed(s)


if __name__ == "__main__":
    unittest.main()
