# -*- coding: utf-8 -*-
import threading
import sqlite3
import time
import os
# 'untreated' ean reason
# 'CPComplexAttr' shop ean least_price max_times
# 'CPAttr' shop minute max_times max_percent percent lowwer control white_list_enable


class DataManager:
    def __init__(self, name):
        self.name = name
        self.lock = threading.Lock()

    def initShopDataBase(self):
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS 'item';")
        c.execute('''CREATE TABLE 'item'
                               (ean       TEXT    NOT NULL,
                                variant_name TEXT NOT NULL DEFAULT '',
                                price     DOUBLE  NOT NULL,
                                shop      TEXT    NOT NULL,
                                primary key (ean, variant_name));''')
        c.execute("DROP TABLE IF EXISTS 'notice';")
        c.execute('''CREATE TABLE 'notice'
                                       (ean    TEXT  NOT NULL,
                                        variant_name TEXT NOT NULL DEFAULT '',
                                        memo   TEXT,
                                        primary key (ean, variant_name));''')
        c.execute("DROP TABLE IF EXISTS 'record';")
        c.execute('''CREATE TABLE 'record'
                                   (ean       TEXT    NOT NULL,
                                    variant_name TEXT NOT NULL DEFAULT '',
                                    price     DOUBLE  NOT NULL,
                                    shop      TEXT    NOT NULL,
                                    primary key (ean, variant_name));''')
        c.execute('''CREATE TABLE IF NOT EXISTS 'white_list'
                                   (ean       TEXT    NOT NULL,
                                    variant_name TEXT NOT NULL DEFAULT '',
                                    primary key (ean, variant_name));''')
        conn.commit()
        conn.close()
        self.lock.release()

    def getAttr(self, ean):
        self.lock.acquire()
        attr = {"self_least_price": 0, "minute": 0,
                "max_times": 5, "max_percent": 0.2,
                "percent": 0.1, "lowwer": 0,
                "control": 0, "my_shop": [str(self.name).lower()]}
        conn = sqlite3.connect("DataBase.db")
        # 通用改价参数
        try:
            ret = conn.execute(
                "select minute,max_times,max_percent,percent,lowwer,control,my_shop from 'CPAttr' where shop=?;",
                (self.name,)).fetchall()
            if len(ret) > 0:
                attr["minute"] = ret[0][0]
                attr["max_times"] = ret[0][1]
                attr["max_percent"] = ret[0][2]
                attr["percent"] = ret[0][3]
                attr["lowwer"] = ret[0][4]
                attr["control"] = ret[0][5]
                attr["my_shop"] += ret[0][6].lower().strip().split(",")
        except:
            raise

        # 具体某个产品的最低价
        try:
            ret = conn.execute("select least_price from 'CPConplexAttr' where ean=? and shop=?;",
                               (ean, self.name)).fetchall()
            if len(ret) > 0:
                attr["self_least_price"] = ret[0][0]
        except:
            attr["self_least_price"] = 0

        conn.close()
        self.lock.release()
        return attr

    def getScrapyUrl(self):
        self.lock.acquire()
        url = ["https://www.noon.com/saudi-en/"]
        conn = sqlite3.connect("DataBase.db")
        try:
            ret = conn.execute("select shop_id from 'shopInfo' where shop=?;", (self.name,)).fetchall()
            if len(ret) > 0:
                url[0] = url[0] + ret[0][0]
        except:
            url = []
        conn.close()
        self.lock.release()
        return url

    def spiderRecord(self, ean, price, gold_shop, variant_name):
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        conn.execute("REPLACE INTO 'record'(ean, variant_name, price, shop) VALUES (?, ?, ?, ?);",
                     (ean, variant_name, price, gold_shop))
        conn.commit()
        conn.close()
        self.lock.release()

    def isInWhiteList(self, ean, variant_name):
        # 判断是否在白名单
        self.lock.acquire()
        conn = sqlite3.connect("DataBase.db")
        ret = conn.execute("select white_list_enable from 'CPAttr' where shop=?", (self.name,)).fetchall()
        if len(ret) <= 0 or ret[0][0] == 0:
            conn.close()
            self.lock.release()
            return True
        conn.close()
        flag = False
        conn = sqlite3.connect(self.name + ".db")
        ret = conn.execute("select * from 'white_list' where ean=? and (variant_name=? or ?='');",
                           (ean, variant_name, variant_name)).fetchall()
        if len(ret) > 0:
            flag = True
        conn.close()
        self.lock.release()
        return flag

    def needToChangePrice(self, ean, price, gold_shop, variant_name):
        # 将需要修改的添加到item表中
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        conn.execute("REPLACE INTO 'item'(ean, variant_name, price, shop) VALUES (?, ?, ?, ?);",
                     (ean, variant_name, price, gold_shop))
        conn.commit()
        conn.close()
        self.lock.release()

    def sendNotice(self, ean, memo, variant_name):
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        conn.execute("REPLACE INTO 'notice'(ean, variant_name, memo) VALUES (?, ?, ?);", (ean, variant_name, memo))
        conn.commit()
        conn.close()
        self.lock.release()

    def getAccountAndPassword(self):
        a, p = ["account", "password"]
        self.lock.acquire()
        conn = sqlite3.connect("DataBase.db")
        ret = conn.execute("select account, password from 'shopInfo' where shop=?;", (self.name,)).fetchall()
        if len(ret) > 0:
            a, p = ret[0][0], ret[0][1]
        conn.close()
        self.lock.release()
        return a, p

    def getFirstNeedChangeItem(self):
        e, p, v = "ean", "price", "variant_name"
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        ret = conn.execute("SELECT ean, price, variant_name FROM 'item' LIMIT 1;").fetchall()
        if len(ret) > 0:
            e, p, v = ret[0][0], ret[0][1], ret[0][2]
        conn.close()
        self.lock.release()
        return e, p, v

    def finishOneChangeItem(self, ean, price, variant_name):
        self.lock.acquire()
        conn = sqlite3.connect(self.name + ".db")
        conn.execute("DELETE from 'item' where ean=? and variant_name=? and price=?;", (ean, variant_name, price))
        conn.commit()
        conn.close()
        self.lock.release()

    def getControlStatus(self):
        self.lock.acquire()
        status = "unknow"
        conn = sqlite3.connect("DataBase.db")
        try:
            ret = conn.execute("select control from 'CPAttr' where shop=?;", (self.name,)).fetchall()
            if len(ret) > 0:
                if ret[0][0] == 0:
                    status = "stop"
                elif ret[0][0] == 1:
                    status = "play"
                elif ret[0][0] == 2:
                    status = "pause"
        except:
            status = "unknow"
        conn.close()
        self.lock.release()
        return status

    def handlerStatus(self):
        while True:
            status = self.getControlStatus()
            if status == "unknow":
                time.sleep(0.1)
                continue
            elif status == "stop":
                os._exit(0)
            elif status == "play":
                return
            elif status == "pause":
                time.sleep(1)
