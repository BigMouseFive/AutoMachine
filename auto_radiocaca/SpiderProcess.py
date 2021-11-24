import traceback
import json
import time
import requests
from auto_radiocaca.DataManager import DataManager


class RadiocacaSpider(object):
    def __init__(self):
        self.database = DataManager()
        self.database.init_shop_dataBase()
        self.page_index = 1

    def get_total(self):
        print("get_total: http://market-api.radiocaca.com/nft-sales")
        response = requests.get("http://market-api.radiocaca.com/nft-sales")
        try:
            data = json.loads(response.text)
            return data["total"]
        except:
            traceback.print_exc()
        return 0

    def get_market_place(self, page_size):
        print("get_market_place: http://market-api.radiocaca.com/nft-sales?pageSize=" + str(page_size))
        response = requests.get("http://market-api.radiocaca.com/nft-sales?pageSize=" + str(page_size))
        try:
            data = json.loads(response.text)
            stime = time.strftime("%Y%m%dT%H%M%SZ", time.localtime())
            self.database.update_market_place(data["list"], stime, len(data["list"]))
            return data["list"]
        except:
            traceback.print_exc()
        return []


if __name__ == '__main__':
    radiocaca_spider = RadiocacaSpider()
    total = radiocaca_spider.get_total()
    print("total: " + str(total))
    market_place = radiocaca_spider.get_market_place(total)
    print("total market_place size: " + str(len(market_place)))
    with open("market_place", "w+") as f:
        f.write(json.dumps(market_place))


