# import socket
# import os
# import struct
# import time
# import array
#
# import select
#
# # ICMP报文类型 => 回送请求报文
# TYPE_ECHO_REQUEST = 8
# CODE_ECHO_REQUEST_DEFAULT = 0
#
# # ICMP报文类型 => 回送应答报文
# TYPE_ECHO_REPLY = 0
# CODE_ECHO_REPLY_DEFAULT = 0
#
# # ICMP报文类型 => 数据报超时报文
# TYPE_ICMP_OVERTIME = 11
# CODE_TTL_OVERTIME = 0
#
# # ICMP报文类型 => 目的站不可达报文
# TYPE_ICMP_UNREACHED = 3
# CODE_NET_UNREACHED = 0
# CODE_HOST_UNREACHED = 1
# CODE_PORT_UNREACHED = 3
#
# MAX_HOPS = 30  # 设置路由转发最大跳数为30
# TIMEOUT = 3  # 如果一个请求超过3s未得到响应，则被认定为超时
# TRIES = 1  # 对于每个中间站点，探测的次数设置为1
#
# # 计算校验和
# '''
# 遍历字符串中的每一对字节，并将它们解释为一个16位的整数，然后将所有这些16位整数相加。如果字符串长度不是偶数，则最后一个字节被视为单独的字节并与前面的字节配对。
# 将相加的结果分成两个16位部分，并将这些部分再次相加。然后，将结果取反，再次将结果的高8位和低8位交换位置，即可获得计算出来的校验和。
# '''
#
#
# # 计算校验和
# def checksum(str):
#     """
#     计算校验和
#     :param str: ICMP报文
#     :return: 校验和
#     """
#     # 1. 判断奇偶，奇数添加空字节
#     if len(str) % 2:
#         str += b'\x00'
#     # 2. 将信息分成16bytes的块, 并相加
#     s = sum(array.array('H', str))
#     # 3. 超过32bytes，高16位加低16位
#     s = (s & 0xffff) + (s >> 16)
#     s += (s >> 16)
#     # 4. 取反
#     answer = ~s
#     # 5. 最后将结果转换为网络字节序（即大端字节序）
#     answer = answer & 0xffff
#     answer = answer >> 8 | (answer << 8 & 0xff00)
#     # print(answer)
#     return answer
#
#
# # 接受 ICMP 报文，并从中解析出 RTT 时间等信息
# def receiveOnePing(mySocket, ID, sequence, destAddr, timeout):
#     timeLeft = timeout
#
#     while True:
#         startedSelect = time.time()
#         # 监视
#         whatReady = select.select([mySocket], [], [], timeLeft)
#         howLongInSelect = (time.time() - startedSelect)
#         # 超时时间内未收到数据包，就返回空
#         if not whatReady[0]:
#             return None
#
#         timeReceived = time.time()
#         # 一次能接受的最大数据1024bytes
#         # 返回：接收到的数据，发送数据的地址和端口号
#         recPacket, addr = mySocket.recvfrom(1024)
#
#         # print("接受到的数据为：", recPacket)
#         # IPv4中，头部信息占20bytes
#         header = recPacket[20: 28]
#         type, code, checksum, packetID, sequence = struct.unpack("!bbHHh", header)
#         # Echo-Reply: type == 0 匹配ID
#         if type == 0 and packetID == ID:
#             # struct模块可以将二进制数据转换为python数据类型
#             # calcsize()将字符串转化为字节数目
#             byte_in_double = struct.calcsize("!d")
#             timeSent = struct.unpack("!d", recPacket[28: 28 + byte_in_double])[0]
#             # timeSent：发送Echo请求的时间戳
#             delay = timeReceived - timeSent  # RTT往返时间
#             # TTL:生存时间 返回TTL的十进制整数值
#             ttl = ord(struct.unpack("!c", recPacket[8:9])[0].decode())
#             return (delay, ttl, byte_in_double)
#
#         timeLeft = timeLeft - howLongInSelect
#         if timeLeft <= 0:
#             return None
#
#
# # 构造 ICMP 报文，发送报文到目标地址
# def sendOnePing(mySocket, ID, sequence, destAddr):
#     # ICMP报文包含：type (8), code (8), checksum (16), id (16), sequence (16)
#     myChecksum = 0
#     # 构建一个ICMP报文头部：type=ICMP_ECHO_REQUEST code=0 checkSum=myChecksum ID,sequence匹配回显请求与回显响应
#     header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
#     # 建一个长度为8字节的数据部分，其中包含当前时间戳
#     data = struct.pack("!d", time.time())
#     # 计算完整数据包的校验和
#     myChecksum = checksum(header + data)
#     # 更新报文头部
#     header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
#     packet = header + data
#     # 将ICMP数据包发送给目的地址，注意此处发送的destAddr必须是元组类型：（destAddr,1）将其转换为元组类型
#     # 1是端口号，但事实上ICMP报文传输信息不需要端口号
#     # print("测试中", destAddr)
#     try:
#         mySocket.sendto(packet, (destAddr, 1))
#     except socket.gaierror as e:
#         print("请输入一个有效的IP地址！")
#         return
#
#
# # 执行一次 ping 操作，即发送 ICMP 报文并接收响应，返回延迟时间（RTT）
# def doOnePing(destAddr, ID, sequence, timeout):
#     # 返回ICMP协议对应的协议号
#     icmp = socket.getprotobyname("icmp")
#
#     # 创建了一个基于ICMP协议的原始socket
#     # socket.AF_INET：指定使用 IPv4 网络协议  socket.SOCK_RAW：指定创建原始套接字（raw socket
#     mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
#
#     sendOnePing(mySocket, ID, sequence, destAddr)
#     delay = receiveOnePing(mySocket, ID, sequence, destAddr, timeout)
#
#     mySocket.close()
#     return delay
#
#
# #  循环执行 doOnePing 函数，每隔 1 秒输出一次延迟时间
# def ping(host, timeout=1):
#     # 转换为主机对应的IP地址
#     dest = socket.gethostbyname(host)
#     print("Ping " + dest)
#
#     # 获取当前进程ID并转换为一个16位无符号整数值
#     myID = os.getpid() & 0xFFFF
#     loss = 0
#     total = 0
#     min_rrt = float("inf")
#     max_rrt = -float("inf")
#     recevied = 0
#     # 默认向服务端发送4次请求信息
#     for i in range(4):
#         result = doOnePing(dest, myID, i, timeout)
#         if not result:
#             print("请求超时")
#             loss += 1
#         else:
#             delay = int(result[0] * 1000)
#             ttl = result[1]
#             bytes = result[2]
#             total += delay
#             min_rrt = min(min_rrt, delay)
#             max_rrt = max(max_rrt, delay)
#             print("来自 " + dest + " 的回复" + ": 字节=" + str(bytes) + " 时间=" + str(delay) + "ms TTL=" + str(ttl))
#         time.sleep(1)
#
#     recevied = 4 - loss
#     print(dest + " 的 Ping 统计信息：")
#     print("数据包: 已发送 = " + str(4) + ", 已接受 = " + str(4 - loss) + ", 丢失 = " + str(loss))
#     if recevied > 0:
#         print("往返路程的估计时间（以毫秒为单位）:")
#         print("最短 = " + str(min_rrt) + "ms, 最长 = " + str(max_rrt) + "ms, 平均 = " + str(total / recevied) + "ms")
#     return
#
#
#
# def get_host_info(host_addr):
#     """"
#     获取相应ip地址对应的主机信息
#     """
#     try:
#         host_info = socket.gethostbyaddr(host_addr)
#     except socket.error as e:
#         display = '{0} (主机名不可得)'.format(host_addr)
#     else:
#         display = '{0} ({1})'.format(host_addr, host_info[0])
#     return display
#
#
# def build_packet():
#     """
#     构建ICMP报文，首部内容如下：
#     ————————————————————————————————————————
#     |type (8) | code (8) | checksum (16)   |
#     ————————————————————————————————————————
#     |        id (16)     |  seq (16)       |
#     ————————————————————————————————————————
#     """
#     # 先将检验和设置为0
#     myChecksum = 0
#     # 用进程号作标识
#     ID = os.getpid() & 0xffff
#     # 序列号
#     sequence = 1
#
#     # 打包出二进制首部
#     header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
#     # 以当前系统时间作为报文的数据部分
#     data = struct.pack("!d", time.time())
#     # 构建一个临时的数据报
#     # 利用原始数据报来计算真正的校验和
#     myChecksum = checksum(header + data)
#
#     # # 处理校验和的字节序列类型：主机序转换为网络序
#     # if sys.platform == 'darwin':
#     #     myChecksum = socket.htons(myChecksum) & 0xffff
#     # else:
#     #     myChecksum = socket.htons(myChecksum)
#
#     # 重新构建出真正的数据包
#     header = struct.pack("!bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, myChecksum, ID, sequence)
#     package = header + data
#     return package
#
#
#
# def tracert(host):
#     dest = socket.gethostbyname(host)
#     print("最多通过30个跃点追踪")
#     print("到", dest, "的路由：")
#
#     for ttl in range(1, MAX_HOPS):
#         for tries in range(0, TRIES):
#
#             # 创建icmp原始套接字
#             icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
#             icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))  # I表示4字节
#             icmp_socket.settimeout(TIMEOUT)
#
#             # 构建报文并发送
#             icmp_package = build_packet()
#             try:
#                 icmp_socket.sendto(icmp_package, (host, 1))
#             except socket.gaierror as e:
#                 print("Wrong!not a effective ip address!")
#                 return
#
#             # 进入阻塞态，等待接收ICMP超时报文/应答报文
#             start_time = time.time()
#             select.select([icmp_socket], [], [], TIMEOUT)
#             end_time = time.time()
#             # 计算阻塞的时间
#             during_time = end_time - start_time
#             if during_time >= TIMEOUT:
#                 print(" * * * 超时请求.")
#                 continue
#             else:
#                 ip_package, ip_info = icmp_socket.recvfrom(1024)
#                 # 从IP数据报中取出ICMP报文的首部，位置在20：28，因为IP数据报首部长度为20
#                 icmp_header = ip_package[20:28]
#
#                 # 解析ICMP数据报首部各字段
#                 after_type, after_code, after_checksum, after_id, after_sequence = struct.unpack("!bbHHh", icmp_header)
#                 # ip_info[0]:发送数据的IP地址
#                 # 想办法获取IP地址对应的主机信息（如果有的话）
#                 output = get_host_info(ip_info[0])
#
#                 if after_type == TYPE_ICMP_UNREACHED:  # 目的不可达
#                     print("目的不可达")
#                     break
#                 elif after_type == TYPE_ICMP_OVERTIME:  # 超时报文
#                     print(" %d rtt=%.0f ms %s" % (ttl, during_time * 1000, output))
#                     continue
#                 elif after_type == 0:  # 应答报文
#                     print(" %d rtt=%.0f ms %s" % (ttl, during_time * 1000, output))
#                     print("追踪完成！")
#                     return
#                 else:
#                     print("return type is %d , code is %d" % (after_type, after_code))
#                     print("追踪失败!")
#                     return
#
#
# # ping("www.baidu.com")
# host = input("please input a dest address:")
# ip = socket.gethostbyname(host)
# tracert(ip)