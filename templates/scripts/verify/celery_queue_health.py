#!/usr/bin/env python3
"""Celery broker and worker queue health check for local dev / verify scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")


def check_broker_ping() -> bool:
    try:
        import redis
    except ImportError:
        print("FAIL: redis package not installed", file=sys.stderr)
        return False

    url = _broker_url()
    try:
        client = redis.from_url(url, socket_connect_timeout=3)
        client.ping()
        print(f"OK: broker ping ({url})")
        return True
    except Exception as exc:
        print(f"FAIL: broker ping ({url}): {exc}", file=sys.stderr)
        return False


def check_worker_inspect() -> bool:
    try:
        from src.infrastructure.tasks.celery_worker_app import app
    except Exception as exc:
        print(f"FAIL: cannot import celery_worker_app: {exc}", file=sys.stderr)
        return False

    try:
        inspect = app.control.inspect(timeout=3.0)
        if inspect is None:
            print("FAIL: Celery inspect unavailable", file=sys.stderr)
            return False

        ping = inspect.ping()
        if not ping:
            print(
                "FAIL: no Celery workers responded (start with "
                "`docker compose --profile async up` or `just dev-celery`)",
                file=sys.stderr,
            )
            return False

        queues = inspect.active_queues() or {}
        queue_names: list[str] = []
        for worker_queues in queues.values():
            for entry in worker_queues:
                name = entry.get("name")
                if name:
                    queue_names.append(name)

        print(f"OK: workers={list(ping.keys())} queues={sorted(set(queue_names)) or ['celery']}")
        return True
    except Exception as exc:
        print(f"FAIL: Celery inspect: {exc}", file=sys.stderr)
        return False


def main() -> int:
    broker_ok = check_broker_ping()
    worker_ok = check_worker_inspect()
    if broker_ok and worker_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
