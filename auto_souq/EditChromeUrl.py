import os
import time

from selenium import webdriver
CHROME_DRIVER_PATH = "../chromedriver.exe"

option = webdriver.ChromeOptions()
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')
# option.add_argument("headless")
option.add_argument('ignore-certificate-errors')
option.add_argument('log-level=3')
option.add_argument('lang=zh_CN.UTF-8')
chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=option)
chrome.get("chrome://appcache-internals/")
readyUri = "https://www.baidu.com/"
js = 'window.open("' + readyUri + '")'
chrome.execute_script(js)
time.sleep(5)
handler = chrome.current_window_handle
for h in chrome.window_handles:
    if h != handler:
        chrome.switch_to.window(h)
time.sleep(5)
chrome.close()
chrome.switch_to.window(handler)
readyUri = "https://www.baidu.com/"
js = 'window.open("' + readyUri + '")'
chrome.execute_script(js)
for h in chrome.window_handles:
    if h != handler:
        chrome.switch_to.window(h)
time.sleep(5)
chrome.close()
time.sleep(10)
chrome.quit()

