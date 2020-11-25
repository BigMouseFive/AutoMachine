# -*- coding: utf-8 -*-
import os
import sys
from multiprocessing import freeze_support
from auto_noon.DataManager import DataManager
from auto_noon.OperateProcess import OperateProcess
from auto_noon.SpiderProcess import SpiderProcess


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


if __name__ == '__main__':
    freeze_support()
    name = sys.argv[1]
    os.system("title AutoMacine " + name)
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
    pre_test(name)
    p1 = OperateProcess(name)
    p1.start()
    while True:
        p = SpiderProcess(name=name)
        p.start()
        p.join()
        database = DataManager(name)
        database.handlerStatus()


# def skr(name):
#     if __name__ == '__main__':
#         os.system("title AutoMacine " + name)
#         freeze_support()
#         os.chdir(os.path.split(os.path.realpath(__file__))[0])
#         pre_test(name)
#         p1 = OperateProcess(name)
#         p1.start()
#         while True:
#             p = SpiderProcess(name=name)
#             p.start()
#             p.join()
#             database = DataManager(name)
#             database.handlerStatus()
#         p1.join()


# skr("BuyMore")
# skr("DZ-store")

