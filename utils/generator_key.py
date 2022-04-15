# coding=utf-8
import time


def generator(code, day, total):
    seconds = day * 3600 * 24
    nowtime = time.time() + 2208988800  # old version 2208888800 new version 2208988800
    end_time_one = int(nowtime) + seconds - 1996111725
    end_time = ""
    for i in range(10):
        part = int(end_time_one % 10)
        end_time = str(part) + end_time
        end_time_one /= 10
    end_time += str(int(total / 10))
    end_time += str(int(total % 10))

    decode = []
    for c in code:
        tmp = 0
        if ord('0') <= ord(c) <= ord('9'):
            tmp = ord(c) - ord('0')
        elif ord('A') <= ord(c) <= ord('Z'):
            tmp = ord(c) - ord('A') + 10
        decode.append(int(tmp))
    size = len(decode)
    for i in range(32 - size):
        decode.append(0)

    decode[1] = decode[1] - 9
    decode[3] = decode[3] - 4
    decode[4] = decode[4] - 4
    decode[5] = int(decode[5] / 2)
    decode[7] = decode[7] - 5
    decode[9] = decode[9] - 13
    decode[10] = decode[10] - 1
    decode[12] = decode[12] - 4
    decode[14] = decode[14] - 6
    decode[16] = decode[16] - 3
    decode[19] = int(decode[19] / 2)

    decode[0] = decode[19] * 2 + decode[1]
    decode[2] = decode[1] * 3 + decode[12]
    decode[6] = decode[16] + 8 + decode[3]
    decode[8] = decode[1] * 4 + decode[5]
    decode[11] = decode[4] * 4 + decode[19]
    decode[13] = decode[10] + 5 + decode[4]
    decode[15] = decode[14] + 8 + decode[12]
    decode[18] = decode[1] * 3 + decode[7]
    decode[20] = decode[7] * decode[12] + decode[1]
    decode[21] = decode[14] * decode[1] + decode[4]
    decode[22] = decode[17] * decode[3] + decode[19]
    decode[23] = decode[12] * decode[16] + decode[5]
    decode[24] = decode[1] * decode[5] + decode[9]
    decode[25] = decode[7] * decode[16] + decode[10]
    decode[26] = decode[3] * decode[1] + decode[17]
    decode[27] = decode[9] * decode[4] + decode[7]
    decode[28] = decode[4] * decode[16] + decode[12]
    decode[29] = decode[9] * decode[3] + decode[14]
    decode[30] = decode[19] * decode[10] + decode[1]
    decode[31] = decode[19] * decode[9] + decode[4]

    decode[7] += 4
    decode[14] += 3
    decode[12] += 6
    decode[1] += 8
    decode[5] += 4
    decode[4] *= 6
    decode[9] += 7
    decode[19] += 8
    decode[17] += 6
    decode[3] *= 7
    decode[16] += 2
    decode[10] += 5

    decode[2] = int(end_time[4]) * 3
    decode[0] = int(end_time[5]) * 2 + 3
    decode[31] = int(end_time[6])
    decode[26] = int(end_time[7]) * 2 + 4
    decode[25] = int(end_time[1]) * 2 + int(end_time[7])
    decode[15] = int(end_time[8]) + 4
    decode[20] = int(end_time[3]) * 2 + int(end_time[8])
    decode[28] = int(end_time[9]) + 7
    decode[23] = int(end_time[2]) + int(end_time[9])
    decode[11] = int(end_time[10]) + int(end_time[5])
    decode[6] = int(end_time[11]) * 2 + 2
    decode[29] = int(end_time[0]) + int(end_time[3]) + int(end_time[11])

    decode[1] += int(end_time[5])
    decode[3] += int(end_time[6])
    decode[4] += int(end_time[7])
    decode[5] += int(end_time[8])
    decode[7] += int(end_time[9])
    decode[8] += int(end_time[6])
    decode[9] += int(end_time[7])
    decode[10] += int(end_time[8])
    decode[12] += int(end_time[8])
    decode[13] += int(end_time[5])
    decode[14] += int(end_time[7])
    decode[16] += int(end_time[9])
    decode[17] += int(end_time[7])
    decode[18] += int(end_time[6])
    decode[19] += int(end_time[6])
    decode[21] += int(end_time[5])
    decode[22] += int(end_time[8])
    decode[24] += int(end_time[9])
    decode[27] += int(end_time[7])
    decode[30] += int(end_time[5])

    code = ""
    for v in decode:
        v = int(v % 36)
        c = ord('A') + v - 10
        if 0 <= v <= 9:
            c = ord('0') + v
        code += chr(c)
    return code


