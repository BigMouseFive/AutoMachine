scores = [
    [90, 5],
    [70, 3],
    [70, 1],
    [84, 3],
    [60, 1],
    [80, 1.5],
    [77, 2],
    [85, 0.5],
    [94, 2],
    [75, 1],
    [91, 0.5],
    [89, 5],
    [73, 4],
    [72, 1.5],
    [78, 1],
    [80, 0.5],
    [85, 1],
    [84, 1],
    [82, 2],
    [77, 3],
    [91, 1],
    [80, 2],
    [76, 3],
    [89, 0.5],
    [93, 2],
    [95, 1.5],
    [93, 1],
    [96, 2],
    [96, 2],
    [88, 4],
    [83, 3],
    [93, 3],
    [80, 0.5],
    [95, 0.5],
    [81, 3],
    [85, 1],
    [82, 2],
    [88, 6],
    [90, 0.5],
    [66, 2],
    [91, 1.5],
    [90, 3],
    [86, 3],
    [90, 0.5],
    [93, 0.5],
    [86, 2],
    [80, 1],
    [87, 2],
    [80, 3],
    [90, 0.5],
    [87, 2],
    [94, 1.5],
    [88, 3],
    [86, 3],
    [93, 2],
    [95, 0.5],
    [61, 2],
    [67, 2],
    [95, 3],
    [89, 3],
    [93, 2],
    [78, 3],
    [95, 2],
    [88, 1.5],
    [95, 0.5],
    [83, 0.5],
    [95, 1],
    [93, 1],
    [86, 2],
    [86, 1],
    [90, 2],
    [90, 1],
    [94, 1],
    [73, 1],
    [85, 2],
    [94, 1],
    [73, 1],
    [85, 0.5],
    [92, 1.5],
    [80, 2],
    [87, 5],
    [77, 10]
]
t1 = 0
t2 = 0
for score in scores:
    point = float(score[1])
    t2 += point
    if score[0] >= 90:
        t1 += 4.0 * point
    elif score[0] >= 85:
        t1 += 3.7 * point
    elif score[0] >= 82:
        t1 += 3.3 * point
    elif score[0] >= 78:
        t1 += 3.0 * point
    elif score[0] >= 75:
        t1 += 2.7 * point
    elif score[0] >= 71:
        t1 += 2.3 * point
    elif score[0] >= 66:
        t1 += 2.0 * point
    elif score[0] >= 62:
        t1 += 1.7 * point
    elif score[0] >= 60:
        t1 += 1.3 * point

print(round(t1 / t2, 2))
