#!/usr/bin/env python3
"""Wait until the database host in DATABASE_URL accepts TCP connections."""

from __future__ import annotations

import os
import socket
import sys
import time
from urllib.parse import urlparse


def _parse_db_target(database_url: str) -> tuple[str, int]:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432

    if not host:
        raise ValueError("DATABASE_URL does not contain a valid host")

    return host, port


def _wait_for_tcp(host: str, port: int, timeout_seconds: int, interval_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    attempt = 1

    while True:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"Database is reachable at {host}:{port}")
                return
        except OSError as exc:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for database at {host}:{port}. Last error: {exc}"
                ) from exc
            print(f"Waiting for database at {host}:{port} (attempt {attempt})...")
            attempt += 1
            time.sleep(interval_seconds)


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2

    try:
        timeout_seconds = int(os.getenv("DB_WAIT_TIMEOUT_SECONDS", "180"))
        interval_seconds = float(os.getenv("DB_WAIT_INTERVAL_SECONDS", "2"))
        host, port = _parse_db_target(database_url)
    except Exception as exc:
        print(f"Invalid database wait configuration: {exc}", file=sys.stderr)
        return 2

    try:
        _wait_for_tcp(host, port, timeout_seconds, interval_seconds)
        return 0
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
