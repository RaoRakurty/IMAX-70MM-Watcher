import copy
import unittest
from datetime import datetime, timedelta, timezone
from verify_cadence import audit


class CadenceTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 9, 1, tzinfo=timezone.utc)
        self.records = []
        for i in range(144):
            slot = self.start+timedelta(minutes=10*i)
            self.records.append({"event": "check_completed", "trigger": "cloud_scheduler",
                                 "scheduled_at": slot.isoformat(),
                                 "started_at": (slot+timedelta(seconds=5)).isoformat(),
                                 "finished_at": (slot+timedelta(seconds=150)).isoformat(),
                                 "status": "success", "heartbeat_sent": True,
                                 "movies": {"104867": {"status": "success"}, "109913": {"status": "success"}}})

    def test_complete_24_hour_window(self):
        result = audit(self.records, self.start)
        self.assertTrue(result["passed"])
        self.assertEqual(result["successful_slots"], 144)
        self.assertEqual(result["maximum_completion_gap_seconds"], 600)

    def test_missing_run(self):
        result = audit(self.records[:10]+self.records[11:], self.start)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["missing_or_failed_slots"]), 1)

    def test_manual_cannot_fill_missing_slot(self):
        self.records[10]["trigger"] = "manual"
        self.assertFalse(audit(self.records, self.start)["passed"])

    def test_failed_or_partial_or_no_heartbeat_cannot_count(self):
        variants = [dict(status="failed"), dict(heartbeat_sent=False),
                    dict(movies={"109913": {"status": "failed"}}),
                    dict(movies={"109913": {"status": "success"}})]
        for change in variants:
            records = copy.deepcopy(self.records)
            records[10].update(change)
            self.assertFalse(audit(records, self.start)["passed"])

    def test_delayed_start(self):
        self.records[10]["started_at"] = (self.start+timedelta(minutes=100, seconds=125)).isoformat()
        result = audit(self.records, self.start)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["delayed_slots"]), 1)

    def test_duplicate_does_not_inflate_coverage(self):
        records = self.records[1:]+[self.records[1]]
        self.assertEqual(len(records), 144)
        result = audit(records, self.start)
        self.assertFalse(result["passed"])
        self.assertEqual(result["successful_slots"], 143)

    def test_cloud_logging_envelopes(self):
        self.assertTrue(audit([{"jsonPayload": r} for r in self.records], self.start)["passed"])


if __name__ == "__main__":
    unittest.main()
