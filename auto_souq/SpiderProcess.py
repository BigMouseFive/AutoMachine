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
        for quote in response.xpath(".//div[@class='column column-block block-grid-large single-item']"):
            self.database.handlerStatus()
            time.sleep(random.randint(1, 3))
            data_id = quote.xpath(".//a[@class='img-link quickViewAction sPrimaryLink']/@data-id").extract()[0] + "/u/"
            data_img = str(quote.xpath(".//a[@class='img-link quickViewAction sPrimaryLink']/@data-img").extract()[0]).split("item_L_")[-1].split("_")[0] + "/i/?ctype=dsrch"
            uri = str(quote.xpath(".//a[@class='img-link quickViewAction sPrimaryLink']/@href").extract()[0]).replace(data_id, data_img)
            if uri is not None:
                yield response.follow(uri, callback=self.parseHandler1)

            # 获取下一页的url, （DEL::如果没有就从头开始）
        next_page = response.xpath(".//li[@class='pagination-next goToPage']/a/@href").extract()
        if next_page is not None and len(next_page) > 0:
            next_page = next_page[0].replace("page=", "section=2&page=")
            yield response.follow(next_page, callback=self.parse)

    def parseHandler1(self, response):
        if not response.text:
            print("parseHandler_b: empty response")
            return
        gold_shop = str(response.xpath(".//span[@class='unit-seller-link']//b//text()").extract()[0]).lower()
        ean = str(response.xpath(".//div[@id='productTrackingParams']/@data-ean").extract()[0])
        url = response.xpath(".//a[@class='show-for-medium bold-text']/@href").extract()
        if url is not None and len(url) > 0:
            yield response.follow(url[0], callback=self.parseHandler2, meta={"ean": ean, "gold_shop": gold_shop})

    def parseHandler2(self, response):
        infos = self.getAllPirce(response)      # 获取所有的价格并以此形式返回{shop_name:[price, rating, fullfilled], ...}
        self.solutionNoon(response.meta["ean"], infos, response.meta["gold_shop"])

    def getAllPirce(self, response):
        infos = {}
        rows = response.xpath(".//div[@id='condition-all']/div[@class='row']")
        for row in rows:
            price = row.xpath(".//div[@class='field price-field']//text()").extract()[0]
            price = round(float(price.strip().split('\n')[-1].split("SAR")[0]), 2)
            shop_name = row.xpath(".//div[@class='field seller-name']//a//text()").extract()[0].lower()
            ret = row.xpath(".//div[@class='field clearfix labels']//div[@class='fullfilled']")
            fullfilled = False
            rating = 100
            if ret:
                fullfilled = True
            else:
                rating = row.xpath(".//div[@class='field seller-rating']//a//text()").extract()
                if rating:
                    rating = round(float(rating[0].split('%')[0].split("(")[-1]), 2)
                else:
                    rating = 0  # no rating yet
            infos[shop_name] = [price, rating, fullfilled]
        return infos

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
                            self.database.needToChangePrice(ean, price, gold_shop, variant_name, 1)
                            out = "情况C " + out + "\t差价比[" + str(round(diff1 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
                else:
                    price = round(infos[self.shop_name][0] - attr["lowwer"], 2)
                    if price < max(infos[gold_shop][0], attr["self_least_price"]):
                        out = "情况D " + out + "\t不修改"
                    else:
                        self.database.needToChangePrice(ean, price, gold_shop, variant_name, 1)
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
                        self.database.needToChangePrice(ean, price, gold_shop, variant_name, 0)
                        out = "情况F " + out + "\t最低价[" + str(least_price) + "]\t" + "差价比[" + \
                              str(round(diff2 * 100, 2)) + "%]\t改价为[" + str(price) + "]"
        out = "前台：" + out
        print(out)


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
        settings.set('LOG_FILE', self.name + ".log")
        settings.set('ROBOTSTXT_OBEY', False)
        process = CrawlerProcess(settings)
        process.crawl(QuotesSpider, shop_name=self.name)
        process.start()
        process.join()
        print("前台抓取数据一轮完成")
        count = random.randint(10, 30)
        database = DataManager(self.name)
        attr = database.getAttr("EMPTY")
        if attr["minute"] != 0:
            count = attr["minute"] * 60
        minute = 0
        while minute <= count:
            database.handlerStatus()
            minute += 1
            time.sleep(1)
            attr = database.getAttr("EMPTY")
            count = attr["minute"] * 60


