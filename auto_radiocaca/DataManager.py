# -*- coding: utf-8 -*-
"""
        "id": 497,
        "name": "SpaceXNaut Dog",
        "image_url": "https://racawebsource.s3.us-east-2.amazonaws.com/nft/spacex_dog_img.jpg",
        "count": 1,
        "fixed_price": "2000000",
        "highest_price": "0",
        "start_time": 1634175707,
        "end_time": -1,
        "status": "active",
        "sale_type": "fixed_price",
        "token_id": "9966",
        "sale_address": "0x0c09911e03cCC3a31db761a7948203F4b6248d8a"
table:
    market_place
        int id # 编号
        string name
        int count # 个数
        double fixed_price # 单价
        int start_time
        string status
        string token_id
        string time #时间

    market_place_last_time
        string time # 时间
        int total # 总数

    buy_now
        string id # 编号
        string time #时间

"""
import threading
import sqlite3
DATABASE_PATH = "../radiocaca.db"


class DataManager:
    def __init__(self):
        self.lock = threading.Lock()

    def init_shop_dataBase(self):
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS 'market_place'(
                                id          INT     NOT NULL PRIMARY KEY,
                                count       INT     NOT NULL,
                                fixed_price DOUBLE  NOT NULL,
                                start_time  INT     NOT NULL,
                                status      TEXT    NOT NULL,
                                token_id    TEXT    NOT NULL,
                                time        TEXT    NOT NULL
                             );''')
        c.execute('''CREATE TABLE IF NOT EXISTS 'market_place_last_time' (
                                                        time    TEXT    NOT NULL PRIMARY KEY,
                                                        total   INT     NOT NULL
                                                     );''')
        c.execute('''CREATE TABLE IF NOT EXISTS 'buy_now' (
                                                id      TEXT    NOT NULL PRIMARY KEY,
                                                time    TEXT    NOT NULL
                                             );''')
        conn.commit()
        conn.close()
        self.lock.release()

    def update_market_place(self, market_place, stime, total):
        print("updateMarketPlace: " + str(total) + " [" + str(stime) + "]")
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        for item in market_place:
            conn.execute("REPLACE INTO 'market_place'(id, count, fixed_price, start_time, status, "
                         "token_id, time) VALUES (?, ?, ?, ?, ?, ?, ?);",
                         (item["id"], item["count"], item["fixed_price"], item["start_time"],
                          item["status"], item["token_id"], stime))
        conn.execute("REPLACE INTO 'market_place_last_time'(time, total) VALUES (?, ?);",
                     (stime, total))
        conn.commit()
        conn.close()
        self.lock.release()

    def del_market_place(self, m_ids):
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        for m_id in m_ids:
            conn.execute("DELETE from 'market_place' where id=?;", (m_id,))
        conn.commit()
        conn.close()
        self.lock.release()

    def add_buy_now(self, m_id, stime):
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("REPLACE INTO 'buy_now'(id, time) VALUES (?, ?);", (m_id, stime))
        conn.commit()
        conn.close()
        self.lock.release()

    def del_buy_now(self, m_id):
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("DELETE from 'buy_now' where id=?;", (m_id,))
        conn.commit()
        conn.close()
        self.lock.release()

    def get_first_buy_now(self):
        first_buy_now = None
        self.lock.acquire()
        conn = sqlite3.connect(DATABASE_PATH)
        ret = conn.execute("SELECT id, time FROM 'buy_now' LIMIT 1;").fetchall()
        if len(ret) > 0:
            first_buy_now = {
                "id": ret[0][0],
                "time": ret[0][1]
            }
        conn.close()
        self.lock.release()
        return first_buy_now