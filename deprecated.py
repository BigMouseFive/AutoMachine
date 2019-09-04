# -*- coding: utf-8 -*-
from multiprocessing import freeze_support
import os
from colorama import init
from DataManager import DataManager
from OperateProcess import OperateProcess
from SpiderProcess import SpiderProcess


def pre_test(name):
    # pre database
    db = DataManager(name)
    db.initShopDataBase()

    # pre log.txt
    log_file = name + ".log"
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except PermissionError:
            print("PermissionError")


def skr(name):
    if __name__ == '__main__':
        freeze_support()
        os.chdir(os.path.split(os.path.realpath(__file__))[0])
        # pre_test(name)
        p1 = OperateProcess(name)
        p1.start()
        while False:
            p = SpiderProcess(name=name)
            p.start()
            p.join()
            database = DataManager(name)
            database.handlerStatus()


init(autoreset=True)
skr("BuyMore")
# os.system("title AutoMacine " + sys.argv[1])
# skr(sys.argv[1])
