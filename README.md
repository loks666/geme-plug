# geme-plug

`geme-plug` 是一个用于 **GemeOpen / GeekOpen GSPM1B 智能插座** 的 Python MQTT SDK，面向自建 MQTT Broker（例如 EMQX）。

> 本项目是第三方开源 SDK，与 GemeOpen / 武汉智鸟科技无隶属关系。

## 安装

```bash
pip install geme-plug
```

## 快速开始

```python
from geme_plug import SmartPlug

plug = SmartPlug(
    host="192.168.31.100",   # EMQX Broker IP / hostname
    mac="AABBCCDDEEFF",
)

plug.connect()

plug.turn_on()
plug.turn_off()

print(plug.get_status())
print(plug.get_power())

plug.disconnect()
```

也支持上下文管理器：

```python
from geme_plug import SmartPlug

with SmartPlug(host="192.168.31.100", mac="AA:BB:CC:DD:EE:FF") as plug:
    plug.turn_on()
    print(plug.get_power())
```

## EMQX 认证

EMQX 未开启 MQTT 客户端认证时，只需要 `host` 和 `mac`。

开启认证后：

```python
plug = SmartPlug(
    host="192.168.31.100",
    mac="AABBCCDDEEFF",
    username="geme",
    password="your-password",
)
```

`port` 默认是 `1883`。

## 使用 Docker Compose 启动 EMQX

仓库内置了与以下 `docker run` 配置等价的 `compose.yaml`：

```bash
docker compose up -d
```

- MQTT Broker：`mqtt://<本机局域网 IP>:1883`
- EMQX Dashboard：`http://127.0.0.1:18083`

设备必须连接到运行 EMQX 的电脑的局域网 IP，不能使用设备视角下的
`127.0.0.1`。EMQX Dashboard 的初始登录信息请以当前镜像的启动页提示为准，
首次登录后应立即修改密码。

## 关断测试

确认设备已经连到该 Broker 后，可运行：

```bash
python examples/turn_off.py \
  --host <运行 EMQX 的局域网 IP> \
  --mac <插座 MAC 地址>
```

脚本先查询当前状态，再发布关断指令，最后重新查询并验证设备报告为关闭。

## 设备 MQTT 配置

在使用 SDK 前，插座必须已经：

1. 完成 2.4 GHz Wi-Fi 配网；
2. 配置为连接你的 MQTT Broker / EMQX；
3. 配置与 SDK 一致的 MQTT Topic。

`geme-plug` 默认使用规范化后的**小写 MAC**生成 Topic：

```text
/geme/{mac}/publish
/geme/{mac}/subscribe
```

例如 MAC 为 `AA:BB:CC:DD:EE:FF`：

```text
/geme/aabbccddeeff/publish
/geme/aabbccddeeff/subscribe
```

在 GemeOpen 的“自定义 MQTT”配置中，应让控制/发布主题和上报/订阅主题与这里保持一致。

如果你已经给设备配置了其他 Topic，可以显式覆盖：

```python
plug = SmartPlug(
    host="192.168.31.100",
    mac="AABBCCDDEEFF",
    publish_topic="my/device/command",
    subscribe_topic="my/device/state",
)
```

## API

### `SmartPlug(...)`

```python
SmartPlug(
    host: str,
    mac: str,
    port: int = 1883,
    username: str | None = None,
    password: str | None = None,
    timeout: float = 5.0,
    publish_topic: str | None = None,
    subscribe_topic: str | None = None,
    client_id: str | None = None,
)
```

MAC 可以使用以下任意格式：

```text
AABBCCDDEEFF
AA:BB:CC:DD:EE:FF
AA-BB-CC-DD-EE-FF
```

SDK 内部统一规范化为 `aabbccddeeff`。

### `connect()` / `disconnect()`

连接或断开 MQTT Broker。

### `turn_on()` / `turn_off()`

控制插座通断电。SDK 根据 GSPM1B 协议发送：

```json
{"type":"event","key":1}
```

或：

```json
{"type":"event","key":0}
```

### `get_status()`

查询设备状态，返回 `PlugStatus`，常用字段包括：

- `mac`
- `device_type`
- `version`
- `key` / `is_on`
- `signal`
- `ip`
- `ssid`
- `wifi_lock`
- `key_lock`
- `on_state`
- `timer_enable`
- `timer_interval`

### `get_power()`

查询电量数据，返回 `PowerStatus`：

- `voltage`：V
- `current`：A
- `power`：W
- `energy`：kWh
- `key` / `is_on`

## 说明

本版本聚焦于最基础、稳定的控制能力：连接 Broker、通断控制、状态查询和电量查询。设备配网和局域网自动发现暂不包含在 `1.0.0` 中。

## License

MIT