def degenerator(register_code):
    register_code_int = []
    for i in range(len(register_code)):
        if '9' >= register_code[i] >= '0':
            register_code_int.append(ord(register_code[i]) - ord('0'))
        elif 'Z' >= register_code[i] >= 'A':
            register_code_int.append(ord(register_code[i]) - ord('A') + 10)
        elif 'z' >= register_code[i] >= 'a':
            register_code_int.append(ord(register_code[i]) - ord('a') + 10)
    end_time = [0] * 32
    end_time[4] = register_code_int[2] / 3
    end_time[5] = (register_code_int[0] - 3) / 2
    end_time[6] = register_code_int[31]
    end_time[7] = (register_code_int[26] - 4) / 2
    end_time[1] = (register_code_int[25] - end_time[7]) / 2
    end_time[8] = register_code_int[15] - 4
    end_time[3] = (register_code_int[20] - end_time[8]) / 2
    end_time[9] = register_code_int[28] - 7
    end_time[2] = register_code_int[23] - end_time[9]
    end_time[10] = register_code_int[11] - end_time[5]
    end_time[11] = (register_code_int[6] - 2) / 2
    end_time[0] = register_code_int[29] - end_time[3] - end_time[11]
    end_time_one = 0
    for i in range(10):
        end_time_one = end_time_one * 10 + end_time[i]
    nowtime = time.time() + 2208988800
    seconds = end_time_one - nowtime + 1996111725
    days = seconds / 3600 / 24
    total = 0
    for i in range(10, 12):
        total = total * 10 + end_time[i]
    return int(round(days, 0)), int(seconds), int(total)


print(generator("FIE56ED6XGDIIG7UI94W", 3666, 1))  # 台式机
print(generator("HFAJI6NKNEG556GD5FO4", 242, 1))  # gg 61.153.184.9  2021-01-11
print(generator("YFS5I61KCSA55NGD54IC", 366, 1))  # gg 115.220.1.39  2021-01-11
print(generator("7EGKII165SDKK27XJDDA", 30, 1))  # 罗伍   2021-01/-12
print(generator("MCADAGNA8MFK8SJQD4WM", 30, 1))  # 罗伍   2021-01-18
print(generator("YFAHI6WKMN4551GD5EIC", 366, 1))  # gg 139.9.184.81  2021-01-21
print(generator("TDEH40IA9N4D9988398K", 61, 1))  # Bruce 111.229.193.250  2021-02-05
print(generator("LDE640CAXH4D9T8D8DBS", 366, 1))  # gg 106.52.68.62  2021-02-20
print(generator("4D88408ACDED9K8A54HQ", 366, 1))  # gg 152.136.187.93  2021-02-20  替换111.229.172.80
print(generator("1D2840LAJQCD9J8A5BH8", 250, 1))  # bruce 150.158.173.233 2021-03-01
print(generator("BD8D40DADIED958B61WE", 38, 1))  # bruce 82.156.102.232 2021-03-01
print(generator("ABR9ICP6SG977Q7K94GS", 41, 2))  # 苘子 2021-03-31
print(generator("YBCDIMYBMPCZJPBM6AXI", 30, 1))  # Bruce 2021-03-24
print(generator("8G695SPF8TBSG2JUBCPC", 30, 1))  # noon卖家 will介绍 2021-04-02
print(generator("8AIBHAM6AE2JJZ7ND6MQ", 62, 2))  # tina 2021-04-19
print(generator("GAC7HAR60JCJJP7LB4AE", 62, 2))  # tina 2021-04-19 替换电脑
print(generator("BMYCCEHJ9E9AEGFOC924", 60, 1))  # nancy 2021-04-20  第一次使用时间2020-06-20
print(generator("YBCDIMYBMPCZJPBM6AXI", 90, 1))  # Bruce 2021-04-24
print(generator("8G695SPF8TBSG2JUBCPC", 30, 1))  # noon卖家 will介绍 2021-05-08
print(generator("BD8D40DADIED958B61WE", 31, 1))  # bruce 82.156.102.232 2021-05-14
print(generator("ABR9ICP6SG977Q7K94GS", 90, 2))  # 苘子 2021-05-10
print(generator("2FJ7I6M5ED715D6E6294", 142, 1))  # gg 139.9.184.81  2021-01-21
print(generator("LNJ79QL8XL3DH2F1J5CU", 90, 1))  # 友庆 2021-07-02
print(generator("BD8D40DADIED958B61WE", 30, 1))  # Bruce 82.156.102.232 2021-06-16
print(generator("HCSJBEN65L87BCFPD1AU", 2, 1))  # 罗伍 2021-07-23
print(generator("LNJ79QL8XL3DH2F1J5CU", 90, 1))  # 友庆 2021-07-02
print(generator("DDEB40BANGGD9Z8C77Q8", 42, 1))  # gg 119.45.135.40 2021-08-01 替换61.153.184.9  2021-01-11
print(generator("SDQ940HA2M8D9E8FAAKE", 166, 1))  # gg 119.45.135.122 2021-08-01 替换115.220.1.39  2021-01-11
print(generator("VD5540HAHMDD9T894D8G", 207, 1))  # gg 119.45.116.129 2021-08-01 替换152.136.1 vb87.93  2021-02-20
print(generator("0LICIQXDUOGDDB7P7EWC", 91, 1))  # 李秋生 2021-08-12
print(generator("WEIG52OBIS5IAB9MG26A", 365, 1))  # nancy 2021-10-16
print(generator("PEFE52HBLLGIAA9LF90G", 365, 1))  # nancy 2021-10-16
print(generator("2FJ7I6M5ED715D6E6294", 368, 1))  # gg 39.104.76.234 2021-10-30
print(generator("0LICIQXDUOGDDB7P7EWC", 90, 1))  # 李秋生 2021-11-16
print(generator("NAXD5GH6BL7JJ77QD7SW", 60, 1))  # 你好，了解改价 2022-04-15
