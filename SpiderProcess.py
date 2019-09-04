import sys
import scrapy.spiderloader
import scrapy.statscollectors
import scrapy.logformatter
import scrapy.dupefilters
import scrapy.squeues
import scrapy.extensions.spiderstate
import scrapy.extensions.corestats
import scrapy.extensions.telnet
import scrapy.extensions.logstats
import scrapy.extensions.memusage
import scrapy.extensions.memdebug
import scrapy.extensions.feedexport
import scrapy.extensions.closespider
import scrapy.extensions.debug
import scrapy.extensions.httpcache
import scrapy.extensions.statsmailer
import scrapy.extensions.throttle
import scrapy.core.scheduler
import scrapy.core.engine
import scrapy.core.scraper
import scrapy.core.spidermw
import scrapy.core.downloader
import scrapy.downloadermiddlewares.stats
import scrapy.downloadermiddlewares.httpcache
import scrapy.downloadermiddlewares.cookies
import scrapy.downloadermiddlewares.useragent
import scrapy.downloadermiddlewares.httpproxy
import scrapy.downloadermiddlewares.ajaxcrawl
import scrapy.downloadermiddlewares.decompression
import scrapy.downloadermiddlewares.defaultheaders
import scrapy.downloadermiddlewares.downloadtimeout
import scrapy.downloadermiddlewares.httpauth
import scrapy.downloadermiddlewares.httpcompression
import scrapy.downloadermiddlewares.redirect
import scrapy.downloadermiddlewares.retry
import scrapy.downloadermiddlewares.robotstxt
import scrapy.spidermiddlewares.depth
import scrapy.spidermiddlewares.httperror
import scrapy.spidermiddlewares.offsite
import scrapy.spidermiddlewares.referer
import scrapy.spidermiddlewares.urllength
import scrapy.pipelines
import scrapy.core.downloader.handlers.http
import scrapy.core.downloader.contextfactory
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import multiprocessing
from multiprocessing import Process
import random
import json
import time
from DataManager import DataManager


