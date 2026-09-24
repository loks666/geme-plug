"""Turn off a GemeOpen smart plug and verify its reported state."""

from __future__ import annotations

import argparse
from pathlib import Path

from geme_plug import RequestTimeoutError, SmartPlug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="MQTT broker host; overrides .env")
    parser.add_argument("--port", type=int, help="MQTT broker port; overrides .env")
    parser.add_argument("--mac", help="Plug MAC address; overrides .env")
    parser.add_argument("--timeout", type=float, help="Response timeout; overrides .env")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with SmartPlug(
        host=args.host,
        port=args.port,
        mac=args.mac,
        timeout=args.timeout,
        username=args.username,
        password=args.password,
        env_file=args.env_file,
    ) as plug:
        try:
            before = plug.get_status()
            print(f"before: is_on={before.is_on}, ip={before.ip}, mac={before.mac}")
        except RequestTimeoutError:
            print("before: device did not answer the status query")

        plug.turn_off()
        print(f"sent OFF to {plug.publish_topic}")

        try:
            after = plug.get_status()
        except RequestTimeoutError as exc:
            raise SystemExit(f"OFF was published, but state verification timed out: {exc}") from exc

        print(f"after: is_on={after.is_on}, ip={after.ip}, mac={after.mac}")
        if after.is_on is not False:
            raise SystemExit("device did not report an OFF state")


if __name__ == "__main__":
    main()
