import multiprocessing
import time
import requests
import json
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from DataManager import DataManager
CHROME_DRIVER_PATH = "../chromedriver.exe"


def printYellow(mess):
    # print(Fore.YELLOW + mess)
    print(mess)


def printRed(mess):
    # print(Fore.RED + mess)
    print(mess)


class OperateProcess(multiprocessing.Process):
    def __init__(self, name):
        multiprocessing.Process.__init__(self)  # 重构了Process类里面的构造函数
        self.name = name
        self.record = {}  # {"ean":[price, count]}

    def exceptHandler(self, info):
        info = time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + info
        print(info)
        self.debug_file.write(info)
        self.debug_file.flush()

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        self.debug_file = open(self.name + ".debuginfo", "a")
        self.database = DataManager(self.name)
        printYellow("启动后台改价任务")
        while 1:
            option = webdriver.ChromeOptions()
            option.add_argument('--no-sandbox')
            option.add_argument('--disable-dev-shm-usage')
            # option.add_argument("headless")
            option.add_argument('ignore-certificate-errors')
            option.add_argument('log-level=3')
            option.add_argument('lang=zh_CN.UTF-8')
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'stylesheet': 2,
                }
            }
            option.add_experimental_option('prefs', prefs)
            self.chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=option)
            self.chrome.maximize_window()
            try:
                self.LoginAccount()
            except:
                self.exceptHandler(traceback.format_exc())
                self.chrome.quit()
                self.database.handlerStatus()
                continue

    def LoginAccount(self):
        self.database.handlerStatus()
        printYellow("后台：登录账户")
        self.chrome.get('https://login.noon.partners/en/')
        try:
            account, password = self.database.getAccountAndPassword()
            xpath = ".//div[@class='jsx-1240009043 group']"
            WebDriverWait(self.chrome, 30, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            elemLogin = self.chrome.find_elements_by_xpath(".//div[@class='jsx-1240009043 group']/input")
            elemNewLoginBtn = self.chrome.find_element_by_xpath(
                ".//button[@class='jsx-1789715842 base ripple primary uppercase fullWidth']")
            elemLogin[0].clear()
            elemLogin[1].clear()
            elemLogin[0].send_keys(account)
            elemLogin[1].send_keys(password)
            elemNewLoginBtn.click()
        except:
            printYellow("后台：方式1登录失败，尝试方式2")
        i = 0
        while self.chrome.current_url != "https://core.noon.partners/en-sa/":
            time.sleep(1)
            i = i + 1
            if i > 150:
                raise TimeoutError
        while 1:
            try:
                self.NewInventory()
            except:
                # self.exceptHandler(traceback.format_exc())
                raise

    def NewInventory(self):
        if not self.database.shopLock():
            printYellow("后台：已经超出店铺数量限制")
            self.database.setStopStatus()
            while True:
                time.sleep(6000)
        printYellow("后台：打开改价页面")
        self.loginHandler = self.chrome.current_window_handle
        handlers = self.chrome.window_handles
        self.unknownHandler = ""
        for handler in handlers:
            if handler != self.loginHandler:
                self.unknownHandler = handler
                break
        js = 'window.open("https://catalog.noon.partners/en-sa/catalog")'
        self.chrome.execute_script(js)
        handlers = self.chrome.window_handles
        for handler in handlers:
            if handler != self.loginHandler and handler != self.unknownHandler:
                self.inventoryHandler = handler
                break
        while 1:
            try:
                self.OperateProductSelenium()
            except:
                self.exceptHandler(traceback.format_exc())
                self.chrome.refresh()
                continue

    def prepareJSON(self, ret_json, partner_sku, price):
        global is_active, json_sale_end, json_sale_start
        json_price = ""
        json_sale_price = ""
        for part in ret_json["psku"]["available_psku"]:
            if part["psku_canonical"] == partner_sku:
                is_active = part["is_active"]
                json_price = str(round(price, 2))
                if "sale_price_sa" not in part and part["sale_price_sa"] is not None:
                    json_sale_price = str(round(price, 2))
                    json_price = str(part["price_sa"])
                    json_sale_end = part["sale_end_sa"]
                    json_sale_start = part["sale_start_sa"]
        json_stock = []
        for stock in ret_json["psku"]["stock"][0]["stock_group"]:
            json_stock.append({
                "id_warehouse": stock["id_warehouse"],
                "quantity": "0",
                "stock_gross": stock["stock_gross"],
                "stock_transferred": stock["stock_transferred"],
                "stock_reserved": stock["stock_reserved"],
                "stock_net": stock["stock_net"],
                "processing_time": str(stock["processing_time"]),
                "stock_updated": False,
                "country_code": stock["country_code"],
                "max_processing_time": stock["max_processing_time"]
            })
        ret_json = {
            "pskus": [{
                "id_warranty": "0",
                "partner_sku": ret_json["psku"]["partner_sku"],
                "sku": ret_json["psku"]["sku"],
                "psku_canonical": ret_json["psku"]["psku_canonical"],
                "is_active": is_active,
                "stocks": json_stock,
                "price": json_price
            }]
        }
        if len(json_sale_price) > 0:
            ret_json["pskus"][0]["sale_price"] = json_sale_price
            ret_json["pskus"][0]["sale_end"] = json_sale_end
            ret_json["pskus"][0]["sale_start"] = json_sale_start

        return json.dumps(ret_json)

    def OperateProductRequests(self):
        printYellow("后台：开始改价")
        selenium_cookies = self.chrome.get_cookies()
        selenium_headers = self.chrome.execute_script("return navigator.userAgent")
        selenium_headers = {
            'User-Agent': selenium_headers,
            "origin": "https://catalog.noon.partners",
            "Content-Type": "application/json",
            "x-locale": "en-sa"
        }
        s = requests.session()
        s.headers.update(selenium_headers)
        for cookie in selenium_cookies:
            short_cookie = {cookie["name"]: cookie["value"]}
            requests.utils.add_dict_to_cookiejar(s.cookies, short_cookie)
        s.verify = "./noon.cer"
        while True:
            time.sleep(1)
            ean, price, variant_name = self.database.getFirstNeedChangeItem()
            if ean == "ean":
                continue
            out = "后台：" + time.strftime("%Y-%m-%d %H:%M:%S") + " " + ean + " " + str(round(price, 2))
            url = "https://catalog.noon.partners/_svc/clapi-v1/catalog/items?limits=20&page=1&search=" + ean
            r = s.get(url)
            if r.status_code == 200:
                ret_json = json.loads(r.text)
                if ret_json is not None and "items" in ret_json:
                    if len(ret_json["items"]) == 1 and "partner_sku" in ret_json["items"][0]:
                        partner_sku = ret_json["items"][0]["partner_sku"]
                        partner_sku = partner_sku.replace('.', '').replace('-', '')
                        if len(partner_sku) > 0:
                            url = "https://catalog.noon.partners/_svc/clapi-v1/catalog/item/details?psku_canonical=" + partner_sku
                            r = s.get(url)
                            if r.status_code == 200:
                                ret_json = json.loads(r.text)
                                try:
                                    ret_json = self.prepareJSON(ret_json, partner_sku, price)
                                    url = "https://catalog.noon.partners/_svc/clapi-v1/psku"
                                    r = s.post(url, data=ret_json, headers={
                                        "Referer": "https://catalog.noon.partners/en-sa/catalog/" + partner_sku})
                                    if r.status_code == 200:
                                        printYellow(out + "\t改价成功")
                                    else:
                                        printRed(out + "\t改价失败\t[6]")
                                except:
                                    printRed(out + "\t改价失败\t[5]")
                                    raise
                            else:
                                printRed(out + "\t改价失败\t[4]")
                        else:
                            printRed(out + "\t改价失败\t[3]")
                    else:
                        printRed(out + "\t改价失败\t[2]")
                else:
                    printRed(out + "\t改价失败\t[1]")
            else:
                printRed(out + "\t改价失败\t[0]")

            self.database.finishOneChangeItem(ean, price, variant_name)

    def OperateProductSelenium(self):
        global product_url, elemProduct, debug_out
        printYellow("后台：开始改价")
        url_bak = ""
        while True:
            self.database.handlerStatus()
            time.sleep(1)
            ean, price, variant_name = self.database.getFirstNeedChangeItem()
            if ean == "ean" and price == "price":
                continue
            out = time.strftime("%Y-%m-%d %H:%M:%S") + " " + ean + "[" + variant_name + "]\t" + str(round(price, 2))
            self.chrome.switch_to.window(self.inventoryHandler)
            try:
                xpath = './/div[@class="jsx-3807287210 searchWrapper"]'
                WebDriverWait(self.chrome, 120, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                elemSearch = self.chrome.find_element_by_xpath('.//div[@class="jsx-3807287210 searchWrapper"]//input')
                elemSearch.clear()
                elemSearch.send_keys(ean)
                debug_out = ""
                while 1:
                    time.sleep(1.5)
                    e1 = self.chrome.find_elements_by_xpath(
                        ".//div[@class='jsx-448933760 ctr']/table/tbody/tr[1]/td[1]//span")
                    e2 = self.chrome.find_elements_by_xpath(
                        ".//table[@class='jsx-3498568516 table']//td[@class='jsx-3498568516 td']"
                        "//div[@class='jsx-3793681198 text']")
                    if not (len(e1) == 1 or len(e2) == 1):
                        continue
                    debug_out += "1"
                    elemProducts = self.chrome.find_elements_by_xpath(
                        ".//div[@class='jsx-448933760 ctr']/table/tbody/tr")
                    if len(elemProducts) >= 1:
                        debug_out += "2"
                        elemProduct = self.chrome.find_elements_by_xpath(
                            ".//table[@class='jsx-3498568516 table']//td[@class='jsx-3498568516 td']"
                            "//div[@class='jsx-3793681198 text']")
                        if len(elemProduct) == 1:
                            debug_out += "3"
                            product_url = ""
                            url_bak = ""
                            break
                        if len(elemProducts) == 1:
                            debug_out += "4"
                            elemProduct = self.chrome.find_elements_by_xpath(
                                ".//div[@class='jsx-448933760 ctr']/table/tbody/tr[1]/td[1]//span")
                            product_url = str(elemProduct[0].text)
                            if product_url != url_bak:
                                debug_out += "5"
                                url_bak = product_url
                                break
                        else:
                            debug_out += "6"
                            e1 = self.chrome.find_elements_by_xpath(
                                ".//div[@class='jsx-448933760 ctr']/table/tbody/tr[1]/td[1]//span")
                            if not len(e1) == 1:
                                debug_out += "$"
                                continue
                            if variant_name == "":
                                debug_out += "7"
                                product_url = ""
                                url_bak = ""
                                break
                            for elemProduct in elemProducts:
                                debug_out += "8"
                                key = elemProduct.find_elements_by_xpath(".//div[text()='Variant']")
                                if len(key) == 1:
                                    value = key[0].find_elements_by_xpath("./following-sibling::div[1]")
                                    debug_out += "9" + value[0].text
                                    if len(value[0].text) > 0 and len(value) == 1 and value[0].text[0] == variant_name[                                        0] and value[0].text in variant_name:
                                        elemProduct = elemProduct.find_elements_by_xpath("./td[1]//span")
                                        debug_out += "0"
                                        if len(elemProduct) == 1:
                                            debug_out += "|"
                                            product_url = str(elemProduct[0].text)
                                            if product_url != url_bak:
                                                debug_out += "!"
                                                url_bak = product_url
                                                raise FileExistsError
                            debug_out += "#"
                            product_url = ""
                            url_bak = ""
                            break
            except FileExistsError:
                a = 1
            except:
                raise
            if product_url == "" or len(elemProduct) != 1:
                printRed("后台：" + out + "\t没找到这个产品")
                printRed("\n\n" + debug_out + "\n\n")
                self.database.finishOneChangeItem(ean, price, variant_name)
                continue
            self.chrome.execute_script("arguments[0].click()", elemProduct[0])
            # self.chrome.switch_to.window(self.loginHandler)
            # js = 'window.location.replace("' + product_url + '")'
            # self.chrome.execute_script(js)
            change_count, flag = self.database.isLowerThanMaxTimes(ean, variant_name)
            if flag:
                try:
                    xpath = ".//div[@class='jsx-509839755 priceInputWrapper']//input[@name='sale_price_sa']"
                    WebDriverWait(self.chrome, 80, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elemInput = self.chrome.find_element_by_xpath(xpath)
                    value = elemInput.get_attribute("value")
                    if value is None or value == "value" or len(value) == 0:
                        xpath = ".//div[@class='jsx-509839755 priceInputWrapper']//input[@name='price_sa']"
                        elemInput = self.chrome.find_element_by_xpath(xpath)
                    old_price = round(float(elemInput.get_attribute("value")), 2)
                    elemInput.clear()
                    elemInput.send_keys(str(price))
                    xpath = ".//div[@class='jsx-509839755 fixedBottom']/button"
                    WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elemBtn = self.chrome.find_element_by_xpath(xpath)
                    time_change = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.chrome.execute_script("arguments[0].click()", elemBtn)
                    self.database.addAChange(ean, variant_name, old_price, price)
                    self.database.addChangeRecord(ean, variant_name, time_change, price)
                    out += "[" + str(change_count + 1) + "次]"
                    # if ean in self.record:
                    #     self.record[ean][0] = price
                    #     self.record[ean][1] += 1
                    # else:
                    #     self.record[ean] = [price, 1]
                    printYellow("后台：" + out + "\t改价成功")
                except:
                    out += "[" + str(change_count) + "次]"
                    self.exceptHandler(traceback.format_exc())
                    printRed("后台：" + out + "\t改价失败")
            else:
                out += "[" + str(change_count) + "次]"
                printRed("后台：" + out + "\t达到最大改价次数")
            self.database.finishOneChangeItem(ean, price, variant_name)
            self.chrome.back()

    def checkPage(self, driver):
        checkPageFinishScript = "try {if (document.readyState !== 'complete') {return false;} if (window.jQuery) { if (" \
                                "window.jQuery.active) { return false; } else if (window.jQuery.ajax && " \
                                "window.jQuery.ajax.active) { return false; } } if (window.angular) { if (!window.qa) { " \
                                "window.qa = {doneRendering: false }; } var injector = window.angular.element(" \
                                "'body').injector(); var $rootScope = injector.get('$rootScope'); var $http = " \
                                "injector.get('$http'); var $timeout = injector.get('$timeout'); if ($rootScope.$$phase " \
                                "=== '$apply' || $rootScope.$$phase === '$digest' || $http.pendingRequests.length !== 0) " \
                                "{ window.qa.doneRendering = false; return false; } if (!window.qa.doneRendering) { " \
                                "$timeout(function() { window.qa.doneRendering = true;}, 0); return false;}} return " \
                                "true;} catch (ex) {return false;} "
        return driver.execute_script(checkPageFinishScript)
