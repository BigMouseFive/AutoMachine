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
    name = "noon_car"

    def __init__(self, shop_name=None, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.database = DataManager(shop_name)
        self.shop_name = shop_name.lower()
        self.start_urls = self.database.getScrapyUrl()
        self.page_index = 1
        # out = "抓取数据：" + self.start_urls[0]
        # print(out)

    def parse(self, response):
        for asin in response.xpath(".//div[@class='sg-col-20-of-24 s-result-item "
                                   "sg-col-0-of-12 sg-col-28-of-32 sg-col-16-of-20 "
                                   "sg-col sg-col-32-of-36 sg-col-12-of-16 sg-col-24-of-28']/@data-asin").extract():
            self.database.handlerStatus()
            time.sleep(random.randint(0, 1))
            url = "https://www.amazon.ae/dp/" + asin
            if url is not None:
                url = url.split('?')[0]
                yield response.follow(url, callback=self.parseHandler1, meta={"asin": asin})

        # 获取下一页的url, （DEL::如果没有就从头开始）
        next = response.xpath(".//li[@class='a-last']/a/@href").extract()
        if next and len(next) > 0 and len(next[0]) > 0:
            self.page_index = self.page_index + 1
            next_page = "https://www.amazon.ae/" + next[0]
            yield response.follow(next_page, callback=self.parse)

    def parseHandler1(self, response):
        try:
            gold_shop = response.xpath(".//a[@id='sellerProfileTriggerId']//text()").extract()[0].lower()
        except IndexError:
            return
        asin = response.meta["asin"]
        url = "https://www.amazon.ae/gp/offer-listing/" + asin
        yield response.follow(url, callback=self.parseHandler2, meta={"asin": asin, "gold_shop": gold_shop, "infos": {}})

    def parseHandler2(self, response):   # 包含了getAllPrice
        rows = response.xpath(".//div[@class='a-row a-spacing-mini olpOffer']")
        for row in rows:
            price = row.xpath(".//span[@class='a-size-large a-color-price olpOfferPrice a-text-bold']//text()").extract()[0]
            price = round(float(price.split("AED")[-1].strip()), 2)
            is_fba = False
            price_ship = 0
            ret = row.xpath(".//span[@class='supersaver']")
            if ret and len(ret) > 0:
                is_fba = True
            ret = row.xpath(".//p[@class='olpShippingInfo']//span[@class='olpShippingPrice']//text()")
            if ret and len(ret) > 0:
                price_ship = ret.extract()[0]
                price_ship = round(float(price_ship.split("AED")[-1].strip()), 2)
            shop_name = row.xpath(".//h3[@class='a-spacing-none olpSellerName']//a/text()").extract()[0]
            shop_name = shop_name.lower()
            rating = row.xpath(".//p[@class='a-spacing-small']//a/b/text()")
            if rating and len(rating) > 0:
                rating = int(rating.extract()[0].split("%")[0].strip())
            else:
                rating = 0
            response.meta["infos"][shop_name] = [round(price + price_ship, 2), rating, is_fba]

        next = response.xpath(".//li[@class='a-last']/a/@href").extract()
        if next and len(next) > 0 and len(next[0]) > 0:
            next_page = "https://www.amazon.ae/" + next[0]
            yield response.follow(next_page, callback=self.parseHandler2, meta={"infos": response.meta["infos"],
                                                                              "asin": response.meta["asin"],
                                                                              "gold_shop": response.meta["gold_shop"]})
        else:
            self.solutionNoon(response.meta["asin"], response.meta["infos"], response.meta["gold_shop"])

    def solutionNoon(self, asin, infos, gold_shop, variant_name=""):
        # is_fbn = 1 if infos[gold_shop][2] else 0
        # least = 9999
        # least_fbn = 9999
        # shop_l = "#####"
        # shop_lf = "#####"
        # for v in infos:
        #     if least > infos[v][0]:
        #         shop_l = v
        #         least = infos[v][0]
        #     if infos[v][2]:
        #         if least_fbn > infos[v][0]:
        #             shop_lf = v
        #             least_fbn = infos[v][0]
        #
        # is_least = 1 if shop_l == gold_shop else 0
        # self.database.addTest(asin, gold_shop, infos[gold_shop][0], is_fbn, is_least, shop_l, least, shop_lf, least_fbn)
        #
        # if infos[gold_shop][2]:
        #     print("==================" + asin + ":" + gold_shop + "==================")
        #
        # for v in infos:
        #     print(v + ":" + str(infos[v][0]) + "," + str(infos[v][1]) + "," + str(infos[v][2]))

        for v in infos:
            if infos[v][2]:
                infos[v][0] = round(infos[v][0] + 10, 2)

        if not self.database.isInWhiteList(asin, variant_name):
            out = "前台：不在白名单 " + time.strftime("%Y-%m-%d %H:%M:%S") + "   " + asin + "[" + variant_name + "]\t本店铺[" + str(
                infos[self.shop_name][0]) + "]\t" + \
                  "购物车[" + str(infos[gold_shop][0]) + "][" + gold_shop + "]"
            print(out)
            return
        attr = self.database.getAttr(asin)
        out = time.strftime("%Y-%m-%d %H:%M:%S") + "   " + asin + "[" + variant_name + "]\t本店铺[" + \
              str(infos[self.shop_name][0]) + "]\t" + "购物车[" + str(infos[gold_shop][0]) + "][" + gold_shop + "]"
        self.database.spiderRecord(asin, infos[gold_shop][0], gold_shop, variant_name)
        if gold_shop in attr["my_shop"]:  # 黄金购物车是自家店铺
            out = "情况A " + out + "\t不修改"
        else:
            is_fbn = 1 if infos[self.shop_name][2] else 0
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
                    self.database.needToChangePrice(asin, price, gold_shop, variant_name, is_fbn)
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
        while count:
            database.handlerStatus()
            count -= 1
            time.sleep(1)
            attr = database.getAttr("EMPTY")
            count = attr["minute"] * 60
