import socket
from flask import Flask, request, jsonify
import dns.resolver

app = Flask(__name__)


@app.route('/api', methods=['GET', 'POST'])
def process_request():
    global ip, port, version
    if request.method == 'GET':
        ip = request.args.get('ip')
        port = int(request.args.get('port'))
        version = request.args.get('version')
    elif request.method == 'POST':
        data = request.json
        ip = data.get('ip')
        port = data.get('port')
        version = data.get('version')

    # 在这里处理你的请求，并准备回传的数据
    response_data = {
        'message': 'Request processed successfully',
        'client_ip': ip,
        'client_port': port,
        'client_version': version
    }

    return jsonify(response_data)


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


if __name__ == '__main__':
    domain = "8.mcbbb.top"  # 替换为你的域名
    server_address, server_port = resolve_minecraft_srv(domain)

    if server_address and server_port:
        print("Server Address:", server_address)
        print("Server Port:", server_port)
    else:
        import dns.resolver


        def resolve_dns_with_fallback(domain):
            try:
                # 创建 DNS 解析器
                resolver = dns.resolver.Resolver()

                # 尝试解析 A 记录
                a_records = resolver.resolve(domain, 'A')

                server_address_a = str(a_records[0])
                return server_address_a
            except dns.resolver.NoAnswer:
                pass  # 没有 A 记录，继续尝试解析 CNAME 记录
            except dns.exception.DNSException as e:
                print("Error resolving A record:", e)

            try:
                # 尝试解析 CNAME 记录
                cname_records = resolver.resolve(domain, 'CNAME')

                cname_target = str(cname_records[0].target).rstrip('.')
                # 递归解析 CNAME 记录的目标
                return resolve_dns_with_fallback(cname_target)
            except dns.resolver.NoAnswer:
                pass  # 没有 CNAME 记录，继续尝试解析 AAAA 记录
            except dns.exception.DNSException as e:
                print("Error resolving CNAME record:", e)

            try:
                # 尝试解析 AAAA 记录
                aaaa_records = resolver.resolve(domain, 'AAAA')

                server_address_aaaa = str(aaaa_records[0])
                return server_address_aaaa
            except dns.resolver.NoAnswer:
                pass  # 没有 AAAA 记录，解析失败
            except dns.exception.DNSException as e:
                print("Error resolving AAAA record:", e)

            return None  # 所有尝试都失败，返回 None


        if __name__ == '__main__':
            domain = "8.mcbbb.top"  # 替换为你的域名

            resolved_ip = resolve_dns_with_fallback(domain)

            if resolved_ip:
                print("Resolved IP Address:", resolved_ip)
            else:
                print("Unable to resolve A/CNAME/AAAA records for", domain)

        print("Unable to resolve SRV record for", domain)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


def query_minecraft_server(server_ip, server_port):
    global socku
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


# 服务器IP和端口
server_ip = "222.187.232.146"
server_port = 25565

# 查询服务器并获取MOTD信息
motd = query_minecraft_server(server_ip, server_port)
print(motd)

# 定义目标IP地址和端口号
target_ip = "222.187.232.146"
target_port = 19132

# 创建UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 定义要发送的数据
sendto = bytes.fromhex("0100000000240D12D300FFFF00FEFEFEFEFDFDFDFD12345678")
try:
    # 发送数据到指定的IP和端口
    sock.sendto(sendto, (target_ip, target_port))

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
    print(selected_lines)

finally:
    # 关闭socket连接
    sock.close()
