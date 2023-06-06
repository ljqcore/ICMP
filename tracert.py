import array
import socket
import os
import struct
import time
import select


# ICMP报文类型 => 回送请求报文
TYPE_ECHO_REQUEST = 8
CODE_ECHO_REQUEST_DEFAULT = 0

# ICMP报文类型 => 回送应答报文
TYPE_ECHO_REPLY = 0
CODE_ECHO_REPLY_DEFAULT = 0

# ICMP报文类型 => 数据报超时报文
TYPE_ICMP_OVERTIME = 11
CODE_TTL_OVERTIME = 0

# ICMP报文类型 => 目的站不可达报文
TYPE_ICMP_UNREACHED = 3
CODE_NET_UNREACHED = 0
CODE_HOST_UNREACHED = 1
CODE_PORT_UNREACHED = 3

MAX_HOPS = 30  # 设置路由转发最大跳数为30
TIMEOUT = 3  # 如果一个请求超过3s未得到响应，则被认定为超时
TRIES = 3  # 对于每个中间站点，探测的次数设置为3


def checksum(data):
    """
    计算校验和
    """
    if len(data) % 2:  # 长度为奇数，则补字节
        data += b'\x00'
    s = sum(array.array('H', data))
    s = (s & 0xffff) + (s >> 16)  # 移位计算两次，以确保高16位为0
    s += (s >> 16)
    answer = ~s  # 取反
    # 将结果转换为网络字节序（即大端字节序）
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    # print(answer)
    return answer


def get_host_info(host_addr):
    """"
    获取相应ip地址对应的主机信息
    """
    try:
        host_info = socket.gethostbyaddr(host_addr)
    except socket.error as e:
        display = '{0} (主机名不可得)'.format(host_addr)
    else:
        display = '{0} ({1})'.format(host_addr, host_info[0])
    return display


def build_packet():
    """"
    构建ICMP报文
    """
    # 先将检验和设置为0
    myChecksum = 0
    # 用进程号作标识
    ID = os.getpid() & 0xffff
    # 序列号
    sequence = 1

    # 打包出二进制首部 !-网络字节序（大端序）
    header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
    # 以当前系统时间作为报文的数据部分
    data = struct.pack("!d", time.time())
    # 构建一个临时的数据报
    # 利用原始数据报来计算真正的校验和
    myChecksum = checksum(header + data)
    # 重新构建出真正的数据包
    header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
    package = header + data
    return package


def tracert(host):
    dest = socket.gethostbyname(host)
    text = ''
    print("最多通过30个跃点追踪")
    text += "最多通过30个跃点追踪" + '\n'
    print("到", dest, "的路由：")
    text += "到" + str(dest) + "的路由：" + '\n'

    for ttl in range(1, MAX_HOPS):
        print("%2d" % ttl, end="")
        text += "%2d" % ttl
        for tries in range(0, TRIES):

            # 创建icmp原始套接字
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
            # 设置原始套接字的TTL属性
            icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))  # I表示4字节
            # 设置超时时间
            icmp_socket.settimeout(TIMEOUT)

            # 构建报文并发送
            icmp_package = build_packet()
            try:
                start = time.time()
                icmp_socket.sendto(icmp_package, (host, 1))
            except socket.gaierror as e:
                print("这不是一个有效的地址！")
                text += "这不是一个有效的地址！" + '\n'
                return text

            # 进入阻塞态，等待接收ICMP超时报文/应答报文
            select.select([icmp_socket], [], [], TIMEOUT)
            end_time = time.time()
            # 计算阻塞的时间
            during_time = end_time - start
            if during_time >= TIMEOUT:
                print("    *    ", end="")
                text += "    *    "
            else:
                print(" %4.0f ms " % (during_time * 1000), end="")
                text += " %4.0f ms " % (during_time*1000)
            if tries >= TRIES - 1:
                try:
                    ip_package, ip_info = icmp_socket.recvfrom(1024)
                except socket.timeout:
                    print(" 请求超时.")
                    text += " 请求超时." + '\n'
                else:
                    # 从IP数据报中取出ICMP报文的首部，位置在20：28，因为IP数据报首部长度为20
                    icmp_header = ip_package[20:28]

                    # 解析ICMP数据报首部各字段
                    after_type, after_code, after_checksum, after_id, after_sequence = struct.unpack("!bbHHh", icmp_header)

                    # ip_info[0]:发送数据的IP地址
                    # 想办法获取IP地址对应的主机信息（如果有的话）
                    output = get_host_info(ip_info[0])

                    if after_type == TYPE_ICMP_UNREACHED:  # 目的不可达
                        print("目的不可达")
                        text += "目的不可达" + '\n'
                        break
                    elif after_type == TYPE_ICMP_OVERTIME:  # 超时报文
                        print(" %s" % output)
                        text += " %s" % output + '\n'
                        continue
                    elif after_type == 0:  # 应答报文
                        print(" %s" % output)
                        text += " %s" % output + '\n'
                        print("追踪完成！")
                        text += "追踪完成！" + '\n'
                        return text
                    else:
                        print("请求超时.")
                        text += "请求超时." + '\n'
                        print("追踪失败!")
                        text += "追踪失败!" + '\n'
                        return text


if __name__ == "__main__":
    host = input("please input a dest address:")
    text = tracert(host)
    # print(text)
