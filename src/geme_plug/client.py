from __future__ import annotations

import json
import re
import threading
import uuid
from typing import Any

import paho.mqtt.client as mqtt

from .exceptions import ConnectionError, ProtocolError, RequestTimeoutError
from .models import PlugStatus, PowerStatus

_MAC_RE = re.compile(r"^[0-9a-f]{12}$")


def normalize_mac(mac: str) -> str:
    """Normalize a MAC address to 12 lowercase hexadecimal characters."""
    normalized = re.sub(r"[^0-9A-Fa-f]", "", mac).lower()
    if not _MAC_RE.fullmatch(normalized):
        raise ValueError(
            "mac must contain exactly 12 hexadecimal characters, "
            "for example 'AABBCCDDEEFF' or 'AA:BB:CC:DD:EE:FF'"
        )
    return normalized


class SmartPlug:
    """Synchronous MQTT client for GemeOpen GSPM1B-compatible smart plugs.

    The plug must already be configured to connect to the same MQTT broker and
    use the same publish/subscribe topics as this client.
    """

    def __init__(
        self,
        host: str,
        mac: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 5.0,
        publish_topic: str | None = None,
        subscribe_topic: str | None = None,
        client_id: str | None = None,
    ) -> None:
        if not host or not host.strip():
            raise ValueError("host cannot be empty")
        if port <= 0 or port > 65535:
            raise ValueError("port must be between 1 and 65535")
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if password is not None and username is None:
            raise ValueError("username is required when password is provided")

        self.host = host.strip()
        self.port = int(port)
        self.mac = normalize_mac(mac)
        self.username = username
        self.password = password
        self.timeout = float(timeout)

        # The SDK publishes commands to the topic subscribed to by the device,
        # and subscribes to the topic used by the device for responses.
        self.publish_topic = publish_topic or "request"
        self.subscribe_topic = subscribe_topic or "response"
        self.client_id = client_id or f"geme-plug-{self.mac}-{uuid.uuid4().hex[:8]}"

        self._connected = threading.Event()
        self._connect_error: str | None = None
        self._pending: dict[str, tuple[threading.Event, dict[str, Any] | None]] = {}
        self._pending_lock = threading.Lock()

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
            protocol=mqtt.MQTTv311,
        )
        if self.username is not None:
            self._client.username_pw_set(self.username, self.password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def connect(self) -> "SmartPlug":
        """Connect to the MQTT broker and subscribe to the plug response topic."""
        if self._connected.is_set():
            return self

        self._connect_error = None
        try:
            rc = self._client.connect(self.host, self.port, keepalive=60)
        except OSError as exc:
            raise ConnectionError(
                f"failed to connect to MQTT broker {self.host}:{self.port}: {exc}"
            ) from exc
        if rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(
                f"failed to connect to MQTT broker {self.host}:{self.port}: rc={rc}"
            )
        self._client.loop_start()

        if not self._connected.wait(self.timeout):
            self._client.loop_stop()
            try:
                self._client.disconnect()
            except Exception:
                pass
            detail = f": {self._connect_error}" if self._connect_error else ""
            raise ConnectionError(
                f"failed to connect to MQTT broker {self.host}:{self.port}{detail}"
            )
        return self

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if not self._connected.is_set():
            return
        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()
            self._connected.clear()

    def turn_on(self) -> None:
        """Turn the plug output on."""
        self._publish({"type": "event", "key": 1})

    def turn_off(self) -> None:
        """Turn the plug output off."""
        self._publish({"type": "event", "key": 0})

    def get_status(self) -> PlugStatus:
        """Query basic plug status."""
        payload = self._request({"type": "info"})
        return PlugStatus.from_payload(payload)

    def get_power(self) -> PowerStatus:
        """Query voltage, current, power, energy and switch state."""
        payload = self._request({"type": "statistic"})
        return PowerStatus.from_payload(payload)

    def __enter__(self) -> "SmartPlug":
        return self.connect()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.disconnect()

    def _ensure_connected(self) -> None:
        if not self._connected.is_set():
            raise ConnectionError("not connected; call plug.connect() first")

    def _publish(self, payload: dict[str, Any]) -> None:
        self._ensure_connected()
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        info = self._client.publish(self.publish_topic, encoded, qos=0, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(f"MQTT publish failed with rc={info.rc}")
        info.wait_for_publish(timeout=self.timeout)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_connected()
        message_id = uuid.uuid4().hex
        request = dict(payload)
        request["messageId"] = message_id
        event = threading.Event()

        with self._pending_lock:
            self._pending[message_id] = (event, None)

        try:
            self._publish(request)
            if not event.wait(self.timeout):
                raise RequestTimeoutError(
                    f"device {self.mac} did not respond within {self.timeout:g}s"
                )
            with self._pending_lock:
                _, response = self._pending.get(message_id, (event, None))
            if response is None:
                raise ProtocolError("device response was empty")
            return response
        finally:
            with self._pending_lock:
                self._pending.pop(message_id, None)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            self._connect_error = str(reason_code)
            return
        result, _ = client.subscribe(self.subscribe_topic, qos=0)
        if result != mqtt.MQTT_ERR_SUCCESS:
            self._connect_error = f"subscribe failed with rc={result}"
            return
        self._connected.set()

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        self._connected.clear()

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return

        message_id = payload.get("messageId")
        if message_id is None:
            return
        message_id = str(message_id)

        with self._pending_lock:
            pending = self._pending.get(message_id)
            if pending is None:
                return
            event, _ = pending
            self._pending[message_id] = (event, payload)
            event.set()
