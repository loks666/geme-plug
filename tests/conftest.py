"""Small paho-mqtt stub so protocol/unit tests can run in offline CI sandboxes.

Real installations use the declared paho-mqtt dependency.
"""

import sys
import types


if "paho.mqtt.client" not in sys.modules:
    paho = types.ModuleType("paho")
    mqtt_pkg = types.ModuleType("paho.mqtt")
    client_mod = types.ModuleType("paho.mqtt.client")

    class _CallbackAPIVersion:
        VERSION2 = 2

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def username_pw_set(self, *args, **kwargs):
            pass

    client_mod.Client = _Client
    client_mod.CallbackAPIVersion = _CallbackAPIVersion
    client_mod.MQTTv311 = 4
    client_mod.MQTT_ERR_SUCCESS = 0

    paho.mqtt = mqtt_pkg
    mqtt_pkg.client = client_mod
    sys.modules["paho"] = paho
    sys.modules["paho.mqtt"] = mqtt_pkg
    sys.modules["paho.mqtt.client"] = client_mod
