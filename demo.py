import socket


def query_minecraft_server(server_ip, server_port):
    try:
        # 创建TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 设置超时时间为5秒

        # 连接服务器
        sock.connect((server_ip, server_port))

        # 发送握手数据包
        handshake_packet = b"\xFE\x01" + b"\x00" * 125
        sock.send(handshake_packet)

        # 接收服务器响应数据
        response = sock.recv(1024)

        # 解析MOTD信息
        motd = response[5:].decode("utf-16be")

        return motd
    except socket.timeout:
        print("连接超时")
    finally:
        sock.close()


# 服务器IP和端口
server_ip = "222.187.232.146"
server_port = 25565

# 查询服务器并获取MOTD信息
motd = query_minecraft_server(server_ip, server_port)
print("MOTD:", motd)
