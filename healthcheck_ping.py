"""Send a strict Healthchecks.io start or success ping."""
from __future__ import annotations

import argparse
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(raw: str) -> str:
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme != "https" or parsed.hostname != "hc-ping.com" or not parsed.path.strip("/"):
        raise ValueError("HC_PING_URL must be https://hc-ping.com/<uuid>")
    if parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.port:
        raise ValueError("HC_PING_URL contains unsupported URL components")
    return raw.rstrip("/")


def ping(raw: str, event: str, timeout: float = 10) -> None:
    base = validate_url(raw)
    url = base if event == "success" else f"{base}/start"
    request = urllib.request.Request(url, method="POST", headers={"User-Agent": "imax-watcher/1"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
            body = response.read(16)
            if response.status != 200 or body.strip() != b"OK":
                raise RuntimeError(f"heartbeat rejected with HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"heartbeat rejected with HTTP {exc.code}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=("start", "success"))
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    ping(args.url, args.event)
    print(f"Healthchecks {args.event} ping accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
