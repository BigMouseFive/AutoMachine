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
import json
import time
import random
from auto_noon.DataManager import DataManager
from logger import logger


class QuotesSpider(scrapy.Spider):
    name = "goldcar"

    def __init__(self, shop_name=None, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.database = DataManager(shop_name)
        self.shop_name = shop_name.lower()
        self.origin_start_urls = self.database.getScrapyUrl()
        self.first_time = True
        self.page_index = 1
        self.start_urls = []
        try:
            self.page_index = int(open(self.shop_name + "_page_size").read())
        except:
            pass
        self.handler = "parseHandler_b"
        if len(self.origin_start_urls) > 0:
            self.start_urls.append(self.origin_start_urls[0] + "&page=" + str(self.page_index))
        # logger.info("前台,从第" + str(self.page_index) + "页开始爬取")

    def parse(self, response):
        shop_type = self.database.getShopType()
        add_headers = {}
        if shop_type == "ksa":
            add_headers = {"x-locale": "en-sa"}
        elif shop_type == "uae":
            add_headers = {"x-locale": "en-ae"}
        if self.first_time:
            next_page = self.origin_start_urls[0] + "&page=" + str(self.page_index)
            logger.info("前台,从第" + str(self.page_index) + "页开始爬取")
            yield response.follow(next_page, headers=add_headers, callback=self.parse)
            self.first_time = False
            return
        # 数据解析为json
        data = json.loads(response.body.decode("utf-8"))
        # 获取hits（产品信息）
        hits = []
        if "hits" in data and isinstance(data["hits"], list):
            hits = data["hits"]
        # 获取page页数上线
        nb_pages = None
        if "nbPages" in data:
            nb_pages = data["nbPages"]
        for hit in hits:
            self.database.handlerStatus()
            time.sleep(random.uniform(0.5, 2.5))
            uri = "https://www.noon.com/_svc/catalog/api/v3/u/"
            uri += hit["url"] + "/"
            uri += hit["sku"] + "/p"
            if uri is not None:
                yield response.follow(uri, headers=add_headers, callback=self.parseHandler_b)

        # 获取下一页的url, （DEL::如果没有就从头开始）
        if nb_pages is not None:
            self.page_index = self.page_index + 1
            if self.page_index <= nb_pages:
                with open(self.shop_name + "_page_size", "w") as f:
                    f.write(str(self.page_index))
                next_page = self.origin_start_urls[0] + "&page=" + str(self.page_index)
                yield response.follow(next_page, headers=add_headers, callback=self.parse)
                return
        with open(self.shop_name + "_page_size", "w") as f:
            f.write(str(1))
        logger.info("前台,抓取数据一轮完成")

        # 等待
        attr = self.database.getAttr("EMPTY")
        count = 2
        if attr["minute"] != 0:
            count = attr["minute"] * 60
        minute = 0
        while minute <= count:
            self.database.handlerStatus()
            minute += 1
            time.sleep(1)
            attr = self.database.getAttr("EMPTY")
            count = 2
            if attr["minute"] != 0:
                count = attr["minute"] * 60

        # 重新开始
        logger.info("前台,启动前台抓取任务")
        self.page_index = 1
        next_page = self.origin_start_urls[0] + "&page=" + str(self.page_index)
        logger.info("前台,从第" + str(self.page_index) + "页开始爬取")
        yield response.follow(next_page, headers=add_headers, callback=self.parse)

    def parseHandler_b(self, response):
        if not response.text:
            logger.info("前台,parseHandler_b: empty response")
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
                    logger.info("前台,parseHandler_b: handler variant error: " + str(variant))
        except ValueError:
            logger.info("前台,parseHandler_b: handler json error")
            return

    def getAllPirce_b(self, offers):
        infos = {}
        gold_shop = offers[0]["store_name"].lower()
        for offer in offers:
            # logger.info(offer)
            is_fbn = "fbn" in offer["flags"]
            rating = 0.99
            if "seller_score" in offer:
                rating = offer["seller_score"]
            price = offer["price"]
            if offer["sale_price"]:
                price = offer["sale_price"]
            infos[offer["store_name"].lower()] = [price, rating, is_fbn]
        return infos, gold_shop

    def solutionNoon(self, ean, infos, gold_shop, variant_name=""):
        if not self.database.isInWhiteList(ean, variant_name):
            out = "前台,不在白名单 " + ean + "[" + variant_name + "]\t本店铺[" + str(infos[self.shop_name][0]) + "]\t" + \
              "购物车[" + str(infos[gold_shop][0]) + "][" + gold_shop + "]"
            logger.info(out)
            return

        attr = self.database.getAttr(ean)
        out = ean + "[" + variant_name + "]\t本店铺[" + str(infos[self.shop_name][0]) + "]\t" + \
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
                            self.database.needToChangePrice(ean, attr["self_least_price"], gold_shop, variant_name)
                            out = "情况C " + out + "\t差价比[" + str(round(diff1 * 100, 2)) + "%]\t改价为[" + str(attr["self_least_price"]) + "]"
                        else:
                            self.database.needToChangePrice(ean, price, gold_shop, variant_name)
                            out = "情况C " + out + "\t差价比[" + str(round(diff1 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
                else:
                    price = round(infos[self.shop_name][0] - attr["lowwer"], 2)
                    if price < max(infos[gold_shop][0], attr["self_least_price"]):
                        self.database.needToChangePrice(ean, attr["self_least_price"], gold_shop, variant_name)
                        out = "情况D " + out + "\t改价为[" + str(attr["self_least_price"]) + "]"
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
                        self.database.needToChangePrice(ean, attr["self_least_price"], gold_shop, variant_name)
                        out = "情况F " + out + "\t最低价[" + str(least_price) + "]\t" + "差价比[" + \
                              str(round(diff2 * 100, 2)) + "%]\t改价为[" + str(attr["self_least_price"]) + "]"
                    else:
                        self.database.needToChangePrice(ean, price, gold_shop, variant_name)
                        out = "情况F " + out + "\t最低价[" + str(least_price) + "]\t" + "差价比[" + \
                              str(round(diff2 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
        out = "前台," + out
        logger.info(out)


class SpiderProcess(object):
    def __init__(self, name):
        self.name = name
        settings = get_project_settings()
        settings.set('USER_AGENT',
                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")
        settings.set('LOG_FILE', self.name + ".log")
        settings.set('ROBOTSTXT_OBEY', False)
        settings.set('DUPEFILTER_CLASS', 'scrapy.dupefilters.BaseDupeFilter')
        self.process = CrawlerProcess(settings)

    def crawl(self):
        d = self.process.crawl(QuotesSpider, shop_name=self.name)
        d.addBoth(lambda _: time.sleep(5))
        d.addBoth(lambda _: self.crawl())

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        logger.info("前台,启动前台抓取任务")
        self.crawl()
        self.process.start()
        logger.info("前台,抓取数据结束")
