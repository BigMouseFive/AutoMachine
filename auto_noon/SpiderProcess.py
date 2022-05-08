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
        self.page_index = 1
        self.start_urls = []
        try:
            self.page_index = int(open(self.shop_name + "_page_size").read())
        except:
            pass
        self.handler = "parseHandler_b"
        if len(self.origin_start_urls) > 0:
            self.start_urls.append(self.origin_start_urls[0] + "&page=" + str(self.page_index))
        logger.info("前台,从第" + str(self.page_index) + "页开始爬取")

    def parse(self, response):
        shop_type = self.database.getShopType()
        add_headers = {}
        if shop_type == "ksa":
            add_headers = {"x-locale": "en-sa"}
        elif shop_type == "uae":
            add_headers = {"x-locale": "en-ae"}
        # for quote in response.xpath(".//div[@class='jsx-3152181095 productContainer']"):
        for quote in response.xpath(".//div[contains(@class, 'productContainer')]"):
            self.database.handlerStatus()
            time.sleep(random.uniform(0.5, 2.5))
            uri = ""
            if self.handler == "parseHandler_a":
                uri = "https://www.noon.com" + str(quote.xpath(".//a[contains(@class, 'product')]/@href").extract()[0])
            elif self.handler == "parseHandler_b" or self.handler == "parseHandler_c":
                uri = "https://www.noon.com/_svc/catalog/api/u/"
                uri += str(quote.xpath("./a/@href").extract()[0]) + "/product/"
                uri += str(quote.xpath("./a/@id").extract()[0].split("-")[-1]) + "/p"
            if uri is not None:
                uri = uri.split('?')[0]
                if self.handler == "parseHandler_a":
                    yield response.follow(uri, headers=add_headers, callback=self.parseHandler_a)
                elif self.handler == "parseHandler_b":
                    yield response.follow(uri, headers=add_headers, callback=self.parseHandler_b)
                elif self.handler == "parseHandler_c":
                    yield response.follow(uri, headers=add_headers, callback=self.parseHandler_c)

        # 获取下一页的url, （DEL::如果没有就从头开始）
        next_page_list = response.xpath(
            "//li[contains(@class, 'next')]//a[@class='arrowLink']/@aria-disabled").extract()
        if len(next_page_list) > 0:
            value = str(next_page_list[0])
        else:
            value = None
        if value is not None and value == "false":
            self.page_index = self.page_index + 1
            if self.page_index <= 50:
                with open(self.shop_name + "_page_size", "w") as f:
                    f.write(str(self.page_index))
                next_page = self.origin_start_urls[0] + "&page=" + str(self.page_index)
                yield response.follow(next_page, callback=self.parse)
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
        yield response.follow(next_page, callback=self.parse)

    def parseHandler_a(self, response):
        infos, gold_shop = self.getAllPirce_a(response)  # 获取所有的价格并以此形式返回{shop_name:[price, rating, fullfilled], ...}
        if gold_shop == "$Rt%6y":
            gold_shop = self.shop_name
        ean = response._get_url().split("/")[-2]  # EAN
        self.solutionNoon(ean, infos, gold_shop)

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

    def parseHandler_c(self, response):
        if not response.text:
            logger.info("前台,parseHandler_c: empty response")
            return
        try:
            res_json = json.loads(response.text)
            sku = res_json["product"]["sku"]
            if not sku: sku = ""
            brand = res_json["product"]["brand"]
            if not brand: brand = ""
            specifications = res_json["product"]["specifications"]
            model_name = " "
            model_number = " "
            for specification in specifications:
                if specification["code"] == "model_number":
                    model_number = specification["value"]
                if specification["code"] == "model_name":
                    model_name = specification["value"]

            logger.info("前台," + sku + "," + str(model_name) + "," + str(model_number))
        except ValueError:
            logger.info("前台,parseHandler_c: handler json error")
            return

    def getAllPirce_a(self, response):
        infos = {}
        gold_shop = "$Rt%6y"
        rows = response.xpath(".//ul[contains(@class, 'offersList')]/li")
        for row in rows:
            price = row.xpath(".//span[@class='value')]//text()").extract()[0]
            price = round(float(price), 2)
            shop_name = row.xpath(".//p[@class='jsx-1312782570')]//text()").extract()
            shop_name = str(shop_name[2]).lower()
            if gold_shop == "$Rt%6y":
                gold_shop = shop_name
            ret = row.xpath(".//div[contains(@class, 'container')]")
            is_fbn = False
            if len(ret) > 0:
                is_fbn = True
            rating = 100
            infos[shop_name] = [price, rating, is_fbn]
        if len(infos) == 0:
            price = response.xpath(
                ".//div[contains(@class, 'pdpPrice']//span[@class='value']//text())").extract()[0]
            price = round(float(price), 2)
            is_fbn = False
            ret = response.xpath(
                ".//div[@class='jsx-2490358733 shippingEstimatorContainer']//div[contains(@class, 'container')]")
            if len(ret) > 0:
                is_fbn = True
            rating = 100
            infos[self.shop_name] = [price, rating, is_fbn]
        return infos, gold_shop

    def getAllPirce_b(self, offers):
        infos = {}
        gold_shop = offers[0]["store_name"].lower()
        for offer in offers:
            # logger.info(offer)
            is_fbn = offer["is_fbn"] == 1
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
                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/70.0.3538.77 Safari/537.36")
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
