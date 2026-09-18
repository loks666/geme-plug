from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlugStatus:
    mac: str
    device_type: str | None = None
    version: str | None = None
    key: int | None = None
    wifi_lock: int | None = None
    key_lock: int | None = None
    signal: int | None = None
    on_state: int | None = None
    timer_enable: int | None = None
    timer_interval: int | None = None
    ip: str | None = None
    ssid: str | None = None
    message_id: str | None = None

    @property
    def is_on(self) -> bool | None:
        if self.key is None:
            return None
        return self.key == 1

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PlugStatus":
        return cls(
            mac=str(payload.get("mac", "")),
            device_type=payload.get("type"),
            version=payload.get("version"),
            key=_to_int(payload.get("key")),
            wifi_lock=_to_int(payload.get("wifiLock")),
            key_lock=_to_int(payload.get("keyLock")),
            signal=_to_int(payload.get("signal")),
            on_state=_to_int(payload.get("onState")),
            timer_enable=_to_int(payload.get("timerEnable")),
            timer_interval=_to_int(payload.get("timerInterval")),
            ip=payload.get("ip"),
            ssid=payload.get("ssid"),
            message_id=_to_str_or_none(payload.get("messageId")),
        )


@dataclass(frozen=True)
class PowerStatus:
    mac: str
    voltage: float | None = None
    current: float | None = None
    power: float | None = None
    energy: float | None = None
    key: int | None = None
    message_id: str | None = None

    @property
    def is_on(self) -> bool | None:
        if self.key is None:
            return None
        return self.key == 1

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PowerStatus":
        return cls(
            mac=str(payload.get("mac", "")),
            voltage=_to_float(payload.get("voltage")),
            current=_to_float(payload.get("current")),
            power=_to_float(payload.get("power")),
            energy=_to_float(payload.get("energy")),
            key=_to_int(payload.get("key")),
            message_id=_to_str_or_none(payload.get("messageId")),
        )


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
