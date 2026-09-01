"""Private Cloud Run endpoint: respond success only AFTER a validated check.

Cloud Run IAM must restrict invocation to the dedicated Cloud Scheduler service
account. Scheduler headers identify an execution; they are NOT authentication.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import watcher
from state_store import FirestoreStore


@dataclass(frozen=True)
class Settings:
    project: str
    scheduler_job: str
    topic: str
    heartbeat_url: str
    database: str = "imax-watcher"
    max_seconds: int = 270

    @classmethod
    def from_env(cls):
        keys = ("GCP_PROJECT_ID", "EXPECTED_SCHEDULER_JOB", "NTFY_TOPIC", "HC_PING_URL")
        missing = [key for key in keys if not os.environ.get(key)]
        if missing:
            raise ValueError("Missing required settings: " + ", ".join(missing))
        settings = cls(*(os.environ[key] for key in keys),
                       database=os.environ.get("FIRESTORE_DATABASE", "imax-watcher"))
        validate_heartbeat_url(settings.heartbeat_url)
        return settings


def validate_heartbeat_url(url: str):
    if not re.fullmatch(r"https://hc-ping\.com/[0-9a-fA-F-]{36}", url):
        raise ValueError("HC_PING_URL must be the HTTPS UUID ping URL from Healthchecks.io")
    uuid.UUID(url.rsplit("/", 1)[1])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected heartbeat redirect")


def send_heartbeat(url: str):
    validate_heartbeat_url(url)
    request = urllib.request.Request(url, data=b"", method="POST",
                                     headers={"User-Agent": "imax-watcher/3.0"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=10) as response:
        if response.status != 200 or response.read(16).strip() != b"OK":
            raise RuntimeError("Heartbeat was not acknowledged")


def scheduled_slot(headers, expected_job: str, now=None) -> str:
    if headers.get("X-CloudScheduler-JobName") != expected_job:
        raise ValueError("Unexpected scheduler job")
    raw = headers.get("X-CloudScheduler-ScheduleTime", "")
    try:
        scheduled = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if scheduled.tzinfo is None:
            raise ValueError("Timezone required")
        scheduled = scheduled.astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError("Missing or invalid scheduler timestamp") from exc
    now = now or watcher.utcnow()
    if not -60 <= (now - scheduled).total_seconds() <= 300:
        raise ValueError("Scheduler timestamp outside allowed delivery/retry window")
    if scheduled.minute % 10 or scheduled.second or scheduled.microsecond:
        raise ValueError("Timestamp is not a configured ten-minute schedule slot")
    return scheduled.isoformat()


class Runner:
    def __init__(self, config: dict, settings: Settings, store, heartbeat=send_heartbeat):
        self.config, self.settings, self.store = config, settings, store
        self.heartbeat = heartbeat

    def execute(self, scheduled_at: str | None, trigger: str = "cloud_scheduler") -> tuple[int, dict]:
        owner = uuid.uuid4().hex
        state = self.store.acquire(owner)
        if state is None:
            return 409, {"status": "busy"}
        previous = state.get("last_run", {})
        if trigger == "cloud_scheduler" and previous.get("scheduled_at") == scheduled_at and previous.get("heartbeat_sent"):
            self.store.release(owner, state)
            # Retried delivery is not a new check. Never refresh health here.
            return 200, {"status": "duplicate", "run_id": previous["run_id"]}
        run = {"event": "check_completed", "run_id": owner,
               "trigger": trigger, "scheduled_at": scheduled_at,
               "started_at": watcher.utcnow().isoformat(), "heartbeat_sent": False}
        token = watcher.DEADLINE.set(time.monotonic() + self.settings.max_seconds)
        http_status = 503
        delivery = {}
        try:
            scan = watcher.run_once(self.config, state)
            run.update(status=scan["status"], movies=scan["movies"])
            # Persist observations AND notification outbox atomically first.
            self.store.save(owner, state)
            try:
                run["notifications_sent"] = watcher.flush_outbox(
                    state, lambda obj: self.store.save(owner, obj), self.settings.topic, delivery=delivery)
            except Exception as exc:
                run["notification_error"] = type(exc).__name__
                raise
            if scan["status"] == "success":
                http_status = 200
        except Exception as exc:
            # Exception messages from HTTP clients may contain secret URLs.
            run.update(status="failed", error_type=type(exc).__name__)
        finally:
            watcher.DEADLINE.reset(token)
        run["finished_at"] = watcher.utcnow().isoformat()
        run["notifications_sent_by_movie"] = delivery
        run["status_lines"] = watcher.status_lines(self.config, run, delivery)
        state["last_run"] = run
        state.setdefault("run_history", []).append(run)
        state["run_history"] = state["run_history"][-288:]
        # If durable state fails, the exception escapes and NO heartbeat is sent.
        self.store.save(owner, state)
        if http_status == 200 and trigger == "cloud_scheduler":
            try:
                self.heartbeat(self.settings.heartbeat_url)
                run["heartbeat_sent"] = True
            except Exception as exc:
                run.update(status="heartbeat_failed", error_type=type(exc).__name__)
                http_status = 503
        self.store.release(owner, state)
        print(json.dumps(run, sort_keys=True), flush=True)
        return http_status, run


def handler_for(runner: Runner):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, body):
            payload = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            # Readiness only. This never advances scan health.
            self.respond(200 if self.path == "/health" else 404,
                         {"ready": True} if self.path == "/health" else {"error": "not found"})

        def do_POST(self):
            if self.path not in ("/run", "/check"):
                self.respond(404, {"error": "not found"})
                return
            try:
                slot = scheduled_slot(self.headers, runner.settings.scheduler_job) if self.path == "/run" else None
            except ValueError:
                self.respond(400, {"error": "invalid scheduler envelope"})
                return
            try:
                status, result = runner.execute(slot, "cloud_scheduler" if self.path == "/run" else "manual")
            except Exception as exc:
                # Redact URL/body/credentials, including traceback output.
                print(json.dumps({"event": "check_error", "error_type": type(exc).__name__}), flush=True)
                status, result = 503, {"status": "failed", "error_type": type(exc).__name__}
            self.respond(status, result)

        def log_message(self, format, *args):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-state", help="Import baseline into an EMPTY Firestore document, then exit")
    args = parser.parse_args()
    if args.seed_state:
        store = FirestoreStore(os.environ["GCP_PROJECT_ID"], os.environ.get("FIRESTORE_DATABASE", "imax-watcher"))
        from pathlib import Path
        store.seed(watcher.load_json(Path(args.seed_state)))
        print("Baseline imported; no health signal sent")
        return
    settings = Settings.from_env()
    runner = Runner(watcher.load_json(watcher.CONFIG_PATH), settings,
                    FirestoreStore(settings.project, settings.database))
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0" if "PORT" in os.environ else "127.0.0.1", port), handler_for(runner)).serve_forever()


if __name__ == "__main__":
    main()
