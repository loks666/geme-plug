# geme-plug

`geme-plug` 是一个用于 GemeOpen / GeekOpen GSPM1B 智能插座的 Python MQTT SDK，支持：

- 打开、关闭插座；
- 查询开关状态和设备信息；
- 查询电压、电流、功率和累计电量；
- 连接启用账号认证的 EMQX 等 MQTT Broker；
- 自定义 MQTT 发布和订阅主题。
- 默认从 `.env` 读取配置，并允许构造函数参数覆盖。

> 本项目是第三方开源 SDK，与 GemeOpen 或设备厂商没有隶属关系。

## 新环境快速开始

下面以 Windows PowerShell 为例。新电脑不需要先安装本仓库源码，只要有 Python 3.10 以上版本并且能够访问 MQTT Broker 即可。

### 第一步：创建独立目录和虚拟环境

```powershell
mkdir geme-plug-test
cd geme-plug-test
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果 PowerShell 禁止运行激活脚本，也可以不激活环境，后续始终使用 `.\.venv\Scripts\python.exe`。

### 第二步：从 PyPI 安装 SDK

```powershell
python -m pip install geme-plug
python -c "import geme_plug; print(geme_plug.__version__)"
```

不激活环境时使用：

```powershell
.\.venv\Scripts\python.exe -m pip install geme-plug
```

### 第三步：配置插座网页

在插座的自定义 MQTT 页面填写：

| 网页字段 | 填写内容 |
| --- | --- |
| Broker / Server / Host | EMQX 所在电脑的局域网 IP，例如 `192.168.50.70` |
| Port | `1883` |
| Username | EMQX 分配的 MQTT 用户名 |
| Password | 对应的 MQTT 密码 |

不要在 Broker 字段中填写 `mqtt://`，也不要把端口拼在 IP 后面。`1883` 是普通 MQTT over TCP；如果网页另有 SSL/TLS 开关，应保持关闭。保存后让插座重启并重新联网。

只有这四项也可以配置该型号：设备 Client ID 和主题由固件处理。当前已测试设备订阅 `response`、发布 `request`。插座仍需先完成 Wi-Fi 配网，并能访问 Broker 的 TCP `1883` 端口。

### 第四步：创建 `.env`

在运行 Python 的目录中新建 `.env`：

```dotenv
GEME_PLUG_HOST=192.168.50.70
GEME_PLUG_PORT=1883
GEME_PLUG_USERNAME=<MQTT_USERNAME>
GEME_PLUG_PASSWORD=<MQTT_PASSWORD>
GEME_PLUG_MAC=<PLUG_MAC_ADDRESS>
GEME_PLUG_PUBLISH_TOPIC=response
GEME_PLUG_SUBSCRIBE_TOPIC=request
GEME_PLUG_TIMEOUT=10
```

仓库用户也可以复制 `.env.example` 后再修改：

```powershell
Copy-Item .env.example .env
```

`.env` 已被 Git 忽略，不要提交账号密码。MAC 地址可从插座标签或配置网页获取。

### 第五步：创建测试文件

新建 `test_plug.py`：

```python
from geme_plug import SmartPlug

plug = SmartPlug()  # 默认读取当前目录的 .env

plug.connect()

try:
    status = plug.get_status()
    print("开关状态:", "打开" if status.is_on else "关闭")

    power = plug.get_power()
    print("功率:", power.power, "W")
    print("电流:", power.current, "A")
finally:
    plug.disconnect()
```

### 第六步：运行

```powershell
python .\test_plug.py
```

不激活环境时：

```powershell
.\.venv\Scripts\python.exe .\test_plug.py
```

如果能输出开关状态、功率和电流，说明 Python 环境、PyPI 包、EMQX、认证信息及 MQTT 主题均已配置正确。需要控制插座时，再调用 `plug.turn_on()` 或 `plug.turn_off()`。

## 1. 环境要求

- Python 3.10 或更高版本；
- 可用的 MQTT Broker，例如 EMQX；
- 插座与运行 SDK 的电脑能够访问同一个 Broker；
- 插座已经完成 Wi-Fi 和自定义 MQTT 配置。

## 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果项目中已经存在 `.venv`，只需激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

`.venv` 是普通 Python 虚拟环境，可以通过 `pip` 安装软件包。也可以不激活环境，直接指定解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install <包名>
```

## 3. 安装 geme-plug

从 PyPI 安装：

```powershell
python -m pip install --upgrade geme-plug
```

若要立即使用仓库中尚未发布的最新代码（包括 `.env` 默认配置），请在仓库根目录安装：

```powershell
python -m pip install -e .
```

不激活虚拟环境时：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade geme-plug
```

检查安装版本：

```powershell
python -c "import geme_plug; print(geme_plug.__version__)"
```

当前 PyPI 包名为 `geme-plug`，Python 导入名为 `geme_plug`。

## 4. 启动 EMQX

仓库提供了 `compose.yaml`：

```powershell
docker compose up -d
docker compose ps
```

默认端口：

- MQTT：`1883`
- EMQX Dashboard：`18083`

在运行 Docker 的同一台电脑上测试 SDK 时，Broker 地址可使用 `127.0.0.1`。插座和局域网内其他电脑连接 Broker 时，应使用运行 EMQX 的电脑的局域网 IP，不能使用它们自身的 `127.0.0.1`。

查看设备是否已连接：

```powershell
docker exec emqx emqx ctl clients list
```

查看最近日志：

```powershell
docker compose logs --tail 100 emqx
```

## 5. MQTT 账号和主题

SDK 与插座必须使用同一个 Broker、端口和 MQTT 账号。建议统一写在本地 `.env`：

