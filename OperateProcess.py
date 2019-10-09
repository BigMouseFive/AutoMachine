import multiprocessing
import time
import traceback
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
            chrome_dir = "../chrome_url.txt"
            f = open(chrome_dir, "r")  # 设置文件对象
            str = f.read()  # 将txt文件的所有内容读入到字符串str中
            f.close()  # 将文件关闭
            option = webdriver.ChromeOptions()
            option.add_argument("user-data-dir=" + os.path.abspath(str))
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
        self.database.handlerStatus()
        printYellow("后台：登录账户")
        account, password = self.database.getAccountAndPassword()

        self.chrome.get("https://uae.souq.com/ae-en/login.php")
        try:
            elemNewAccount = self.chrome.find_element_by_id("email")
            elemNewLoginBtn = self.chrome.find_element_by_id("siteLogin")
            elemNewAccount.send_keys(account)
            print("输入账户:" + account)
            elemNewLoginBtn.click()
            print("点击siteLogin")
            try:
                cssSelectText = "#continue"
                WebDriverWait(self.chrome, 10, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, cssSelectText)))
                print("获取到continue按钮")
                elemContinue = self.chrome.find_element_by_id("continue")
                elemContinue.click()
                print("点击continue")
                cssSelectText = "#ap_password"
                WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, cssSelectText)))
                print("获取到password输入框")
                elemPassword = self.chrome.find_element_by_id("ap_password")
                elemLoginBtn = self.chrome.find_element_by_id("signInSubmit")
                elemPassword.send_keys(Keys.CONTROL + "a")
                elemPassword.send_keys(password)
                print("输入密码：********")
                elemLoginBtn.click()
                print("点击continue")
            except:
                print("方式一登录失败，尝试方式二登录")
                cssSelectText = "#password"
                WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, cssSelectText)))
                print("获取到password输入框")
                elemPassword = self.chrome.find_element_by_id("password")
                elemLoginBtn = self.chrome.find_element_by_id("siteLogin")
                elemPassword.clear()
                elemPassword.send_keys(password)
                print("输入密码：********")
                elemLoginBtn.click()
                print("点击登录")

            cssSelectText = "#search_box"
            WebDriverWait(self.chrome, 20, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, cssSelectText)))
        except:
            if str(self.chrome.current_url).find("uae.souq.com/ae-en/account.php") < 0:
                raise
        while 1:
            try:
                ret = self.NewInventory()
                if ret == -1:
                    return -1
            except:
                raise

    def NewInventory(self):
        if not self.database.shopLock():
            printYellow("后台：已经超出店铺数量限制")
            self.database.setStopStatus()
            while True:
                time.sleep(6000)
        printYellow("后台：打开改价页面")
        self.loginHandler = self.chrome.current_window_handle
        unknownHandler = ""
        for handler in self.chrome.window_handles:
            if handler != self.loginHandler:
                unknownHandler = handler
                break
        readyUri = "https://sell.souq.com/fbs-inventory"
        js = 'window.open("' + readyUri + '")'
        self.chrome.execute_script(js)
        handlers = self.chrome.window_handles
        for handler in handlers:
            if handler != self.loginHandler and handler != unknownHandler:
                self.inventoryFbsHandler = handler
                break

        readyUri = "https://sell.souq.com/inventory/inventory-management"
        js = 'window.open("' + readyUri + '")'
        self.chrome.execute_script(js)
        handlers = self.chrome.window_handles
        for handler in handlers:
            if handler != self.loginHandler and handler != unknownHandler and handler != self.inventoryFbsHandler:
                self.inventoryHandler = handler
                break

        while 1:
            try:
                self.OperateProductSelenium()
            except:
                self.exceptHandler(traceback.format_exc())
                self.chrome.refresh()
                continue

    def OperateProductSelenium(self):
        printYellow("后台：开始改价")
        while True:
            self.database.handlerStatus()
            time.sleep(1)
            ean, price, variant_name, is_fbs = self.database.getFirstNeedChangeItem()
            if ean == "ean" and price == "price":
                continue
            out = time.strftime("%Y-%m-%d %H:%M:%S") + " " + ean + "[" + variant_name + "]\t" + str(round(price, 2))

            if is_fbs == 1:
                self.chrome.switch_to.window(self.inventoryFbsHandler)
            else:
                self.chrome.switch_to.window(self.inventoryHandler)

            change_count, flag = self.database.isLowerThanMaxTimes(ean, variant_name)
            if not flag:
                out += "[" + str(change_count) + "次]"
                printRed("后台：" + out + "\t达到最大改价次数")
                self.database.finishOneChangeItem(ean, price, variant_name)
                continue

            try:
                elemInput = self.chrome.find_elements_by_xpath(".//div[@class='row collapse advanced-search-container']//input")
                elemSearch = self.chrome.find_elements_by_xpath(".//a[@class='button postfix']")
                if not (len(elemInput) > 0 or len(elemSearch) > 0):
                   return -1
                oldEan = elemInput[0].get_attribute("value")
                elemInput[0].clear()
                elemInput[0].send_keys(ean)
                self.chrome.execute_script("arguments[0].click()", elemSearch[0])
                if ean != oldEan:
                    while True:
                        elemLoading = self.chrome.find_element_by_xpath(".//div[@class='filterView']/div[3]")
                        if elemLoading.get_attribute("loading") == "1":
                            break
                        time.sleep(0.5)
                    time.sleep(1)
                    while True:
                        elemLoading = self.chrome.find_element_by_xpath(".//div[@class='filterView']/div[3]")
                        if elemLoading.get_attribute("loading") == "0":
                            break
                        time.sleep(0.5)
                time.sleep(1.5)
                elemProduct = self.chrome.find_elements_by_xpath(".//table[@id='table-inventory']/tbody/tr[1]/td[4]")
                if len(elemProduct) <= 0:
                    printRed("后台：" + out + "\t没找到这个产品")
                    self.database.finishOneChangeItem(ean, price, variant_name)
                    continue
                # elemProduct[0].click()
                self.chrome.execute_script("arguments[0].click()", elemProduct[0])

                elemPriceInput = self.chrome.find_elements_by_xpath(".//input[@id='editableInput']")
                while len(elemPriceInput) <= 0:
                    elemPriceInput = self.chrome.find_elements_by_xpath(".//input[@id='editableInput']")
                if len(elemPriceInput) <= 0:
                    printRed("后台：" + out + "\t无法获取产品的价格修改控件")
                    self.database.finishOneChangeItem(ean, price, variant_name)
                    continue
                # old_price = round(float(str(elemPriceInput[0].get_attribute("value"))), 2)
                old_price = price + 1
                elemPriceInput[0].clear()
                elemPriceInput[0].send_keys(str(price))
                elemBtn = self.chrome.find_elements_by_xpath(".//a[@class='tiny accept-btn']")
                if len(elemBtn) <= 0:
                    printRed("后台：" + out + "\t无法修改价格确定按钮")
                    self.database.finishOneChangeItem(ean, price, variant_name)
                    continue
                time_change = time.strftime("%Y-%m-%d %H:%M:%S")
                self.chrome.execute_script("arguments[0].click()", elemBtn[0])
                self.database.addAChange(ean, variant_name, old_price, price)
                self.database.addChangeRecord(ean, variant_name, time_change, price)
                out += "[" + str(change_count + 1) + "次]"
                printYellow("后台：" + out + "\t改价成功")
                self.database.finishOneChangeItem(ean, price, variant_name)
            except:
                self.exceptHandler(traceback.format_exc())
                self.database.finishOneChangeItem(ean, price, variant_name)
                continue

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