class QuotesSpider(scrapy.Spider):
    name = "goldcar"

    def __init__(self, shop_name=None, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.database = DataManager(shop_name)
        self.shop_name = shop_name.lower()
        self.start_urls = self.database.getScrapyUrl()
        self.page_index = 1
        # out = "抓取数据：" + self.start_urls[0]
        # print(out)

    def parse(self, response):
        handler = "parseHandler_b"
        add_headers = {
            "x-locale": "en-sa",
        }
        for quote in response.xpath(".//div[@class='jsx-2127843686 productContainer']"):
            self.database.handlerStatus()
            time.sleep(random.randint(0, 1))
            uri = ""
            if handler == "parseHandler_a":
                uri = "https://www.noon.com" + str(quote.xpath(".//a[@class='jsx-4244116889 product']/@href").extract()[0])
            elif handler == "parseHandler_b":
                uri = "https://www.noon.com/_svc/catalog/api/u/" + str(quote.xpath(".//a[@class='jsx-4244116889 "
                                                                                   "product']/@href").extract()[0])
            if uri is not None:
                uri = uri.split('?')[0]
                yield response.follow(uri, headers=add_headers, callback=self.parseHandler_b)

        # 获取下一页的url, （DEL::如果没有就从头开始）
        value = str(response.xpath(
            ".//div[@class='jsx-2341487112 paginationWrapper']//a[@class='nextLink']/@aria-disabled").extract()[0])
        if value is not None and value == "false":
            self.page_index = self.page_index + 1
            next_page = self.start_urls[0] + "?page=" + str(self.page_index)
            yield response.follow(next_page, callback=self.parse)

    def parseHandler_a(self, response):
        infos, gold_shop = self.getAllPirce_a(response)  # 获取所有的价格并以此形式返回{shop_name:[price, rating, fullfilled], ...}
        if gold_shop == "$Rt%6y":
            gold_shop = self.shop_name
        ean = response._get_url().split("/")[-2]  # EAN
        self.solutionNoon(ean, infos, gold_shop)

    def parseHandler_b(self, response):
        if not response.text:
            print("parseHandler_b: empty response")
            return
        try:
            res_json = json.loads(response.text)
            ean = res_json["product"]["sku"]
            variants = res_json["product"]["variants"]
            for variant in variants:
                try:
                    offers = variant["offers"]
                    variant_name = variant["variant"]
                    if len(offers) == 0:
                        continue
                    infos, gold_shop = self.getAllPirce_b(offers)
                    if self.shop_name in infos:
                        self.solutionNoon(ean, infos, gold_shop, variant_name)
                except ValueError:
                    print("parseHandler_b: handler variant error: " + str(variant))
        except ValueError:
            print("parseHandler_b: handler json error")
            return

    def getAllPirce_a(self, response):
        infos = {}
        gold_shop = "$Rt%6y"
        rows = response.xpath(".//ul[@class='jsx-1312782570 offersList']/li")
        for row in rows:
            price = row.xpath(".//span[@class='value']//text()").extract()[0]
            price = round(float(price), 2)
            shop_name = row.xpath(".//p[@class='jsx-1312782570']//text()").extract()
            shop_name = str(shop_name[2]).lower()
            if gold_shop == "$Rt%6y":
                gold_shop = shop_name
            ret = row.xpath(".//div[@class='jsx-3304762718 container']")
            is_fbn = False
            if len(ret) > 0:
                is_fbn = True
            rating = 100
            infos[shop_name] = [price, rating, is_fbn]
        if len(infos) == 0:
            price = response.xpath(
                ".//div[@class='jsx-2122863564 pdpPrice']//span[@class='value']//text()").extract()[0]
            price = round(float(price), 2)
            is_fbn = False
            ret = response.xpath(
                ".//div[@class='jsx-2490358733 shippingEstimatorContainer']//div[@class='jsx-3304762718 container']")
            if len(ret) > 0:
                is_fbn = True
            rating = 100
            infos[self.shop_name] = [price, rating, is_fbn]
        return infos, gold_shop

    def getAllPirce_b(self, offers):
        infos = {}
        gold_shop = offers[0]["store_name"].lower()
        for offer in offers:
            is_fbn = offer["is_fbn"] == 1
            rating = offer["seller_score"]
            price = offer["price"]
            if offer["sale_price"]:
                price = offer["sale_price"]
            infos[offer["store_name"].lower()] = [price, rating, is_fbn]
        return infos, gold_shop

    def solutionNoon(self, ean, infos, gold_shop, variant_name=""):
        if not self.database.isInWhiteList(ean, variant_name):
            out = "前台：不在白名单 " + time.strftime("%Y-%m-%d %H:%M:%S") + "   " + ean + "[" + variant_name + "]\t本店铺[" + str(infos[self.shop_name][0]) + "]\t" + \
              "购物车[" + str(infos[gold_shop][0]) + "][" + gold_shop + "]"
            print(out)
            return

        attr = self.database.getAttr(ean)
        out = time.strftime("%Y-%m-%d %H:%M:%S") + "   " + ean + "[" + variant_name + "]\t本店铺[" + str(infos[self.shop_name][0]) + "]\t" + \
              "购物车[" + str(infos[gold_shop][0]) + "][" + gold_shop + "]"
        self.database.spiderRecord(ean, infos[gold_shop][0], gold_shop, variant_name)
        if gold_shop in attr["my_shop"]:  # 黄金购物车是自家店铺
            out = "情况A " + out + "\t不修改"
        else:
            if infos[self.shop_name][2]:  # 是FBN产品
                diff1 = abs(infos[gold_shop][0] - infos[self.shop_name][0]) / infos[self.shop_name][0]
                if infos[gold_shop][2]:  # 黄金购物车是FBN
                    if diff1 > attr["percent"]:
                        out = "情况B " + out + "\t不修改"
                    else:
                        price = round(min(infos[gold_shop][0], infos[self.shop_name][0]) - attr["lowwer"], 2)
                        if price < attr["self_least_price"]:
                            out = "情况C " + out + "\t不修改"
                        else:
                            self.database.needToChangePrice(ean, price, gold_shop, variant_name)
                            out = "情况C " + out + "\t差价比[" + str(round(diff1 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
                else:
                    price = round(infos[self.shop_name][0] - attr["lowwer"], 2)
                    if price < min(infos[gold_shop][0], attr["self_least_price"]):
                        out = "情况D " + out + "\t不修改"
                    else:
                        self.database.needToChangePrice(ean, price, gold_shop, variant_name)
                        out = "情况D " + out + "\t改价为[" + str(price) + "]"

            else:
                least_price = 999999
                for info in infos.values():
                    if least_price > info[0]:
                        least_price = info[0]
                diff2 = abs(min(infos[gold_shop][0], least_price) - infos[self.shop_name][0]) / infos[self.shop_name][0]
                if diff2 > attr["percent"]:
                    out = "情况E " + out + "\t最低价[" + str(least_price) + "]\t" + "差价比[" + \
                          str(round(diff2 * 100, 2)) + "%]" + "不修改"
                else:
                    price = round(min(infos[gold_shop][0], least_price) - attr["lowwer"], 2)
                    if price < attr["self_least_price"]:
                        out = "情况F " + out + "\t最低价[" + str(least_price) + "]\t" + "不修改"
                    else:
                        self.database.needToChangePrice(ean, price, gold_shop, variant_name)
                        out = "情况F " + out + "\t最低价[" + str(least_price) + "]\t" + "差价比[" + \
                              str(round(diff2 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
        out = "前台：" + out
        print(out)

    '''
    def prase2(self, response):
        # 黄金购物车店铺名
        infos, gold_shop = self.getAllPirce(response)  # 获取所有的价格并以此形式返回{shop_name:[price, rating, fullfilled], ...}
        if gold_shop == "$Rt%6y":
            gold_shop = self.shop_name
        ean = response._get_url().split("/")[-2]  # EAN
        self_least_price = self.getAttr(ean)  # 获取改价参数，并返回此ean限制的最低价
        gold_price = infos[gold_shop][0]  # 黄金购物车价格
        self_price = infos[self.shop_name][0]  # 本店铺的price
        percent = round(((self_price - gold_price + self.lowwer) / self_price), 2)  # 差价比
        first_min_price = 999999  # 最低价
        second_min_price = 999999  # 第二低价
        first_min_shop = []  # 最低价的店铺
        second_min_shop = []  # 第二低价的店铺
        fbs_shop = []  # FBS店铺
        fbs_price = 999999  # FBS店铺中的最低价
        for key, info in infos.items():
            if info[0] < first_min_price:
                second_min_price = first_min_price
                first_min_price = info[0]
        for key, info in infos.items():
            if info[2]:
                fbs_shop.append(key)
            if first_min_price == info[0]:
                first_min_shop.append(key)
            if second_min_price == info[0]:
                second_min_shop.append(key)
        for value in fbs_shop:
            if value != self.shop_name:
                if fbs_price > infos[value][0]:
                    fbs_price = infos[value][0]
        self.solution(gold_shop, ean, self_least_price, infos, gold_price, self_price, percent,
                      first_min_price, second_min_price, first_min_shop, second_min_shop, fbs_shop, fbs_price)

    # 不修改情况：
    #       1、改价店铺是黄金购物车 and 【改价店铺的价格】不是最低价 （有买家提议可以适当考虑提价）
    #       2、自己的其他店铺（不包括改价店铺）是黄金购物车 and 【改价店铺的价格】不比【黄金购物车的价格】低
    #       3、其他店铺是黄金购物车 and 【黄金购物车的价格】比【改价店铺的价格】低 and 【差价比】超过【降价幅度】
    # TODO  4、【改价次数】超过【改价次数上限】 and 【总降价比】超过【总降价比上限】 这个规则放在修改进程中判断
    # 考虑提高价格:
    #       5、改价店铺是黄金购物车 and 【改价店铺的价格】是最低价 --> 要判断是否只有自己一人是最低价 1、只有自己一个人是最低价
    #       6、自己的其他店铺（不包括改价店铺）是黄金购物车 and 【改价店铺的价格】比【黄金购物车的价格】低 --> 改价为【黄金购物车的价格】
    #       7、其他店铺是黄金购物车 and 【黄金购物车的价格】比【改价店铺的价格】高 -->（方法1：在不超过差价比的情况下一直降价   方法2：由人工处理）
    # 考虑降低价格
    # ##要满足的条件##  【改价次数】不超过【改价次数上限】 and 【总降价比】不超过【总降价比上限】
    #       8、其他店铺是黄金购物车 and 【黄金购物车的价格】比【改价店铺的价格】低 and 【差价比】不超过【降价幅度】--> 改价为【黄金购物车的价格 - 降价】

    #

    def solution(self, gold_shop, ean, self_least_price, infos, gold_price, self_price, percent,
                 first_min_price, second_min_price, first_min_shop, second_min_shop, fbs_shop, fbs_price):
        percent = round(percent, 2)

        # 1
        if gold_shop == self.shop_name and self_price == gold_price and self_price > first_min_price:
            self.handler1(ean, self_price, first_min_price, gold_shop)
        # 2
        elif gold_shop != self.shop_name and gold_shop in self.my_shop and self_price >= gold_price:
            self.handler2(ean, self_price, gold_price, gold_shop)
        # 3
        elif gold_shop not in self.my_shop and gold_price < self_price and percent > self.percent:
            self.handler3(ean, self_price, gold_price, gold_shop, percent)
        # 5
        elif gold_shop == self.shop_name and self_price == first_min_price:
            self.handler5(ean, self_price, gold_shop, infos, first_min_price, second_min_price,
                          first_min_shop, second_min_shop, fbs_price)
        # 6
        elif gold_shop != self.shop_name and gold_shop in self.my_shop and self_price < gold_price:
            self.handler6(ean, self_price, gold_price, gold_shop)
        # 7
        elif gold_shop not in self.my_shop and gold_price > self_price:
            self.handler7(ean, self_price, gold_price, gold_shop, infos, self_least_price)
        # 8
        elif gold_shop not in self.my_shop and gold_price < self_price and percent <= self.percent:
            self.handler8(ean, self_price, gold_price, gold_shop, percent, self_least_price)

    def handler1(self, ean, self_price, first_min_price, gold_shop):
        out_str = "#1\t" + ean + ":" + "价格[" + str(self_price) + "]\t最低价[" + str(
            first_min_price) + "]\t本店铺[" + gold_shop + "]"
        print(out_str)

    def handler2(self, ean, self_price, gold_price, gold_shop):
        out_str = "#2\t" + ean + ":" + "价格[" + str(self_price) + "]\t黄金购物车价格[" + str(
            gold_price) + "]\t自家店铺[" + gold_shop + "]"
        print(out_str)

    def handler3(self, ean, self_price, gold_price, gold_shop, percent):
        out_str = "#3\t" + ean + ":" + "价格[" + str(self_price) + "]\t购物车[" + str(
            gold_price) + "]\t其他店铺[" + gold_shop + "]\t差价比[" + str(round(percent*100, 2)) + "%]"
        print(out_str)

    def handler5(self, ean, self_price, gold_shop, infos, first_min_price, second_min_price,
                 first_min_shop, second_min_shop, fbs_price):
        out_str = "#5\t" + ean + ":" + "价格[" + str(self_price) + "]\t最低价[" + str(
            first_min_price) + "]\t本店铺[" + gold_shop + "]\t"
        to_price = 0
        if infos[self.shop_name][2]:  # 是否是FBS
            if len(first_min_shop) == 1:  # 是否只有自己一家是最低价
                # 判断second_min_shop中是否有店铺是fbs
                for value in second_min_shop:
                    if infos[value][2]:
                        to_price = infos[value][0]
                        break
                memo = "改价店铺（FBS）是黄金购物车,且只有改价店铺一家是最低价(" + str(first_min_price) + ")," + \
                       "第二低价格(" + str(second_min_price) + ")中"
                if to_price == 0:
                    memo += "没有FBS店铺"
                    if fbs_price < 999999:
                        memo += ",FBS店铺中的最低价格是(" + str(fbs_price) + ")"
                else:
                    memo += "有FBS店铺"
                    to_price = to_price - self.lowwer
                    if to_price != self_price:
                        out_str += "改价为[" + str(to_price) + "]"
                        self.needToChangePrice(ean, to_price, gold_shop)
                self.sendNotice(ean, memo)
            else:
                flag1 = False
                for value in first_min_shop:
                    if infos[value][2]:
                        flag1 = True
                        break
                memo = "改价店铺（FBS）是黄金购物车,不止改价店铺一家是最低价(" + str(first_min_price) + ")," + \
                       "最低价格中"
                if not flag1:
                    memo += "没有FBS店铺"
                    if fbs_price < 999999:
                        memo += ",FBS店铺中的最低价格是(" + str(fbs_price) + ")"
                else:
                    memo += "有FBS店铺"
                self.sendNotice(ean, memo)
        else:  # 不是FBS
            if len(first_min_shop) == 1:  # 是否只有自己一家是最低价
                # 判断min_second_price_shop中是否有店铺是fbs
                for value in second_min_shop:
                    if infos[value][2]:
                        to_price = infos[value][0]
                        break
                memo = "改价店铺（非FBS）是黄金购物车,且只有改价店铺一家是最低价(" + str(first_min_price) + ")," + \
                       "第二低价格(" + second_min_price + ")中"
                if to_price == 0:
                    memo += "没有FBS店铺"
                    if fbs_price < 999999:
                        memo += ",FBS店铺中的最低价格是(" + str(fbs_price) + ")"
                else:
                    memo += "有FBS店铺"
                    to_price = to_price - self.lowwer
                    if to_price != self_price:
                        out_str += "改价为[" + str(to_price) + "]"
                        self.needToChangePrice(ean, to_price, gold_shop)
                self.sendNotice(ean, memo)
            else:
                flag1 = False
                for value in first_min_shop:
                    if infos[value][2]:
                        flag1 = True
                        break
                memo = "改价店铺（非FBS）是黄金购物车,不止改价店铺一家是最低价(" + str(first_min_price) + ")," + \
                       "最低价格中"
                if not flag1:
                    memo += "没有FBS店铺"
                    if fbs_price < 999999:
                        memo += ",FBS店铺中的最低价格是(" + str(fbs_price) + ")"
                else:
                    memo += "有FBS店铺"
                self.sendNotice(ean, memo)
        print(out_str)

    def handler6(self, ean, self_price, gold_price, gold_shop):
        out_str = "#6\t" + ean + ":" + "价格[" + str(self_price) + "]\t购物车[" + str(gold_price) + \
                  "]\t自家店铺[" + gold_shop + "]\t修改"
        print(out_str)
        self.needToChangePrice(ean, gold_price, gold_shop)

    def handler7(self, ean, self_price, gold_price, gold_shop, infos, self_least_price):
        out_str = "#7\t" + ean + ":" + "价格[" + str(self_price) + "]\t购物车[" + str(
            gold_price) + "]其他店铺[" + gold_shop + "]"
        if (not infos[gold_shop][2]) and infos[self.shop_name][2]:  # 黄金购物车不是FBS 自家店铺是FBS
            memo = "黄金购物车(" + gold_shop + ":" + str(infos[gold_shop][0]) + \
                   ")不是FBS, 改价店铺(" + infos[self.shop_name][0] + ")是FBS"
            self.sendNotice(ean, memo)
        else:
            to_price = self_price - self.lowwer
            if to_price < self_least_price:
                out_str += "改价[" + str(to_price) + "]" + "低于此EAN最低价限制[" + self_least_price + "]"
            else:
                out_str += "改价为[" + str(to_price) + "]"
                self.needToChangePrice(ean, to_price, gold_shop)
        print(out_str)

    def handler8(self, ean, self_price, gold_price, gold_shop, percent, self_least_price):
        out_str = "#8\t" + ean + ":" + "价格[" + str(self_price) + "]\t购物车[" + str(
            gold_price) + "]\t其他店铺[" + gold_shop + "]\t差价比[" + str(round(percent*100, 2)) + "%]\t"
        to_price = gold_price - self.lowwer
        if to_price < self_least_price:
            out_str += "改价[" + str(to_price) + "]" + "低于此EAN最低价限制[" + self_least_price + "]"
        else:
            out_str += "改价为[" + str(to_price) + "]"
            self.needToChangePrice(ean, to_price, gold_shop)
        print(out_str)
    '''


class SpiderProcess(multiprocessing.Process):
    def __init__(self, name):
        multiprocessing.Process.__init__(self)  # 重构了Process类里面的构造函数
        self.name = name

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        print("启动前台抓取任务")
        settings = get_project_settings()
        settings.set('USER_AGENT',
                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/70.0.3538.77 Safari/537.36")
        settings.set('LOG_FILE', "log.txt")
        settings.set('ROBOTSTXT_OBEY', False)
        process = CrawlerProcess(settings)
        process.crawl(QuotesSpider, shop_name=self.name)
        process.start()
        process.join()
        print("前台抓取数据一轮完成")
        count = random.randint(30, 70)
        database = DataManager(self.name)
        while count:
            database.handlerStatus()
            count -= 1
            time.sleep(1)