```dotenv
GEME_PLUG_USERNAME=<MQTT_USERNAME>
GEME_PLUG_PASSWORD=<MQTT_PASSWORD>
```

当前设备 `8CCE4E51ACAB` 已实测使用以下主题方向：

| 方向 | 主题 |
| --- | --- |
| SDK 发布命令 | `response` |
| SDK 订阅设备数据 | `request` |
| 设备订阅命令 | `response` |
| 设备发布数据 | `request` |

因此，在当前环境的 `.env` 中应设置：

```dotenv
GEME_PLUG_PUBLISH_TOPIC=response
GEME_PLUG_SUBSCRIBE_TOPIC=request
```

`publish_topic` 和 `subscribe_topic` 始终从 SDK 视角命名：

- `publish_topic`：SDK 向设备发送命令的主题；
- `subscribe_topic`：SDK 接收设备响应的主题。

如果其他设备的自定义 MQTT 页面使用不同主题，请按设备的实际配置修改。可以通过下面的命令查看设备当前订阅的主题：

```powershell
docker exec emqx emqx ctl subscriptions list
```

## 6. 当前环境完整示例

准备好 `.env` 后，无需在代码中重复账号、密码和 MAC：

```python
from geme_plug import SmartPlug

plug = SmartPlug()

plug.connect()

try:
    plug.turn_on()
    print("已打开")

    status = plug.get_status()
    print("开关状态:", "打开" if status.is_on else "关闭")

    power = plug.get_power()
    print("电压:", power.voltage, "V")
    print("电流:", power.current, "A")
    print("功率:", power.power, "W")
    print("累计电量:", power.energy, "kWh")
finally:
    plug.turn_off()
    print("已关闭")
    plug.disconnect()
```

这里使用 `finally`，确保状态或功率查询异常时仍会尝试关闭插座并断开连接。

## 7. 只查询状态和功率

```python
from geme_plug import SmartPlug

plug = SmartPlug()

plug.connect()

try:
    status = plug.get_status()
    print("开关状态:", "打开" if status.is_on else "关闭")

    power = plug.get_power()
    print("功率:", power.power, "W")
    print("电流:", power.current, "A")
finally:
    plug.disconnect()
```

## 8. 使用 Jupyter Notebook 测试

仓库中的 `test_switch.ipynb` 默认读取项目根目录 `.env`，并已配置好连接、开关、状态和功率测试。

在 VS Code 或其他支持 Notebook 的 IDE 中：

1. 打开 `test_switch.ipynb`；
2. 选择解释器 `.venv\Scripts\python.exe`；
3. 从上到下依次运行单元格。

如果 IDE 提示缺少 Notebook 内核，可安装：

```powershell
.\.venv\Scripts\python.exe -m pip install ipykernel
```

## 9. API 说明

### 创建客户端

```python
SmartPlug(
    host: str | None = None,
    mac: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    timeout: float | None = None,
    publish_topic: str | None = None,
    subscribe_topic: str | None = None,
    client_id: str | None = None,
    env_file: str | Path | None = ".env",
)
```

配置优先级为：构造函数显式参数 > 系统环境变量 > `.env` > SDK 内置默认值。比如只临时覆盖 Broker：

```python
plug = SmartPlug(host="192.168.50.71")
```

支持的环境变量：`GEME_PLUG_HOST`、`GEME_PLUG_PORT`、`GEME_PLUG_USERNAME`、`GEME_PLUG_PASSWORD`、`GEME_PLUG_MAC`、`GEME_PLUG_TIMEOUT`、`GEME_PLUG_PUBLISH_TOPIC`、`GEME_PLUG_SUBSCRIBE_TOPIC`、`GEME_PLUG_CLIENT_ID`。

MAC 地址支持以下格式：

```text
8CCE4E51ACAB
8C:CE:4E:51:AC:AB
8C-CE-4E-51-AC-AB
```

### 控制开关

```python
plug.turn_on()
plug.turn_off()
```

### 查询状态

```python
status = plug.get_status()
print(status.is_on)
print(status.mac)
print(status.ip)
print(status.signal)
```

`get_status()` 返回 `PlugStatus`。

### 查询功率

```python
power = plug.get_power()
print(power.voltage)
print(power.current)
print(power.power)
print(power.energy)
```

`get_power()` 返回 `PowerStatus`。

## 10. 常见问题

### `ModuleNotFoundError: No module named 'geme_plug'`

通常是 IDE 选择了错误的 Python 解释器。确认使用：

```text
<项目目录>\.venv\Scripts\python.exe
```

并在该环境中重新安装：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade geme-plug
```

### `Not authorized`

MQTT 用户名或密码与 EMQX 不一致。检查：

- `.env` 或系统环境变量中的认证配置；
- 插座自定义 MQTT 页面中的账号；
- Python 代码中的 `username` 和 `password`。

### `failed to connect to MQTT broker`

依次检查：

1. `docker compose ps` 中 EMQX 是否为 `Up`；
2. Broker IP 和端口是否正确；
3. Windows 防火墙是否允许 TCP 1883；
4. Python 与插座是否能访问同一个 Broker。

### `RequestTimeoutError`

连接 Broker 成功但设备没有返回匹配响应。重点检查：

1. 设备是否在线；
2. SDK 发布主题是否等于设备订阅主题；
3. SDK 订阅主题是否等于设备发布主题；
4. MAC 地址是否正确。

当前设备的 `.env` 应设置：

```dotenv
GEME_PLUG_PUBLISH_TOPIC=response
GEME_PLUG_SUBSCRIBE_TOPIC=request
```

## License

MIT
