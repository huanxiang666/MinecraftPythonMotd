import socket
import struct

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
    print("Received response:", data)

finally:
    # 关闭socket连接
    sock.close()
