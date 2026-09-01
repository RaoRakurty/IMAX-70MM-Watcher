"""Audit exported Cloud Run JSON logs. Manual/test runs cannot fill schedule slots.

Use trusted Cloud Logging exports and exclude any interval with manual Scheduler
RunJob calls, as described in DEPLOYMENT.md. Local test data is not live proof.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def timestamp(raw):
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Timestamps must include timezone")
    return value.astimezone(timezone.utc)


def audit(records, start, hours=24, expected_movie_ids=("104867", "109913")):
    if start.tzinfo is None or start.minute % 10 or start.second or start.microsecond or hours < 1:
        raise ValueError("Window must start on a ten-minute boundary and span at least one hour")
    start = start.astimezone(timezone.utc)
    slots = [start+timedelta(minutes=i*10) for i in range(hours*6)]
    by_slot = {}
    ignored = 0
    for record in records:
        run = record.get("jsonPayload", record)
        if run.get("event") != "check_completed" or run.get("trigger") != "cloud_scheduler":
            ignored += 1
            continue
        try:
            slot = timestamp(run["scheduled_at"])
            began, ended = timestamp(run["started_at"]), timestamp(run["finished_at"])
            healthy = run.get("status") == "success" and run.get("heartbeat_sent") is True
            healthy = healthy and set(run.get("movies", {})) == set(expected_movie_ids) and all(m.get("status") == "success" for m in run["movies"].values())
            if healthy and slot <= began <= ended and slot in slots:
                # Use first successfully completed attempt per schedule slot.
                if slot not in by_slot or ended < by_slot[slot][1]:
                    by_slot[slot] = (began, ended)
        except (ValueError, KeyError, TypeError):
            ignored += 1
    missing = [slot.isoformat() for slot in slots if slot not in by_slot]
    delayed = [slot.isoformat() for slot, (began, ended) in by_slot.items()
               if (began-slot).total_seconds() > 120 or (ended-slot).total_seconds() > 300]
    completions = sorted(ended for _, ended in by_slot.values())
    gaps = [(b-a).total_seconds() for a, b in zip(completions, completions[1:])]
    maximum_gap = max(gaps) if gaps else None
    return {"passed": not missing and not delayed and maximum_gap is not None and maximum_gap <= 900,
            "window_start": start.isoformat(), "hours": hours, "expected_slots": len(slots),
            "successful_slots": len(by_slot), "missing_or_failed_slots": missing,
            "delayed_slots": sorted(delayed), "maximum_completion_gap_seconds": maximum_gap,
            "ignored_records": ignored,
            "runs": [{"scheduled_at": slot.isoformat(), "started_at": began.isoformat(),
                      "finished_at": ended.isoformat(), "status": "success"}
                     for slot, (began, ended) in sorted(by_slot.items())]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_file", type=Path)
    parser.add_argument("--start", required=True, help="UTC ten-minute boundary, e.g. 2026-09-01T00:00:00Z")
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    raw = args.log_file.read_text()
    records = json.loads(raw) if raw.lstrip().startswith("[") else [json.loads(line) for line in raw.splitlines() if line.strip()]
    result = audit(records, timestamp(args.start), args.hours)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
