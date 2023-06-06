import math
import socket
import os
import struct
import time
import array

import select

TYPE_ECHO_REQUEST = 8
CODE_ECHO_REQUEST_DEFAULT = 0
# 计算校验和
'''
遍历字符串中的每一对字节，并将它们解释为一个16位的整数，然后将所有这些16位整数相加。如果字符串长度不是偶数，则最后一个字节被视为单独的字节并与前面的字节配对。
将相加的结果分成两个16位部分，并将这些部分再次相加。然后，将结果取反，再次将结果的高8位和低8位交换位置，即可获得计算出来的校验和。
'''


def checksum(str):
    """
    计算校验和
    :param str: ICMP报文
    :return: 校验和
    """
    # 1. 判断奇偶，奇数添加空字节
    if len(str) % 2:
        str += b'\x00'
    # 2. 将信息分成16bytes的块, 并相加
    s = sum(array.array('H', str))
    # 3. 超过32bytes，高16位加低16位
    s = (s & 0xffff) + (s >> 16)
    s += (s >> 16)
    # 4. 取反
    answer = ~s
    # 5. 最后将结果转换为网络字节序（即大端字节序）
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# 接受 ICMP 报文，并从中解析出 RTT 时间等信息
def receiveOnePing(mySocket, ID, sequence, destAddr, timeout):
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        # 监视
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        # 超时时间内未收到数据包，就返回空
        if not whatReady[0]:
            return None

        timeReceived = time.time()
        # 一次能接受的最大数据1024bytes,事实上只需要读取20个字节的IP头部和8个字节的ICMP数据负载
        # 返回：接收到的数据，发送数据的地址和端口号
        recPacket, addr = mySocket.recvfrom(1024)

        # IPv4中，头部信息占20bytes
        header = recPacket[20: 28]
        type, code, checksum, packetID, sequence = struct.unpack("!bbHHh", header)

        # 检查回收报文Echo-Reply:目的不可达
        if type == 3 and code in [0, 1]:
            if code == 0:
                error = "目标网络无法到达"
            else:
                error = "目标主机不可到达"
            return (error, None, None)
        # Echo-Reply: type == 0 匹配ID
        if type == 0 and packetID == ID:
            # struct模块可以将二进制数据转换为python数据类型
            # calcsize()将字符串转化为字节数目
            byte_in_double = struct.calcsize("!d")
            timeSent = struct.unpack("!d", recPacket[28: 28 + byte_in_double])[0]
            # timeSent：发送Echo请求的时间戳
            delay = timeReceived - timeSent  # RTT往返时间
            # TTL:生存时间 返回TTL的十进制整数值
            ttl = ord(struct.unpack("!c", recPacket[8:9])[0].decode())
            return (None, delay, ttl, byte_in_double)

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None


# 构造 ICMP 报文，发送报文到目标地址
def sendOnePing(mySocket, ID, sequence, destAddr):
    # ICMP报文包含：type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # 构建一个ICMP报文头部：type=ICMP_ECHO_REQUEST code=0 checkSum=myChecksum ID,sequence匹配回显请求与回显响应
    header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
    # 建一个长度为8字节的数据部分，其中包含当前时间戳
    data = struct.pack("!d", time.time())
    # 计算完整数据包的校验和
    myChecksum = checksum(header + data)
    # 更新报文头部
    header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
    packet = header + data
    # 将ICMP数据包发送给目的地址，注意此处发送的destAddr必须是元组类型：（destAddr,1）将其转换为元组类型
    # 1是端口号，但事实上ICMP报文传输信息不需要端口号
    # print("测试中", destAddr)
    try:
        mySocket.sendto(packet, (destAddr, 1))
    except socket.gaierror as e:
        print("请输入一个有效的IP地址！")
        return


# 执行一次 ping 操作，即发送 ICMP 报文并接收响应，返回延迟时间（RTT）
def doOnePing(destAddr, ID, sequence, timeout):
    # 返回ICMP协议对应的协议号
    icmp = socket.getprotobyname("icmp")

    # 创建了一个基于ICMP协议的原始socket
    # socket.AF_INET：指定使用 IPv4 网络协议  socket.SOCK_RAW：指定创建原始套接字(raw socket)
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    sendOnePing(mySocket, ID, sequence, destAddr)
    delay = receiveOnePing(mySocket, ID, sequence, destAddr, timeout)

    mySocket.close()
    return delay


def ping(host, timeout=1):
    # 转换为主机对应的IP地址
    dest = socket.gethostbyname(host)
    print("Ping " + dest)
    text = ''
    # 获取当前进程ID并转换为一个16位无符号整数值
    myID = os.getpid() & 0xFFFF
    loss = 0
    total = 0
    min_rrt = float("inf")
    max_rrt = -float("inf")
    recevied = 0
    sample_list = []
    # 默认向服务端发送4次请求信息
    for i in range(4):
        result = doOnePing(dest, myID, i, timeout)
        if not result:   # 丢包
            print("请求超时")
            text += "请求超时"
            loss += 1
        elif result[0]:  # 主机不可达
            print(result[0])
            text += result[0]
            loss += 1
        else:
            delay = int(result[1] * 1000)
            ttl = result[2]
            bytes = result[3]
            total += delay
            min_rrt = min(min_rrt, delay)
            max_rrt = max(max_rrt, delay)
            sample_list.append(delay)
            print("来自 " + dest + " 的回复" + ": 字节=" + str(bytes) + " 时间=" + str(delay) + "ms TTL=" + str(ttl))
            text += "来自 " + dest + " 的回复" + ": 字节=" + str(bytes) + " 时间=" + str(delay) + "ms TTL=" + str(ttl) + '\n'
        time.sleep(1)

    recevied = 4 - loss
    print(dest + " 的 Ping 统计信息：")
    text += dest + " 的 Ping 统计信息：" + '\n'
    print("数据包: 已发送 = " + str(4) + ", 已接受 = " + str(recevied) + ", 丢失 = " + str(loss))
    text += "数据包: 已发送 = " + str(4) + ", 已接受 = " + str(recevied) + ", 丢失 = " + str(loss) + '\n'
    if recevied > 0:
        print("往返路程的估计时间（以毫秒为单位）:")
        text += "往返路程的估计时间（以毫秒为单位）:" + '\n'
        print("最短 = " + str(min_rrt) + "ms, 最长 = " + str(max_rrt) + "ms, 平均 = " + str(total / recevied) + "ms")
        text += "最短 = " + str(min_rrt) + "ms, 最长 = " + str(max_rrt) + "ms, 平均 = " + str(total / recevied) + "ms" + '\n'
        if recevied > 1:
            variance = sum((x - (total / recevied)) ** 2 for x in sample_list) / (recevied - 1)
            std_dev = math.sqrt(variance)
            print("样本标准差 = %.2fms" % std_dev)
            text += "样本标准差 = %.2fms" % std_dev + '\n'
    return text


# ping("www.baidu.com")
