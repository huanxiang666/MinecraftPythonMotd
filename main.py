#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minecraft 服务器 MOTD 查询 — Java 版 + 基岩版。

现代协议实现:
- Java 版: Server List Ping (1.7+)，VarInt 握手 + JSON 状态响应
- 基岩版: RakNet Unconnected Ping (UDP)
纯标准库。可独立作为模块 import，也可命令行/GUI/HTTP API 运行。
"""
import argparse
import ipaddress
import json
import socket
import struct
import sys
import time

DEFAULT_JAVA_PORT = 25565
DEFAULT_BE_PORT = 19132
DEFAULT_TIMEOUT = 3.0

# RakNet 固定魔数
RAKNET_MAGIC = bytes.fromhex("00FFFF00FEFEFEFEFDFDFDFD12345678")


# ============================================================
# Java 版 (Server List Ping, 1.7+)
# ============================================================

def _write_varint(value: int) -> bytes:
    """VarInt 编码（Minecraft 协议的可变长度整数）。"""
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def _read_varint(sock) -> int:
    """从 socket 读一个 VarInt。"""
    num = 0
    for i in range(5):
        byte = sock.recv(1)
        if not byte:
            raise ConnectionError("连接被服务器关闭")
        b = byte[0]
        num |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            return num
    raise ValueError("VarInt 过长")


def _write_string(s: str) -> bytes:
    data = s.encode("utf-8")
    return _write_varint(len(data)) + data


def _read_exactly(sock, n: int) -> bytes:
    """读满 n 字节，避免 recv 截断。"""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接被服务器关闭")
        buf.extend(chunk)
    return bytes(buf)


def query_java(host: str, port: int = DEFAULT_JAVA_PORT, timeout: float = DEFAULT_TIMEOUT):
    """查询 Java 版服务器状态，返回 dict（含 description/players/version 等）。"""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        # Handshake 包
        handshake = (
            b"\x00"                                  # packet id
            + _write_varint(767)                     # protocol version (1.20.x 附近，不影响查询)
            + _write_string(host)
            + struct.pack(">H", port)
            + _write_varint(1)                       # next state: status
        )
        sock.sendall(_write_varint(len(handshake)) + handshake)
        # Status Request
        sock.sendall(b"\x01\x00")

        # Status Response: 长度 + packet id + JSON 长度 + JSON
        _read_varint(sock)            # 包总长
        pkt_id = _read_varint(sock)   # 应为 0x00
        if pkt_id != 0:
            raise ValueError(f"意外的响应包 id: {pkt_id}")
        json_len = _read_varint(sock)
        payload = _read_exactly(sock, json_len)
        return json.loads(payload.decode("utf-8", "replace"))


def java_summary(data: dict) -> str:
    """把 Java 版 JSON 状态整理成可读字符串。"""
    desc = data.get("description", "")
    if isinstance(desc, dict):
        motd = desc.get("text", "") or "".join(
            c.get("text", "") for c in desc.get("extra", []))
    else:
        motd = str(desc)
    players = data.get("players", {})
    online = players.get("online", "?")
    maxp = players.get("max", "?")
    version = data.get("version", {}).get("name", "?")
    return f"{motd} | 在线 {online}/{maxp} | 版本 {version}"


# ============================================================
# 基岩版 (RakNet Unconnected Ping, UDP)
# ============================================================

def query_bedrock(host: str, port: int = DEFAULT_BE_PORT, timeout: float = DEFAULT_TIMEOUT):
    """查询基岩版服务器，返回结构化 dict。"""
    # Unconnected Ping: 0x01 + 时间戳(8) + magic + client guid(8)
    ping = b"\x01" + struct.pack(">q", int(time.time())) + RAKNET_MAGIC + b"\x00" * 8
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(ping, (host, port))
        data, _ = sock.recvfrom(4096)

    if not data or data[0] != 0x1C:
        raise ValueError("不是有效的基岩版 pong 响应")
    # 跳过: 0x1C + 时间戳(8) + server guid(8) + magic(16) + 字符串长度(2)
    offset = 1 + 8 + 8 + 16
    if len(data) < offset + 2:
        raise ValueError("pong 数据过短")
    strlen = struct.unpack(">H", data[offset:offset + 2])[0]
    text = data[offset + 2: offset + 2 + strlen].decode("utf-8", "replace")
    parts = text.split(";")
    # 字段: edition;motd1;protocol;version;online;max;guid;motd2;...
    def field(i):
        return parts[i] if i < len(parts) else ""
    return {
        "edition": field(0),
        "motd": field(1),
        "protocol": field(2),
        "version": field(3),
        "online": field(4),
        "max": field(5),
        "motd_line2": field(7),
    }


def bedrock_summary(d: dict) -> str:
    return (f"{d['motd']} | 在线 {d['online']}/{d['max']} | "
            f"版本 {d['version']} | {d['edition']}")


# ============================================================
# 统一入口
# ============================================================

def query(host: str, port: int = None, edition: str = "je", timeout: float = DEFAULT_TIMEOUT):
    """查询服务器。edition: 'je'(Java) 或 'be'(基岩)。返回 (raw, summary)。"""
    if edition == "be":
        port = port or DEFAULT_BE_PORT
        raw = query_bedrock(host, port, timeout)
        return raw, bedrock_summary(raw)
    else:
        port = port or DEFAULT_JAVA_PORT
        raw = query_java(host, port, timeout)
        return raw, java_summary(raw)


def resolve_host(host: str):
    """域名解析为 IP；已是 IP 则原样返回。"""
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        return socket.gethostbyname(host)


# ============================================================
# CLI
# ============================================================

def cli_main(argv=None):
    ap = argparse.ArgumentParser(description="Minecraft 服务器 MOTD 查询")
    ap.add_argument("host", help="服务器 IP 或域名")
    ap.add_argument("-p", "--port", type=int, default=None,
                    help="端口（Java 默认 25565，基岩默认 19132）")
    ap.add_argument("-e", "--edition", choices=["je", "be"], default="je",
                    help="je=Java版, be=基岩版")
    ap.add_argument("-t", "--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = ap.parse_args(argv)

    try:
        host = resolve_host(args.host)
        raw, summary = query(host, args.port, args.edition, args.timeout)
        if args.json:
            print(json.dumps(raw, ensure_ascii=False, indent=2))
        else:
            print(summary)
        return 0
    except (socket.timeout, socket.gaierror) as e:
        print(f"[失败] 连接超时或无法解析: {e}")
        return 1
    except (ConnectionError, ValueError, OSError) as e:
        print(f"[失败] {e}")
        return 1


# ============================================================
# GUI
# ============================================================

def gui_main():
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext

    class App:
        def __init__(self, root):
            self.root = root
            root.title("Minecraft MOTD 查询")
            root.geometry("560x360")

            frm = ttk.Frame(root, padding=10)
            frm.pack(fill="x")
            ttk.Label(frm, text="IP/域名:").grid(row=0, column=0, sticky="w")
            self.host_entry = ttk.Entry(frm, width=30)
            self.host_entry.grid(row=0, column=1, sticky="w")
            ttk.Label(frm, text="端口(留空自动):").grid(row=1, column=0, sticky="w")
            self.port_entry = ttk.Entry(frm, width=10)
            self.port_entry.grid(row=1, column=1, sticky="w")
            ttk.Label(frm, text="版本:").grid(row=2, column=0, sticky="w")
            self.edition = ttk.Combobox(frm, values=["je (Java)", "be (基岩)"], width=12)
            self.edition.grid(row=2, column=1, sticky="w")
            self.edition.set("je (Java)")
            ttk.Button(frm, text="查询", command=self.run).grid(row=3, column=0, pady=8)

            self.out = scrolledtext.ScrolledText(root, height=12, font=("Consolas", 10))
            self.out.pack(fill="both", expand=True, padx=10, pady=10)

        def run(self):
            host = self.host_entry.get().strip()
            if not host:
                messagebox.showerror("错误", "请输入 IP 或域名")
                return
            port_txt = self.port_entry.get().strip()
            port = int(port_txt) if port_txt.isdigit() else None
            edition = "be" if self.edition.get().startswith("be") else "je"
            self.out.delete("1.0", "end")
            self.out.insert("end", "查询中…\n")

            def work():
                try:
                    ip = resolve_host(host)
                    raw, summary = query(ip, port, edition)
                    text = summary + "\n\n" + json.dumps(raw, ensure_ascii=False, indent=2)
                except Exception as e:
                    text = f"[失败] {e}"
                self.root.after(0, self._show, text)

            import threading
            threading.Thread(target=work, daemon=True).start()

        def _show(self, text):
            self.out.delete("1.0", "end")
            self.out.insert("end", text)

    root = tk.Tk()
    App(root)
    root.mainloop()


# ============================================================
# HTTP API（可选，需 flask）
# ============================================================

def api_main(host="0.0.0.0", port=19191):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("HTTP API 模式需要 flask: pip install flask")
        sys.exit(1)
    app = Flask(__name__)

    @app.route("/api")
    def api():
        h = request.args.get("ip", "").strip()
        if not h:
            return jsonify({"error": "缺少 ip 参数"}), 400
        p = request.args.get("port", type=int)
        e = request.args.get("version", "je")
        try:
            ip = resolve_host(h)
            raw, summary = query(ip, p, e)
            return jsonify({"ok": True, "summary": summary, "raw": raw})
        except Exception as ex:
            return jsonify({"ok": False, "error": str(ex)}), 502

    print(f"API 监听 http://{host}:{port}/api?ip=HOST&version=je")
    app.run(host=host, port=port)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--api":
            api_main()
        elif sys.argv[1] == "--gui":
            gui_main()
        else:
            sys.exit(cli_main())
    else:
        gui_main()
