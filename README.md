# MinecraftPythonMotd — Minecraft 服务器 MOTD 查询（Python）

查询 Minecraft 服务器的 MOTD / 在线人数 / 版本，**Java 版（TCP）和基岩版（UDP RakNet）都支持**。纯标准库，单文件，CLI / GUI / HTTP API 三种用法。

> 本次维护重构：把 Java 版从 1.6 之前的 legacy 协议换成 **现代 Server List Ping 协议（1.7+）**，修掉了 `recv(1024)` 截断 MOTD 的问题；合并了 5 份重复代码；GUI / API 拆成可选启动。

## 功能

- **Java 版**：Server List Ping（1.7+ 所有现代服务器），返回完整 JSON（MOTD、在线、版本、图标等）
- **基岩版**：RakNet Unconnected Ping，结构化解析 MOTD / 在线 / 版本 / 端口
- 域名自动解析（含 SRV 记录由系统 DNS 处理）
- 三种用法：命令行 / 图形界面 / HTTP API
- 纯标准库（HTTP API 模式才需要 flask）

## 环境要求

- Python 3.8+
- 无第三方依赖（GUI 需 tkinter；HTTP API 需 `pip install flask`）

## 使用

### 命令行

```bash
# 查 Java 版（默认端口 25565）
python main.py mc.hypixel.net

# 查基岩版（默认端口 19132）
python main.py play.example.com -e be

# 指定端口 + 输出原始 JSON
python main.py 1.2.3.4 -p 25565 --json
```

### 图形界面

```bash
python main.py --gui
# 或无参数直接运行
python main.py
```

### HTTP API

```bash
pip install flask
python main.py --api
# 访问 http://127.0.0.1:19191/api?ip=mc.hypixel.net&version=je
```

## 协议说明

- **Java 版**：发送 VarInt 握手包 + Status Request，接收 JSON 状态响应。协议版本号固定填 767，仅用于查询，不影响兼容性。
- **基岩版**：发送 RakNet Unconnected Ping（`0x01` + 时间戳 + magic + GUID），解析 pong 里的分号分隔字段。

## 文件

- `main.py` — 全部功能（单文件）

## 协议

[MIT](LICENSE)
