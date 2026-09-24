import json
import os
import threading

import pytest

from geme_plug import PlugStatus, PowerStatus, SmartPlug, normalize_mac


def test_normalize_mac():
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aabbccddeeff"
    assert normalize_mac("aa-bb-cc-dd-ee-ff") == "aabbccddeeff"
    assert normalize_mac("AABBCCDDEEFF") == "aabbccddeeff"


@pytest.mark.parametrize("value", ["", "abc", "GG:BB:CC:DD:EE:FF", "AABBCCDDEEFF00"])
def test_normalize_mac_rejects_invalid(value):
    with pytest.raises(ValueError):
        normalize_mac(value)


def test_default_topics():
    plug = SmartPlug(host="127.0.0.1", mac="AA:BB:CC:DD:EE:FF", env_file=None)
    assert plug.publish_topic == "request"
    assert plug.subscribe_topic == "response"


def test_custom_topics():
    plug = SmartPlug(
        host="127.0.0.1",
        mac="AABBCCDDEEFF",
        publish_topic="custom/command",
        subscribe_topic="custom/state",
        env_file=None,
    )
    assert plug.publish_topic == "custom/command"
    assert plug.subscribe_topic == "custom/state"


def test_reads_defaults_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GEME_PLUG_HOST=192.0.2.10",
                "GEME_PLUG_PORT=1884",
                "GEME_PLUG_USERNAME=file-user",
                "GEME_PLUG_PASSWORD=file-password",
                "GEME_PLUG_MAC=11:22:33:44:55:66",
                "GEME_PLUG_PUBLISH_TOPIC=device/command",
                "GEME_PLUG_SUBSCRIBE_TOPIC=device/state",
                "GEME_PLUG_TIMEOUT=7.5",
            ]
        ),
        encoding="utf-8",
    )

    plug = SmartPlug(env_file=env_file)

    assert plug.host == "192.0.2.10"
    assert plug.port == 1884
    assert plug.username == "file-user"
    assert plug.password == "file-password"
    assert plug.mac == "112233445566"
    assert plug.publish_topic == "device/command"
    assert plug.subscribe_topic == "device/state"
    assert plug.timeout == pytest.approx(7.5)


def test_explicit_parameters_override_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GEME_PLUG_HOST=192.0.2.10",
                "GEME_PLUG_PORT=1884",
                "GEME_PLUG_USERNAME=file-user",
                "GEME_PLUG_PASSWORD=file-password",
                "GEME_PLUG_MAC=112233445566",
                "GEME_PLUG_PUBLISH_TOPIC=device/command",
                "GEME_PLUG_SUBSCRIBE_TOPIC=device/state",
                "GEME_PLUG_TIMEOUT=7.5",
            ]
        ),
        encoding="utf-8",
    )

    plug = SmartPlug(
        host="198.51.100.20",
        username="argument-user",
        env_file=env_file,
    )

    assert plug.host == "198.51.100.20"
    assert plug.username == "argument-user"
    assert plug.port == 1884
    assert plug.password == "file-password"
    assert plug.mac == "112233445566"
    assert plug.publish_topic == "device/command"
    assert plug.subscribe_topic == "device/state"
    assert plug.timeout == pytest.approx(7.5)


def test_process_environment_overrides_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEME_PLUG_HOST=192.0.2.10\nGEME_PLUG_MAC=112233445566\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEME_PLUG_HOST", "203.0.113.30")
    monkeypatch.setenv("GEME_PLUG_MAC", "AABBCCDDEEFF")

    plug = SmartPlug(env_file=env_file)

    assert plug.host == "203.0.113.30"
    assert plug.mac == "aabbccddeeff"


def test_missing_required_settings(tmp_path, monkeypatch):
    for name in list(os.environ):
        if name.startswith("GEME_PLUG_"):
            monkeypatch.delenv(name)

    with pytest.raises(ValueError, match="GEME_PLUG_HOST"):
        SmartPlug(env_file=tmp_path / "missing.env")


def test_status_model():
    status = PlugStatus.from_payload(
        {
            "mac": "aabbccddeeff",
            "type": "Socket-mini",
            "version": "2.0.0",
            "key": 1,
            "wifiLock": 0,
            "keyLock": 0,
            "signal": -55,
            "onState": 1,
            "timerEnable": 1,
            "timerInterval": 60,
            "ip": "192.168.31.123",
            "ssid": "wifi",
            "messageId": "abc",
        }
    )
    assert status.is_on is True
    assert status.device_type == "Socket-mini"
    assert status.ip == "192.168.31.123"


def test_power_model():
    power = PowerStatus.from_payload(
        {
            "mac": "aabbccddeeff",
            "voltage": 226.024,
            "current": 1.027,
            "power": 232.511,
            "energy": 25.047,
            "key": 1,
            "messageId": "abc",
        }
    )
    assert power.voltage == pytest.approx(226.024)
    assert power.energy == pytest.approx(25.047)
    assert power.is_on is True


class _PublishInfo:
    rc = 0

    def wait_for_publish(self, timeout=None):
        return None


class _FakeClient:
    def __init__(self, plug):
        self.plug = plug
        self.published = []

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload))
        data = json.loads(payload)
        if data["type"] in {"info", "statistic"}:
            response = {"messageId": data["messageId"], "mac": self.plug.mac}
            if data["type"] == "info":
                response.update({"type": "Socket-mini", "key": 1, "ip": "192.168.31.9"})
            else:
                response.update({"voltage": 220.0, "current": 0.5, "power": 110.0, "energy": 1.25, "key": 1})

            class Message:
                payload = json.dumps(response).encode()

            threading.Timer(0.01, lambda: self.plug._on_message(self, None, Message())).start()
        return _PublishInfo()


def test_request_response_flow():
    plug = SmartPlug(
        host="127.0.0.1", mac="AABBCCDDEEFF", timeout=1, env_file=None
    )
    plug._connected.set()
    plug._client = _FakeClient(plug)

    status = plug.get_status()
    power = plug.get_power()

    assert status.device_type == "Socket-mini"
    assert status.ip == "192.168.31.9"
    assert power.power == pytest.approx(110.0)
