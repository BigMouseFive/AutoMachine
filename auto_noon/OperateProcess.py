import io
import os
import threading
import time
import zipfile
import requests
import json
import traceback
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from auto_noon.DataManager import DataManager
from logger import logger
CHROME_DRIVER_PATH = "../chromedriver.exe"
CHROME_DRIVER_URL = "https://registry.npmmirror.com/-/binary/chromedriver/"


class OperateProcess(object):
    def __init__(self, name):
        self.name = name
        self.headless = True
        if os.path.exists("open_chrome"):
            self.headless = False
        self.record = {}  # {"ean":[price, count]}
        self.monitor_num = 0
        self.monitoring = False
        self.mutex = threading.Lock()

    def reset_monitor(self, flag=True, num=120):
        self.mutex.acquire()
        self.monitor_num = num
        self.monitoring = flag
        self.mutex.release()

    # 监控chromedirver是否出现了长时间未返回的问题(socket层面）
    def monitor_loop(self):
        while True:
            self.mutex.acquire()
            try:
                if self.monitoring:
                    if self.monitor_num > 0:
                        self.monitor_num -= 1
                    else:
                        self.chrome.quit()
                        self.monitoring = False
            except:
                logger.warning(traceback.format_exc())
            self.mutex.release()
            time.sleep(1)

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        self.database = DataManager(self.name)
        logger.info("后台,启动后台改价任务")
        threading.Thread(target=self.monitor_loop).start()
        while 1:
            option = webdriver.ChromeOptions()
            option.add_argument('--no-sandbox')
            option.add_argument('--disable-dev-shm-usage')
            if self.headless:
                option.add_argument("headless")
            option.add_argument("--window-size=1920,1050")
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
            try:
                self.chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=option)
            except SessionNotCreatedException:
                logger.info("后台,ChromeDriver版本不匹配，将尝试获取匹配版本")
                version = \
                traceback.format_exc().split("Current browser version is")[-1].split("with binary path")[0].split(".")[
                    0].strip()
                self.getChromeDriver(version)
                continue
            # self.chrome.maximize_window()
            try:
                self.LoginAccount()
                self.NewInventory()
                self.OperateProductSelenium()
            except:
                logger.info("后台," + traceback.format_exc())
                logger.info("后台,重启......")
                self.reset_monitor(False)
                self.chrome.quit()
                self.database.handlerStatus()
                continue

    # 获取对应版本的chromedriver
    def getChromeDriver(self, version):
        logger.info("后台,获取ChromeDriver[" + str(version) + "]")
        ret = requests.get(CHROME_DRIVER_URL)
        for item in ret.json():
            if version in item["name"]:
                logger.info("后台,找到匹配版本[" + str(item["name"]) + "]")
                ret = requests.get(CHROME_DRIVER_URL + item["name"] + "chromedriver_win32.zip")
                zip_data = zipfile.ZipFile(io.BytesIO(ret.content))
                for file in zip_data.filelist:
                    if file.filename == "chromedriver.exe":
                        with open(CHROME_DRIVER_PATH, "wb") as f:
                            f.write(zip_data.read(file))
                            logger.info("后台,获取ChromeDriver成功，将重启后台")
                        return

    def LoginAccount(self):
        logger.info("后台,登录账户1")
        self.database.handlerStatus()
        logger.info("后台,登录账户2")
        self.reset_monitor()
        self.chrome.get('https://login.noon.partners/en/')
        try:
            account, password = self.database.getAccountAndPassword()
            logger.info("后台,获取账号：" + str(account))
            xpath = ".//div[@class='jsx-1240009043 group']"
            self.reset_monitor()
            WebDriverWait(self.chrome, 30, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.reset_monitor()
            elemLogin = self.chrome.find_elements_by_xpath(".//div[@class='jsx-1240009043 group']/input")
            self.reset_monitor()
            elemNewLoginBtn = self.chrome.find_element_by_xpath(
                ".//button[@class='jsx-1789715842 base ripple primary uppercase fullWidth']")
            self.reset_monitor()
            elemLogin[0].clear()
            self.reset_monitor()
            elemLogin[1].clear()
            self.reset_monitor()
            elemLogin[0].send_keys(account)
            self.reset_monitor()
            elemLogin[1].send_keys(password)
            self.reset_monitor()
            elemNewLoginBtn.click()
        except:
            self.reset_monitor(False)
            logger.info("后台,方式1登录失败，尝试方式2")
        self.reset_monitor(False)
        i = 0
        compare = ""
        shop_type = self.database.getShopType()
        if shop_type == "ksa":
            compare = "https://core.noon.partners/en-sa/"
        elif shop_type == "uae":
            compare = "https://core.noon.partners/en-ae/"
        compare = "https://core.noon.partners/en-"
        logger.info("后台,账号类型：" + shop_type)
        while compare not in self.chrome.current_url:
            time.sleep(1)
            i = i + 1
            if i > 150:
                logger.info("后台,登录超时，请检查账号密码时候有误")
                raise TimeoutError

    def NewInventory(self):
        logger.info("后台,打开改价页面")
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
        self.reset_monitor()
        self.chrome.execute_script(js)
        handlers = self.chrome.window_handles
        for handler in handlers:
            if handler != self.loginHandler and handler != self.unknownHandler:
                self.inventoryHandler = handler
                break

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

    def OperateProductSelenium(self):
        error_count = 0
        logger.info("后台,开始改价")
        while True:
            self.reset_monitor(False)
            self.database.handlerStatus()
            # time.sleep(1)
            ean, price, variant_name = self.database.getFirstNeedChangeItem()
            if ean == "ean" and price == "price":
                time.sleep(1)
                continue
            out = ean + "[" + variant_name + "]\t" + str(round(price, 2))
            self.reset_monitor()
            self.chrome.switch_to.window(self.inventoryHandler)
            catelog_url_elems = []
            try:
                search_xpath = '//input[@type="search"]'
                self.reset_monitor()
                WebDriverWait(self.chrome, 100, 0.5).until(EC.presence_of_element_located((By.XPATH, search_xpath)))
                self.reset_monitor()
                elemSearch = self.chrome.find_element_by_xpath(search_xpath)
                self.reset_monitor()
                elemSearch.clear()
                self.reset_monitor()
                elemSearch.send_keys(ean[0:-1])
                self.reset_monitor()
                elemSearch.send_keys(Keys.ENTER)
                limit = 4
                while limit:
                    time.sleep(1)
                    # 判断是否还在搜索中
                    self.reset_monitor()
                    please_wait_elems = self.chrome.find_elements_by_xpath("//div[contains(text(), 'Please wait')]")
                    if len(please_wait_elems) == 1:
                        limit -= 1
                        continue

                    # 判断是否搜索出结果
                    self.reset_monitor()
                    no_data_elems = self.chrome.find_elements_by_xpath("//div[contains(text(), 'No Summary data')]")
                    if no_data_elems:
                        break

                    # 获取搜索结果的第一个产品的ean 判断是否和搜索内容一致
                    self.reset_monitor()
                    tr_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]")
                    if len(tr_elems) != 0:
                        self.reset_monitor()
                        td_elems = tr_elems[0].find_elements_by_xpath(".//td")
                        has_find = False
                        for td_elem in td_elems:
                            if len(td_elem.text) >= 1 and str(td_elem.text)[0:-1] == ean[0:-1]:
                                self.reset_monitor()
                                catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[2]//a")
                                if len(catelog_url_elems) == 0:
                                    self.reset_monitor()
                                    catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[3]//a")
                                if len(catelog_url_elems) == 0:
                                    self.reset_monitor()
                                    catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[1]//a")
                                if len(catelog_url_elems) == 0:
                                    self.reset_monitor()
                                    catelog_url_elems = self.chrome.find_elements_by_xpath("//table/tbody/tr[1]/td[4]//a")
                                has_find = True
                                break
                        if has_find:
                            limit = 0
                        else:
                            limit -= 1
                    else:
                        limit -= 1
            except:
                self.reset_monitor(False)
                logger.info("后台," + traceback.format_exc())
                error_count += 1
                if error_count > 3:
                    raise
                else:
                    continue
            if len(catelog_url_elems) != 1:
                self.database.finishOneChangeItem(ean, price, variant_name)
                continue

            change_count, flag = self.database.isLowerThanMaxTimes(ean, variant_name)
            if flag:
                self.reset_monitor()
                self.chrome.execute_script("arguments[0].click()", catelog_url_elems[0])
                try:
                    sale_price_xpath = "//input[@name='salePrice']"
                    self.reset_monitor()
                    WebDriverWait(self.chrome, 80, 0.5).until(EC.presence_of_element_located((By.XPATH, sale_price_xpath)))
                    self.reset_monitor()
                    elemInput = self.chrome.find_element_by_xpath(sale_price_xpath)
                    self.reset_monitor()
                    value = elemInput.get_attribute("value")
                    if value is None or value == "value" or len(value) == 0:
                        price_xpath = "//input[@name='price']"
                        self.reset_monitor()
                        elemInput = self.chrome.find_element_by_xpath(price_xpath)
                    self.reset_monitor()
                    old_price = round(float(elemInput.get_attribute("value")), 2)
                    self.reset_monitor()
                    elemInput.clear()
                    self.reset_monitor()
                    elemInput.send_keys(Keys.CONTROL, "a")
                    self.reset_monitor()
                    elemInput.send_keys(Keys.DELETE)
                    self.reset_monitor()
                    elemInput.send_keys(str(price))

                    # save_button_xpath = "//div[contains(text(), 'Save Changes')]"  # Submit
                    # WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.XPATH, save_button_xpath)))
                    # elemBtn = self.chrome.find_element_by_xpath(save_button_xpath)
                    # self.chrome.execute_script("arguments[0].click()", elemBtn)
                    # time.sleep(0.5)

                    # 点击按钮 Save Changes
                    save_changes_xpath = "//div[contains(text(), 'Save Changes')]"
                    self.reset_monitor()
                    WebDriverWait(self.chrome, 20, 0.5).until(
                        EC.presence_of_element_located((By.XPATH, save_changes_xpath)))
                    self.reset_monitor()
                    elemBtn = self.chrome.find_elements_by_xpath(save_changes_xpath)[-1]
                    self.reset_monitor()
                    self.chrome.execute_script("arguments[0].click()", elemBtn)
                    time.sleep(0.5)

                    # 点击按钮submit
                    submit_button_xpath = "//div[contains(text(), 'Submit')]"
                    self.reset_monitor()
                    WebDriverWait(self.chrome, 20, 0.5).until(
                        EC.presence_of_element_located((By.XPATH, submit_button_xpath)))
                    self.reset_monitor()
                    elemBtn = self.chrome.find_elements_by_xpath(submit_button_xpath)[0]
                    self.reset_monitor()
                    self.chrome.execute_script("arguments[0].click()", elemBtn)
                    time.sleep(0.5)

                    time_change = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.database.addAChange(ean, variant_name, old_price, price)
                    self.database.addChangeRecord(ean, variant_name, time_change, price)
                    out += "[" + str(change_count + 1) + "次]"
                    logger.info("后台," + out + "\t改价成功")
                except:
                    self.reset_monitor(False)
                    out += "[" + str(change_count) + "次]"
                    error_count += 1
                    if error_count > 3:
                        raise
                    else:
                        logger.info(traceback.format_exc())
                        logger.info("后台," + out + "\t改价失败")
            else:
                out += "[" + str(change_count) + "次]"
                logger.info("后台," + out + "\t达到最大改价次数")

            self.database.finishOneChangeItem(ean, price, variant_name)
            if flag:
                self.reset_monitor()
                self.chrome.back()
                self.reset_monitor()
                self.chrome.back()

    def ScheduleFBN(self):
        logger.info("后台,打开预约界面")
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
                logger.info(traceback.format_exc())
                self.chrome.refresh()
                continue

    def ChooseOpenItem(self):
        logger.info("后台,打开预约界面成功")
        WebDriverWait(self.chrome, 120, 0.5).until(EC.presence_of_element_located((By.XPATH, ".//div[@class='jsx-2800349317 ctr']")))
        logger.info("后台,选择Open项目")
        items = self.chrome.find_elements_by_xpath(".//table/tbody/tr")
        logger.info("后台,items size:" + str(len(items)))
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
                                "true;} catch (ex) {return false;}"
        return driver.execute_script(checkPageFinishScript)


# timeout 357 367 385 137 270
