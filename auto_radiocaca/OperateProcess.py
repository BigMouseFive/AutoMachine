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
from auto_radiocaca.DataManager import DataManager
import logging
CHROME_DRIVER_PATH = "../chromedriver.exe"


class OperateProcess(object):
    def __init__(self):
        self.database = DataManager()
        self.database.init_shop_dataBase()

    def run(self):  # 固定用run方法，启动进程自动调用run方法
        self.init_chrome()
        self.login_metamask()
        self.loop_execute()

    def init_chrome(self):
        logging.info("初始化浏览器")
        option = webdriver.ChromeOptions()
        option.add_argument("user-data-dir=C:/Users/戴锐/AppData/Local/Google/Chrome/User Data")
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-dev-shm-usage')
        # option.add_argument("headless")
        # option.add_argument("--window-size=1920,1050")
        option.add_argument('ignore-certificate-errors')
        option.add_argument('log-level=3')
        option.add_argument('lang=zh_CN.UTF-8')
        prefs = {
            'profile.default_content_setting_values': {
                'images': 1,
                'stylesheet': 2,
            }
        }
        option.add_experimental_option('prefs', prefs)
        self.chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=option)
        self.chrome.maximize_window()

    def switch_window_to_url(self, url, count=1):
        while count > 0:
            for window_handle in self.chrome.window_handles:
                self.chrome.switch_to.window(window_handle)
                logging.debug(self.chrome.current_url)
                if url in self.chrome.current_url:
                    return True
            time.sleep(0.5)
            count -= 1
        return False

    def login_metamask(self):
        logging.info("登录钱包")
        self.chrome.get("https://market.radiocaca.com/#/market-place/")
        self.checkPage()
        try:
            if self.switch_window_to_url("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/notification.html#unlock"):
                ret = self.chrome.find_elements_by_xpath("//input[@id='password']")
                if len(ret) > 0:
                    pass_input = ret[0]
                    pass_input.send_keys("12345ssdlH.....")
                    time.sleep(2)
                    unlock_btn = self.chrome.find_element_by_xpath("//button")
                    unlock_btn.click()
        except:
            traceback.print_exc()

    def loop_execute(self):
        logging.info("开始购买")
        while True:
            first_buy_now = self.database.get_first_buy_now()
            if first_buy_now:
                s_id = str(first_buy_now["id"])
                url = "https://market.radiocaca.com/#/market-place/" + s_id
                js = 'window.open("' + url + '")'
                self.chrome.execute_script(js)
                logging.info("[" + s_id + "] " + "打开产品页面: " + url)
                self.checkPage()
                self.switch_window_to_url(url)

                # 获取buy now按钮
                xpath_url = "//button[contains(@class, 'buy-btn')]"
                WebDriverWait(self.chrome, 5, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath_url)))
                buy_btn = self.chrome.find_element_by_xpath(xpath_url)
                self.chrome.execute_script("arguments[0].click()", buy_btn)
                logging.info("[" + s_id + "] " + "点击购买")

                # 获取approve按钮
                xpath_url = "//button[contains(@class, 'approve-btn')]"
                WebDriverWait(self.chrome, 5, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath_url)))
                approve_btn = self.chrome.find_element_by_xpath(xpath_url)
                self.chrome.execute_script("arguments[0].click()", approve_btn)
                logging.info("[" + s_id + "] " + "点击授权")

                # 钱包授权
                approve_flag = False
                if self.switch_window_to_url("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/notification.html#confirm-transaction", 5):
                    next_btn = self.chrome.find_element_by_xpath("//button[contains(@data-testid, 'page-container-footer-next')]")
                    cancel_btn = self.chrome.find_element_by_xpath("//button[contains(@data-testid, 'page-container-footer-cancel')]")
                    if logging.info(next_btn.get_attribute("disabled")):
                        self.chrome.execute_script("arguments[0].click()", next_btn)
                        logging.info("[" + s_id + "] " + "钱包授权成功")
                        approve_flag = True
                    else:
                        logging.warning("[" + s_id + "] " + "余额不足，点击拒绝")
                        self.chrome.execute_script("arguments[0].click()", cancel_btn)

                # 切换到产品页面
                self.switch_window_to_url(url)
                # 判断授权是否成功
                if approve_flag:
                    buy_btn = self.chrome.find_element_by_xpath("//div[contains(@class, 'buttonBox')]/button[1]")
                    self.chrome.execute_script("arguments[0].click()", buy_btn)
            else:
                time.sleep(1)

    def checkPage(self):
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
        return self.chrome.execute_script(checkPageFinishScript)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    operate_process = OperateProcess()
    operate_process.run()
