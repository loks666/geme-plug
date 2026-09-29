"""Check the local broker and control a Geme smart plug.

Values come from .env and can be overridden with command-line options.
The default action only checks the broker; it does not switch the plug.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from geme_plug import GemePlugError, SmartPlug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="broker",
        choices=("broker", "status", "power", "on", "off"),
        help="broker only checks MQTT connectivity and is the safe default",
    )
    parser.add_argument("--host", help="MQTT broker host; overrides .env")
    parser.add_argument("--port", type=int, help="MQTT broker port; overrides .env")
    parser.add_argument("--username", help="MQTT username; overrides .env")
    parser.add_argument("--password", help="MQTT password; overrides .env")
    parser.add_argument("--mac", help="Plug MAC address; overrides .env")
    parser.add_argument("--publish-topic", help="SDK command topic; overrides .env")
    parser.add_argument("--subscribe-topic", help="SDK response topic; overrides .env")
    parser.add_argument("--timeout", type=float, help="Response timeout; overrides .env")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plug = SmartPlug(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        mac=args.mac,
        publish_topic=args.publish_topic,
        subscribe_topic=args.subscribe_topic,
        timeout=args.timeout,
        env_file=args.env_file,
    )

    try:
        with plug:
            if args.action == "broker":
                print(f"MQTT Broker 连接成功: {plug.host}:{plug.port}")
            elif args.action == "status":
                status = plug.get_status()
                print(
                    f"插座状态: {'打开' if status.is_on else '关闭'}, "
                    f"IP={status.ip}, MAC={status.mac}, 信号={status.signal}"
                )
            elif args.action == "power":
                power = plug.get_power()
                print(
                    f"电压={power.voltage} V, 电流={power.current} A, "
                    f"功率={power.power} W, 累计电量={power.energy} kWh"
                )
            elif args.action == "on":
                plug.turn_on()
                print("已发送打开命令")
            elif args.action == "off":
                plug.turn_off()
                print("已发送关闭命令")
    except (GemePlugError, OSError, ValueError) as exc:
        raise SystemExit(f"操作失败: {exc}") from exc


if __name__ == "__main__":
    main()
