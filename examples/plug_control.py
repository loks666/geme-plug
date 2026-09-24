"""Check the local broker and control a Geme smart plug.

Values come from .env and can be overridden with command-line options.
The default action only checks the broker; it does not switch the plug.
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from geme_plug import GemePlugError, SmartPlug


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def parse_args() -> argparse.Namespace:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="broker",
        choices=("broker", "status", "power", "on", "off"),
        help="broker only checks MQTT connectivity and is the safe default",
    )
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=_env_int("MQTT_PORT", 1883))
    parser.add_argument("--username", default=os.getenv("MQTT_USERNAME"))
    parser.add_argument("--password", default=os.getenv("MQTT_PASSWORD"))
    parser.add_argument("--mac", default=os.getenv("PLUG_MAC", "8CCE4E51ACAB"))
    parser.add_argument(
        "--publish-topic",
        default=os.getenv("PLUG_PUBLISH_TOPIC", "response"),
    )
    parser.add_argument(
        "--subscribe-topic",
        default=os.getenv("PLUG_SUBSCRIBE_TOPIC", "request"),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_env_float("PLUG_TIMEOUT", 10.0),
    )
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
    )

    try:
        with plug:
            if args.action == "broker":
                print(f"MQTT Broker 连接成功: {args.host}:{args.port}")
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
