import socket
from flask import Flask, request, jsonify
import dns.resolver
import re
import time
import tkinter as tk
import threading

def query_minecraft_server(server_ip, server_port):
    try:
        # 创建TCP socket
        socku = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socku.settimeout(5)  # 设置超时时间为5秒

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
    finally:
            # 关闭socket连接
            sock.close()

def is_valid_ip(address):# 判断IP地址
    pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(pattern, address):
        print("yes")
    else:
        print("no")
def resolve_minecraft_srv(domain):
    try:
        # 解析 SRV 记录
        resolver = dns.resolver.Resolver()
        srv_records = resolver.query('_minecraft._tcp.' + domain, 'SRV')

        # 提取服务器地址和端口
        server_address_srv = str(srv_records[0].target).rstrip('.')
        server_port_srv = srv_records[0].port

        return server_address_srv, server_port_srv
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
        print("Error resolving SRV record:", e)
        return None, None
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

def tkgui():
    def submit_button_click():
        input1_value = input1.get()
        input2_value = input2.get()
        input3_value = input3.get()

        display_text.config(state=tk.NORMAL)
        display_text.delete(1.0, tk.END)
        display_text.insert(tk.END, f"输入框1: {input1_value}\n")
        display_text.insert(tk.END, f"输入框2: {input2_value}\n")
        display_text.insert(tk.END, f"输入框3: {input3_value}\n")
        display_text.config(state=tk.DISABLED)

    # 创建主窗口
    root = tk.Tk()
    root.title("输入框示例")

    # 创建输入框和提交按钮
    input1 = tk.Entry(root)
    input2 = tk.Entry(root)
    input3 = tk.Entry(root)
    submit_button = tk.Button(root, text="提交", command=submit_button_click)

    # 创建显示框
    display_text = tk.Text(root, height=10, width=30)
    display_text.config(state=tk.DISABLED)  # 设置为只读

    # 设置布局
    input1.pack(pady=5)
    input2.pack(pady=5)
    input3.pack(pady=5)
    submit_button.pack(pady=10)
    display_text.pack(pady=10)

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
        return "hello"

    if __name__ == '__main__':
            app.run(host='0.0.0.0', port=8080)
gui_thread = threading.Thread(target=tkgui)
web_thread = threading.Thread(target=webserver)

gui_thread.start()
web_thread.start()

gui_thread.join()
web_thread.join()





