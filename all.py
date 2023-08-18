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

# 定义目标IP地址和端口号
target_ip = "222.187.232.146"
target_port = 19132

# 创建UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 定义要发送的数据
senddata = bytes.fromhex("0100000000240D12D300FFFF00FEFEFEFEFDFDFDFD12345678")
try:
    # 发送数据到指定的IP和端口
    sock.sendto(senddata, (target_ip, target_port))

    # 等待接收响应数据
    data, server = sock.recvfrom(4096)

    # 按分号分割响应数据
    split_data = data.split(b";")

    # 选择感兴趣的特定行的索引
    interested_indices = [1, 2, 3, 4, 5, 6, 8]

    # 创建一个字符串来存储所选行的内容
    selected_lines = ""

    # 遍历所选索引，并将对应行的内容添加到字符串中
    for index in interested_indices:
        line = split_data[index].decode("utf-8")
        if index == 1:
            line = line.split("\\")[0]  # 截取 \ 前面的内容
        selected_lines += line + " "  # 将内容添加到字符串中，并加入空格

    # 打印选中的行内容
    print("Selected lines:", selected_lines)

finally:
    # 关闭socket连接
    sock.close()
