import io
import unittest
from datetime import datetime, timezone
from unittest import mock

import dispatch_guard
import healthcheck_ping


class DispatchGuardTests(unittest.TestCase):
    def setUp(self):
        self.secret = "s" * 32
        self.slot = "2026-08-31T20:40:00.000Z"
        self.now = datetime(2026, 8, 31, 20, 41, tzinfo=timezone.utc)

    def test_accepts_current_signed_slot(self):
        supplied = dispatch_guard.signature(self.secret, self.slot)
        self.assertEqual(dispatch_guard.validate(self.slot, supplied, self.secret, self.now).minute, 40)

    def test_rejects_bad_signature(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            dispatch_guard.validate(self.slot, "0" * 64, self.secret, self.now)

    def test_rejects_stale_or_off_grid_slot(self):
        stale = dispatch_guard.signature(self.secret, self.slot)
        with self.assertRaisesRegex(ValueError, "delivery window"):
            dispatch_guard.validate(self.slot, stale, self.secret, datetime(2026, 8, 31, 20, 50, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, "boundary"):
            dispatch_guard.parse_slot("2026-08-31T20:41:00Z")


class HealthcheckTests(unittest.TestCase):
    def test_rejects_non_healthchecks_url(self):
        with self.assertRaises(ValueError):
            healthcheck_ping.validate_url("https://example.com/token")

    @mock.patch("healthcheck_ping.urllib.request.build_opener")
    def test_success_ping_requires_ok(self, opener):
        response = mock.MagicMock(status=200)
        response.read.return_value = b"OK"
        response.__enter__.return_value = response
        opener.return_value.open.return_value = response
        healthcheck_ping.ping("https://hc-ping.com/12345678", "success")
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://hc-ping.com/12345678")

    @mock.patch("healthcheck_ping.urllib.request.build_opener")
    def test_start_ping_uses_start_endpoint(self, opener):
        response = mock.MagicMock(status=200)
        response.read.return_value = b"OK\n"
        response.__enter__.return_value = response
        opener.return_value.open.return_value = response
        healthcheck_ping.ping("https://hc-ping.com/12345678", "start")
        request = opener.return_value.open.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/start"))


if __name__ == "__main__":
    unittest.main()
