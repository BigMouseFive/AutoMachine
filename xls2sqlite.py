# -*- coding: utf-8 -*-
import xlrd
import xlwt
import os
import sys
import sqlite3


class X2S:
    def __init__(self, src, dst):
        try:
            self.xls = xlrd.open_workbook(src)
            print("打开表格[" + src + "]")
        except:
            print("无法打开表格[" + src + "]")
            # os.system("pause")
            exit(-1)
        self.dst = dst

    def addWhiteList(self, shop_name):
        conn = sqlite3.connect(self.dst)
        try:
            sheet = self.xls.sheet_by_index(0)
            count = 0
            for i in range(0, sheet.nrows):
                v = sheet.cell(i, 0).value
                if len(v) == 10 and v[0] == 'N':
                    count += 1
                    conn.execute("REPLACE INTO 'whiteList' (shop, ean, variant_name) values(?,?,'')", (shop_name, v))
                    print(str(count) + ":" + v)
            conn.commit()
            print("共获取到" + str(count) + "个")
        except:
            raise
            print("获取表格内容错误")
            conn.close()
            # os.system("pause")
            exit(-1)
        conn.close()

    def addWhiteShop(self, shop_name):
        my_shop = []
        try:
            sheet = self.xls.sheet_by_index(0)
            count = 0
            for i in range(0, sheet.nrows):
                v = sheet.cell(i, 0).value
                if len(v) > 0:
                    my_shop.append(v)
                    count += 1
                    print(str(count) + ":" + v)
        except:
            print("获取表格内容错误")
            # os.system("pause")
            exit(-1)

        conn = sqlite3.connect(self.dst)
        try:
            ret = conn.execute("select my_shop from 'CPAttr' where shop=?;", (shop_name,)).fetchall()
            if len(ret) <= 0:
                raise ValueError
            if len(ret[0][0]) > 0:
                my_shop += ret[0][0].split(",")
            my_shop = ",".join(i for i in set(my_shop))
            conn.execute("update 'CPAttr' set my_shop=? where shop=?;", (my_shop, shop_name))
            conn.commit()
        except:
            print("保存表格内容错误")
            conn.close()
            # os.system("pause")
            exit(-1)
        conn.close()

    def addProductAttr(self, shop_name):
        conn = sqlite3.connect(self.dst)
        try:
            sheet = self.xls.sheet_by_index(0)
            count = 0
            for i in range(0, sheet.nrows):
                v1 = sheet.cell(i, 0).value
                v2 = sheet.cell(i, 1).value
                v3 = sheet.cell(i, 2).value
                try:
                    v2 = float(v2)
                    v3 = int(v3)
                    conn.execute("REPLACE INTO 'CPComplexAttr'(shop, ean, least_price, max_times) VALUES (?, ?, ?, ?);",(shop_name, v1, v2, v3))
                    count += 1
                    print(str(count) + ":" + str(v1) + "," + str(v2) + "," + str(v3))
                except:
                    print("表格内容错误，第" + str(i+1) + "行")
        except:
            print("获取表格内容错误")
            conn.close()
            # os.system("pause")
            exit(-1)
        conn.commit()
        conn.close()


class S2X:
    def __init__(self, src, dst):
        if os.path.exists(dst):
            os.remove(dst)
        try:
            self.xls = xlwt.Workbook(encoding='utf-8')
            print("创建表格[" + dst + "]")
        except:
            print("创建表格[" + src + "]失败")
            # os.system("pause")
            exit(-1)
        self.src = src
        self.dst = dst

    def exportGoldCar(self):
        conn = sqlite3.connect(self.src)
        ret = []
        try:
            ret = conn.execute("select ean, variant_name, price, shop from 'record';").fetchall()
        except:
            conn.close()
            print("获取购物车信息失败")
            # os.system("pause")
            exit(-1)
        conn.close()

        try:
            sheet = self.xls.add_sheet('record')
            sheet.write(0, 0, label="sku")
            sheet.write(0, 1, label="variant")
            sheet.write(0, 2, label="price")
            sheet.write(0, 3, label="shop")

            for i in range(1, len(ret)):
                sheet.write(i, 0, label=ret[i-1][0])
                sheet.write(i, 1, label=ret[i-1][1])
                sheet.write(i, 2, label=ret[i-1][2])
                sheet.write(i, 3, label=ret[i-1][3])
            self.xls.save(self.dst)
            print("导出到表格成功")
        except:
            print("导出到表格失败")
            # os.system("pause")
            exit(-1)

    def exportChangePrice(self):
        conn = sqlite3.connect(self.src)
        ret = []
        try:
            ret = conn.execute("select time_change, ean, variant_name, price from 'change_record' "
                               "order by time_change desc limit 10000;").fetchall()
        except:
            conn.close()
            print("获取改价信息失败")
            # os.system("pause")
            exit(-1)
        conn.close()

        try:
            sheet = self.xls.add_sheet('change_record')
            sheet.write(0, 0, label="time")
            sheet.write(0, 1, label="ean")
            sheet.write(0, 2, label="variant_name")
            sheet.write(0, 3, label="price")

            for i in range(1, len(ret)):
                sheet.write(i, 0, label=ret[i-1][0])
                sheet.write(i, 1, label=ret[i-1][1])
                sheet.write(i, 2, label=ret[i-1][2])
                sheet.write(i, 3, label=ret[i-1][3])
            self.xls.save(self.dst)
            print("导出到表格成功")
        except:
            print("导出到表格失败")
            #  os.system("pause")
            exit(-1)


os.system("title AutoMachine Helper")
try:
    method = sys.argv[1]
    if method == "GoldCar":
        # 注意 xlwt 是以xls方式保存表格的 所以保存的文件名后缀得是xls
        s2x = S2X(sys.argv[2], sys.argv[3])
        s2x.exportGoldCar()
    elif method == "WhiteShop":
        x2s = X2S(sys.argv[2], sys.argv[3])
        x2s.addWhiteShop(sys.argv[4])
    elif method == "WhiteList":
        x2s = X2S(sys.argv[2], sys.argv[3])
        x2s.addWhiteList(sys.argv[4])
    elif method == "ProductAttr":
        x2s = X2S(sys.argv[2], sys.argv[3])
        x2s.addProductAttr(sys.argv[4])
    elif method == "ChangePrice":
        s2x = S2X(sys.argv[2], sys.argv[3])
        s2x.exportChangePrice()
except:
    print("出现异常")
    # os.system("pause")
    exit(-1)

# a = X2S("C:/Users/79054/Desktop/record.xls", "D:/Utils/AutoMachine/VisualStudio2013WorkPlatform/lemon01/x64/Debug/DataBase.db")
# a.addWhiteList("BuyMore")
# a = S2X("D:/Utils/AutoMachine/VisualStudio2013WorkPlatform/automachine/pak_installer/dist/deprecated/BuyMore.db", "C:/Users/79054/Desktop/record.xls")
# a.exportGoldCar()
