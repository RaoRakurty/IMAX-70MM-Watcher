"""Authenticate and validate a Cloudflare Cron workflow dispatch."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import os
from datetime import datetime, timezone


EVENT_NAME = "imax-ten-minute"


def parse_slot(raw: str) -> datetime:
    slot = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if slot.tzinfo is None:
        raise ValueError("scheduled slot must include a timezone")
    slot = slot.astimezone(timezone.utc)
    if slot.minute % 10 or slot.second or slot.microsecond:
        raise ValueError("scheduled slot must be on a UTC ten-minute boundary")
    return slot


def signature(secret: str, slot_text: str) -> str:
    if len(secret) < 32:
        raise ValueError("dispatch secret must contain at least 32 characters")
    message = f"{EVENT_NAME}:{slot_text}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def validate(slot_text: str, supplied: str, secret: str, now: datetime | None = None) -> datetime:
    slot = parse_slot(slot_text)
    expected = signature(secret, slot_text)
    if not hmac.compare_digest(expected, supplied):
        raise ValueError("invalid scheduler dispatch signature")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = (current - slot).total_seconds()
    if age < -60 or age > 300:
        raise ValueError(f"scheduler dispatch is outside the allowed delivery window ({age:.0f}s)")
    return slot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", required=True)
    parser.add_argument("--signature", required=True)
    args = parser.parse_args()
    slot = validate(args.slot, args.signature, os.environ.get("DISPATCH_HMAC_SECRET", ""))
    print(f"Authenticated Cloudflare Cron slot: {slot.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
