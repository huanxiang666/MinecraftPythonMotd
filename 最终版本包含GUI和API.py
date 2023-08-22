import socket
from flask import Flask, request, jsonify
import dns.resolver
import re
import time
import tkinter as tk
from tkinter import ttk
import threading


def query_minecraft_server(server_ip, server_port):
    try:
        # 创建TCP socket
        socku = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socku.settimeout(2)  # 设置超时时间为5秒

        # 连接服务器
        socku.connect((server_ip, server_port))

        # 发送握手数据包
        handshake_packet = b"\xFE\x01" + b"\x00" * 125
        socku.send(handshake_packet)

        # 接收服务器响应数据
        response = socku.recv(1024)

        # 解析MOTD信息
        motd = response[5:].decode("utf-16be")

        return motd
    except socket.timeout:
        print("连接超时")
    finally:
        socku.close()


def query_bedrock_server(server_ip, server_port):
    try:

        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)  # 设置超时时间为5秒

        # 定义要发送的数据
        sendto = bytes.fromhex("0100000000240D12D300FFFF00FEFEFEFEFDFDFDFD12345678")
        try:
            # 发送数据到指定的IP和端口
            sock.sendto(sendto, (server_ip, server_port))

            # 等待接收响应数据
            data, server = sock.recvfrom(4096)

            # 按分号分割响应数据
            split_data = data.split(b";")

            # 选择感兴趣的特定行的索引
            interested_indices = [1, 2, 3, 4, 5, 6, 8]

            # 创建一个字符串来存储所选行的内容
            selected_lines2 = ""

            # 遍历所选索引，并将对应行的内容添加到字符串中
            for index in interested_indices:
                line = split_data[index].decode("utf-8")
                if index == 1:
                    line = line.split("\\")[0]  # 截取 \ 前面的内容
                selected_lines2 += line + " "  # 将内容添加到字符串中，并加入空格

            # 打印选中的行内容
            return selected_lines2
        except socket.timeout:
            print("连接超时")
            return "连接超时"
    finally:
        # 关闭socket连接
        sock.close()


def is_valid_ip(address):  # 判断IP地址
    pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(pattern, address):
        return True
    else:
        return False


def resolve_minecraft_srv(domain,nosrvport):
    try:
        # 解析 SRV 记录
        resolver = dns.resolver.Resolver()
        srv_records = resolver.query('_minecraft._tcp.' + domain, 'SRV')

        # 提取服务器地址和端口
        server_address_srv = resolve_dns_with_fallback(str(srv_records[0].target).rstrip('.'))
        server_port_srv = srv_records[0].port
        return query_minecraft_server(server_address_srv, server_port_srv)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
        print("Error resolving SRV record:", e)
        nextip=resolve_dns_with_fallback(domain)
        test = query_minecraft_server(nextip, int(nosrvport))
        return test



def resolve_dns_with_fallback(domain):
    try:
        # 创建 DNS 解析器
        resolver = dns.resolver.Resolver()

        # 尝试解析 A 记录
        try:
            a_records = resolver.resolve(domain, 'A')
            server_address_a = str(a_records[0])
            return server_address_a
        except dns.resolver.NoAnswer:
            pass  # 没有 A 记录，继续尝试解析 CNAME 记录
        except dns.exception.DNSException as e:
            print("Error resolving A record:", e)

        # 尝试解析 CNAME 记录
        try:
            cname_records = resolver.resolve(domain, 'CNAME')
            cname_target = str(cname_records[0].target).rstrip('.')
            # 递归解析 CNAME 记录的目标
            return resolve_dns_with_fallback(cname_target)
        except dns.resolver.NoAnswer:
            pass  # 没有 CNAME 记录，继续尝试解析 AAAA 记录
        except dns.exception.DNSException as e:
            print("Error resolving CNAME record:", e)

        # 尝试解析 AAAA 记录
        try:
            aaaa_records = resolver.resolve(domain, 'AAAA')
            server_address_aaaa = str(aaaa_records[0])
            return server_address_aaaa
        except dns.resolver.NoAnswer:
            pass  # 没有 AAAA 记录，解析失败
        except dns.exception.DNSException as e:
            print("Error resolving AAAA record:", e)

        return None  # 所有尝试都失败，返回 None

    except dns.exception.DNSException as e:
        print("Error:", e)
        return None


def ping(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 设置超时时间为2秒

        start_time = time.time()
        sock.connect((host, port))
        end_time = time.time()

        rtt = (end_time - start_time) * 1000  # 转换成毫秒

        print(f"从 {host}:{port} 到达，往返时间：{rtt:.2f} 毫秒")
    except Exception as e:
        print("Ping 失败:", e)
    finally:
        sock.close()


def output(ip, port, mode):
    if is_valid_ip(ip):
        if mode == "be":
            return query_bedrock_server(ip, port)
        else:
            return query_minecraft_server(ip, port)
    else:
        if mode == "be":
            return query_bedrock_server(resolve_dns_with_fallback(ip), int(port))
        else:
            return resolve_minecraft_srv(ip,port)






def tkgui():
    def handle_submission():
        ip = ip_entry.get()
        port = port_entry.get()
        version = version_var.get()
        result = output(ip, port, version)
        result_label.config(text=result)

    # 创建 GUI 窗口
    root = tk.Tk()
    root.title("Motd查询:主机IP:19191/api?ip=mcbbb.top&port=25565&version=je")

    # 添加输入框和标签
    ip_label = tk.Label(root, text="IP或者域名:")
    ip_label.pack()

    ip_entry = tk.Entry(root)
    ip_entry.pack()
    ip_entry.insert(0, "mcbbb.top")  # 默认值

    port_label = tk.Label(root, text="端口号（一般基岩19132）:")
    port_label.pack()

    port_entry = tk.Entry(root)
    port_entry.pack()
    port_entry.insert(0, "25565")  # 默认值

    # 添加选择框
    version_label = tk.Label(root, text="BE基岩版JE电脑Java版本:")
    version_label.pack()

    version_var = tk.StringVar()
    version_combobox = ttk.Combobox(root, textvariable=version_var, values=["je", "be"])
    version_combobox.pack()
    version_combobox.set("je")  # 默认选择

    # 添加提交按钮
    submit_button = tk.Button(root, text="提交", command=handle_submission)
    submit_button.pack()

    # 显示处理结果
    result_label = tk.Label(root, text="")
    result_label.pack()

    # 启动主循环
    root.mainloop()


def webserver():
    app = Flask(__name__)

    @app.route('/api', methods=['GET', 'POST'])
    def process_request():
        global ip, port, version, srvport
        if request.method == 'GET':
            ip = request.args.get('ip')
            port = int(request.args.get('port'))
            version = request.args.get('version')
        elif request.method == 'POST':
            data = request.json
            ip = data.get('ip')
            port = data.get('port')
            version = data.get('version')
        return output(ip, port,version)

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=19191)


gui_thread = threading.Thread(target=tkgui)
web_thread = threading.Thread(target=webserver)

gui_thread.start()
web_thread.start()

gui_thread.join()
web_thread.join()
