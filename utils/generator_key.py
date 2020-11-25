import time


def generator(code, day, total):
    seconds = day * 3600 * 24
    nowtime = time.time() + 2208988800 # old version 2208888800
    endtime = int(nowtime) + seconds - 1996111725
    endTime = ""
    for i in range(10):
        part = int(endtime % 10)
        endTime = str(part) + endTime
        endtime /= 10
    endTime += str(int(total / 10))
    endTime += str(int(total % 10))

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

    decode[2] = int(endTime[4]) * 3
    decode[0] = int(endTime[5]) * 2 + 3
    decode[31] = int(endTime[6])
    decode[26] = int(endTime[7]) * 2 + 4
    decode[25] = int(endTime[1]) * 2 + int(endTime[7])
    decode[15] = int(endTime[8]) + 4
    decode[20] = int(endTime[3]) * 2 + int(endTime[8])
    decode[28] = int(endTime[9]) + 7
    decode[23] = int(endTime[2]) + int(endTime[9])
    decode[11] = int(endTime[10]) + int(endTime[5])
    decode[6] = int(endTime[11]) * 2 + 2
    decode[29] = int(endTime[0]) + int(endTime[3]) + int(endTime[11])

    decode[1] += int(endTime[5])
    decode[3] += int(endTime[6])
    decode[4] += int(endTime[7])
    decode[5] += int(endTime[8])
    decode[7] += int(endTime[9])
    decode[8] += int(endTime[6])
    decode[9] += int(endTime[7])
    decode[10] += int(endTime[8])
    decode[12] += int(endTime[8])
    decode[13] += int(endTime[5])
    decode[14] += int(endTime[7])
    decode[16] += int(endTime[9])
    decode[17] += int(endTime[7])
    decode[18] += int(endTime[6])
    decode[19] += int(endTime[6])
    decode[21] += int(endTime[5])
    decode[22] += int(endTime[8])
    decode[24] += int(endTime[9])
    decode[27] += int(endTime[7])
    decode[30] += int(endTime[5])

    code = ""
    for v in decode:
        v = int(v % 36)
        c = ord('A') + v - 10
        if 0 <= v <= 9:
            c = ord('0') + v
        code += chr(c)
    return code


print(generator("FIE56ED6XGDIIG7UI94W", 100, 2))
