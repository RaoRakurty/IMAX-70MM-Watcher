"""Offline checks for movie priority and inclusive monitoring end dates."""
import copy
import io
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from unittest.mock import patch

import watcher as w
from test_reliability import THEATER, listing


class MonitoringPriorityTests(unittest.TestCase):
    def setUp(self):
        self.config = w.load_json(w.CONFIG_PATH)
        self.odyssey = next(m for m in self.config["movies"] if m["short_name"] == "ODYSSEY")
        self.dune = next(m for m in self.config["movies"] if m["short_name"] == "DUNE")
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_date_rotation_stops_at_inclusive_end_despite_window_shift(self):
        state = {"initialized": True, "date_probe_cursor": 25,
                 "active_window_start": "2026-09-01"}
        self.assertEqual(w.scan_dates_for_movie(self.odyssey, state, date(2026, 9, 16)),
                         [date(2026, 9, 16), date(2026, 9, 17)])
        self.assertEqual(w.scan_dates_for_movie(self.odyssey, state, date(2026, 9, 17)),
                         [date(2026, 9, 17)])
        for day in (date(2026, 9, 18), date(2026, 10, 1)):
            self.assertEqual(w.scan_dates_for_movie(self.odyssey, state, day), [])

    def test_narrowed_range_resets_out_of_range_bootstrap_cursor(self):
        state = {"initialized": False, "bootstrap_next_date": "2026-09-25", "showtimes": {}}
        with patch.object(w, "fetch", return_value=listing(day=date(2026, 9, 17), movie="999")):
            first, shows = w.discover_movie(self.odyssey, state, THEATER, {}, date(2026, 9, 17))
        self.assertTrue(first)
        self.assertTrue(state["initialized"])
        self.assertEqual(shows, [])

    def test_legacy_discovery_and_baseline_honor_end(self):
        cfg = copy.deepcopy(self.odyssey)
        cfg.pop("monitoring_start")
        cfg["bootstrap_end"] = "2026-09-30"
        state = {"initialized": False, "showtimes": {}}
        with patch.object(w, "fetch", return_value=listing(day=date(2026, 9, 17), movie="999")):
            w.discover_movie(cfg, state, THEATER, {}, date(2026, 9, 17))
        self.assertTrue(state["initialized"])
        state["showtimes"]["later"] = {"iso": "2026-09-25T19:15:00"}
        self.assertTrue(all(d <= date(2026, 9, 17)
                            for d in w.scan_dates_for_movie(cfg, state, date(2026, 9, 16))))

    def test_cached_new_pending_and_pinned_showtimes_cannot_escape_cutoff(self):
        cfg = copy.deepcopy(self.odyssey)
        cfg["seed_showtimes"] = [{"showtime_id": "later", "iso": "2026-09-18T15:15:00"}]
        state = {"showtimes": {
            "last": {"theater_id": "207", "iso": "2026-09-17T22:59:00"},
            "later": {"theater_id": "207", "iso": "2026-09-18T15:15:00"},
        }, "pending_seat_checks": ["later"], "pending_notification_checks": ["later"]}
        selected = w.select_showtimes_to_poll(cfg, state, date(2026, 9, 4), {"later"})
        self.assertEqual([s.showtime_id for s in selected], ["last"])
        self.assertEqual(state["pending_seat_checks"], [])

    def test_after_midnight_spillover_beyond_end_is_not_discovered(self):
        page = listing(day=date(2026, 9, 17)).replace("Showtime=2026-09-17T19:15:00",
                                                    "Showtime=2026-09-18T02:00:00")
        state = {"initialized": True, "showtimes": {}}
        with patch.object(w, "fetch", return_value=page):
            _, shows = w.discover_movie(self.odyssey, state, THEATER, {}, date(2026, 9, 17))
        self.assertEqual(shows, [])
        self.assertEqual(state["showtimes"], {})

    def test_dune_pin_is_first_even_when_new_showtimes_fill_budget(self):
        cfg = copy.deepcopy(self.dune)
        state = {"showtimes": {str(n): {"theater_id": "207", "iso": "2026-12-17T10:00:00"}
                               for n in range(30)}}
        new_ids = set(state["showtimes"])
        w.seed_configured_showtimes(cfg, state, THEATER)
        selected = w.select_showtimes_to_poll(cfg, state, date(2026, 9, 4), new_ids)
        self.assertEqual(len(selected), 20)
        self.assertEqual(selected[0].showtime_id, "644486")

    def test_odyssey_rotation_has_reduced_budget(self):
        state = {"showtimes": {str(n): {"theater_id": "207", "iso": "2026-09-17T10:00:00"}
                               for n in range(12)}}
        first = w.select_showtimes_to_poll(self.odyssey, state, date(2026, 9, 4), set())
        second = w.select_showtimes_to_poll(self.odyssey, state, date(2026, 9, 4), set())
        self.assertEqual(len(first), 4)
        self.assertEqual(len(second), 4)
        self.assertFalse({s.showtime_id for s in first} & {s.showtime_id for s in second})

    def test_dune_completes_before_odyssey_rate_limit(self):
        order = []
        def discover(movie, state, *_):
            order.append(movie["short_name"])
            if movie["short_name"] == "ODYSSEY":
                raise w.CinemarkBackoff("HTTP 429", 21600)
            state["initialized"] = True
            state["date_observations"] = []
            return False, []
        now = datetime(2026, 9, 4, 3, tzinfo=timezone.utc)
        with patch.object(w, "utcnow", return_value=now), \
                patch.object(w, "discover_movie", side_effect=discover), \
                patch.object(w, "poll_seats_and_alert"):
            result = w.run_once(self.config, {})
        self.assertEqual(order, ["DUNE", "ODYSSEY"])
        self.assertEqual(result["movies"]["109913"]["status"], "success")
        self.assertEqual(result["movies"]["104867"]["status"], "backoff")
        self.assertEqual(result["status"], "failed")

    def test_end_uses_dallas_midnight_and_dune_continues(self):
        for hour, expected in ((4, ["DUNE", "ODYSSEY"]), (5, ["DUNE"])):
            with self.subTest(utc_hour=hour):
                order = []
                def discover(movie, state, *_):
                    order.append(movie["short_name"])
                    state["initialized"] = True
                    state["date_observations"] = []
                    return False, []
                now = datetime(2026, 9, 18, hour, tzinfo=timezone.utc)
                with patch.object(w, "utcnow", return_value=now), \
                        patch.object(w, "discover_movie", side_effect=discover), \
                        patch.object(w, "poll_seats_and_alert"):
                    result = w.run_once(self.config, {})
                self.assertEqual(order, expected)
                self.assertEqual(result["status"], "success")
                if hour == 5:
                    self.assertEqual(result["movies"]["104867"]["status"], "inactive")
                    line = w.status_lines(self.config, result)[1]
                    self.assertIn("MONITORING ENDED: through 2026-09-17", line)
                    self.assertNotIn("tickets unavailable", line)

    def test_cutoff_cancels_out_of_range_alerts_without_bypassing_backoff(self):
        now = datetime(2026, 9, 4, 3, tzinfo=timezone.utc)
        state = {"backoff_until": "2026-09-04T03:33:21+00:00", "movies": {
            "104867": {"showtimes": {"later": {"iso": "2026-09-18T19:15:00"}}}
        }, "outbox": [{"movie_id": "104867", "showtime_id": "later", "id": "old"}]}
        with patch.object(w, "utcnow", return_value=now), patch.object(w, "fetch") as fetch:
            result = w.run_once(self.config, state)
        fetch.assert_not_called()
        self.assertEqual(result["status"], "backoff")
        self.assertEqual(state["backoff_until"], "2026-09-04T03:33:21+00:00")
        self.assertEqual(state["outbox"], [])
        self.assertEqual(state["cancelled_alerts"], 1)

    def test_inactive_odyssey_does_not_hide_dune_failure(self):
        now = datetime(2026, 9, 18, 5, tzinfo=timezone.utc)
        with patch.object(w, "utcnow", return_value=now), \
                patch.object(w, "fetch", side_effect=TimeoutError("unavailable")):
            result = w.run_once(self.config, {})
        self.assertEqual(result["movies"]["104867"]["status"], "inactive")
        self.assertEqual(result["movies"]["109913"]["status"], "failed")
        self.assertEqual(result["status"], "failed")

    def test_end_before_start_is_rejected(self):
        cfg = dict(self.odyssey, monitoring_end="2026-08-31")
        with self.assertRaises(w.ScanError):
            w.monitoring_window(cfg, date(2026, 9, 4))


if __name__ == "__main__":
    unittest.main()
