import multiprocessing
import time
import requests
import json
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from auto_noon.DataManager import DataManager

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
        # self.debug_file.write(info)
        # self.debug_file.flush()

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        self.database = DataManager(self.name)
        printYellow("启动后台改价任务")
        while 1:
            option = webdriver.ChromeOptions()
            option.add_argument('--no-sandbox')
            option.add_argument('--disable-dev-shm-usage')
            option.add_argument("headless")
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
        printYellow("后台：登录账户1")
        # todo dylan 测试临时屏蔽
        self.database.handlerStatus()
        printYellow("后台：登录账户2")
        self.chrome.get('https://login.noon.partners/en/')
        try:
            account, password = self.database.getAccountAndPassword()
            printYellow("获取账号：" + str(account))
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
        compare = ""
        shop_type = self.database.getShopType()
        if shop_type == "ksa":
            compare = "https://core.noon.partners/en-sa/"
        elif shop_type == "uae":
            compare = "https://core.noon.partners/en-ae/"
        print("账号类型：" + shop_type)
        while self.chrome.current_url != compare:
            time.sleep(1)
            i = i + 1
            if i > 150:
                raise TimeoutError
        while 1:
            try:
                # todo dylan 测试预约fbn功能，临时屏蔽原有改价函数
                self.NewInventory()
                # self.ScheduleFBN()
            except:
                # self.exceptHandler(traceback.format_exc())
                raise

    def NewInventory(self):
        # if not self.database.shopLock():
        #     printYellow("后台：已经超出店铺数量限制")
        #     self.database.setStopStatus()
        #     while True:
        #         time.sleep(6000)
        printYellow("后台：打开改价页面")
        self.loginHandler = self.chrome.current_window_handle
        handlers = self.chrome.window_handles
        self.unknownHandler = ""
        for handler in handlers:
            if handler != self.loginHandler:
                self.unknownHandler = handler
                break
        js = ""
        shop_type = self.database.getShopType()
        if shop_type == "ksa":
            js = 'window.open("https://catalog.noon.partners/en-sa/catalog")'
        elif shop_type == "uae":
            js = 'window.open("https://catalog.noon.partners/en-ae/catalog")'
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
                # self.exceptHandler(traceback.format_exc())
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
        error_count = 0
        printYellow("后台：开始改价")
        while True:
            self.database.handlerStatus()
            # time.sleep(1)
            ean, price, variant_name = self.database.getFirstNeedChangeItem()
            if ean == "ean" and price == "price":
                time.sleep(1)
                continue
            out = time.strftime("%Y-%m-%d %H:%M:%S") + " " + ean + "[" + variant_name + "]\t" + str(round(price, 2))
            self.chrome.switch_to.window(self.inventoryHandler)
            catelog_url_elems = []
            try:
                search_xpath = '//input[@type="search"]'
                WebDriverWait(self.chrome, 100, 0.5).until(EC.presence_of_element_located((By.XPATH, search_xpath)))
                elemSearch = self.chrome.find_element_by_xpath(search_xpath)
                elemSearch.clear()
                elemSearch.send_keys(ean[0:-1])
                elemSearch.send_keys(Keys.ENTER)
                limit = 2
                while limit:
                    time.sleep(1)
                    # 判断是否还在搜索中
                    please_wait_elems = self.chrome.find_elements_by_xpath("//div[contains(text(), 'Please wait')]")
                    if len(please_wait_elems) == 1:
                        continue

                    # 判断是否搜索出结果
                    no_data_elems = self.chrome.find_elements_by_xpath("//div[contains(text(), 'No Summary data')]")
                    if no_data_elems:
                        break

                    # 获取搜索结果的第一个产品的ean 判断是否和搜索内容一致
                    tr_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]")
                    if len(tr_elems) != 0:
                        # headless 模式下 显示ean的td元素被隐藏，需要点击第一个td去展开
                        arrow_ctr_elem = tr_elems[0].find_elements_by_xpath(".//td[contains(@class, 'tableArrowCtr')]")
                        if len(arrow_ctr_elem) == 1:
                            arrow_ctr_elem[0].click()
                            catalog_xpath = "//td[contains(text(), 'Catalog SKU')]/../td[2]"
                            catalog_td_elems = []
                            try:
                                WebDriverWait(self.chrome, 1, 0.1).until(EC.presence_of_element_located((By.XPATH, catalog_xpath)))
                                catalog_td_elems = arrow_ctr_elem[0].find_elements_by_xpath(catalog_xpath)
                            except:
                                pass
                            if len(catalog_td_elems) == 1 and len(catalog_td_elems[0].text) > 1 and str(catalog_td_elems[0].text)[0:-1] == ean[0:-1]:
                                catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[3]//a")
                                break
                            else:
                                limit -= 1
                        else:
                            td_elems = tr_elems[0].find_elements_by_xpath(".//td")
                            for td_elem in td_elems:
                                if len(td_elem.text) >= 1 and str(td_elem.text)[0:-1] == ean[0:-1]:
                                    catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[2]//a")
                                    break
                                else:
                                    limit -= 1
                    else:
                        limit -= 1
            except FileExistsError:
                a = 1
            except:
                error_count += 1
                if error_count > 3:
                    raise
                else:
                    continue
            if len(catelog_url_elems) != 1:
                # printRed("后台：" + out + "\t没找到这个产品")
                self.database.finishOneChangeItem(ean, price, variant_name)
                continue

            self.chrome.execute_script("arguments[0].click()", catelog_url_elems[0])

            change_count, flag = self.database.isLowerThanMaxTimes(ean, variant_name)
            if flag:
                try:
                    sale_price_xpath = "//input[@name='sale_price']"
                    WebDriverWait(self.chrome, 80, 0.5).until(EC.presence_of_element_located((By.XPATH, sale_price_xpath)))
                    elemInput = self.chrome.find_element_by_xpath(sale_price_xpath)
                    value = elemInput.get_attribute("value")
                    if value is None or value == "value" or len(value) == 0:
                        price_xpath = "//input[@name='price']"
                        elemInput = self.chrome.find_element_by_xpath(price_xpath)
                    old_price = round(float(elemInput.get_attribute("value")), 2)
                    elemInput.clear()
                    elemInput.send_keys(Keys.CONTROL, "a")
                    elemInput.send_keys(Keys.DELETE)
                    elemInput.send_keys(str(price))
                    save_button_xpath = "//div[contains(text(), 'Submit')]" # Save Changes
                    WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.XPATH, save_button_xpath)))
                    elemBtn = self.chrome.find_element_by_xpath(save_button_xpath)
                    time_change = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.chrome.execute_script("arguments[0].click()", elemBtn)
                    time.sleep(0.5)
                    self.database.addAChange(ean, variant_name, old_price, price)
                    self.database.addChangeRecord(ean, variant_name, time_change, price)
                    out += "[" + str(change_count + 1) + "次]"
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

    def ScheduleFBN(self):
        printYellow("后台：打开预约界面")
        self.loginHandler = self.chrome.current_window_handle
        handlers = self.chrome.window_handles
        self.unknownHandler = ""
        for handler in handlers:
            if handler != self.loginHandler:
                self.unknownHandler = handler
                break
        js = ""
        shop_type = self.database.getShopType()
        if shop_type == "ksa":
            js = 'window.open("https://warehouse.noon.partners/en-sa/transfers?status=1&type=2&zone=all")'
        elif shop_type == "uae":
            js = 'window.open("https://warehouse.noon.partners/en-ae/transfers?status=1&type=2&zone=all")'
        self.chrome.execute_script(js)
        handlers = self.chrome.window_handles
        for handler in handlers:
            if handler != self.loginHandler and handler != self.unknownHandler:
                self.inventoryHandler = handler
                break
        while 1:
            try:
                self.ChooseOpenItem()
            except:
                self.exceptHandler(traceback.format_exc())
                self.chrome.refresh()
                continue

    def ChooseOpenItem(self):
        print("后台：打开预约界面成功")
        WebDriverWait(self.chrome, 120, 0.5).until(EC.presence_of_element_located((By.XPATH, ".//div[@class='jsx-2800349317 ctr']")))
        print("后台：选择Open项目")
        items = self.chrome.find_elements_by_xpath(".//table/tbody/tr")
        print("items size:" + str(len(items)))
        for item in items:
            status_div = item.find_element_by_xpath("./td[@data-label='Status']/div")
            if open in status_div.get_attribute("div"):
                asn_button = item.find_element_by_xpath("./td[@data-label='Shipment Number']/button")
                self.chrome.execute_script("arguments[0].click()", asn_button)
                while True:
                    time.sleep(1)

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



# timeout 357 367 385 137 270
