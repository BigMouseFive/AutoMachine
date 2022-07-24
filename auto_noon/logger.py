import logging
import os.path
import time


class Logger:
    def __init__(self):
        self.logger = logging.getLogger("test")  # 不加名称设置root logger

    def init(self):
        dir_name = time.strftime("%Y_%m_%d")
        file_name = time.strftime("%H_%M_%S.csv")
        try:
            os.mkdir(dir_name)
        except:
            pass

        formatter = logging.Formatter('%(asctime)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # 使用FileHandler输出到文件
        fh = logging.FileHandler(dir_name + "/" + file_name)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)

        # 使用StreamHandler输出到屏幕
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        # 添加两个Handler
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def info(self, value):
        self.logger.info(value)

    def warning(self, value):
        self.logger.warning(value)

    def error(self, value):
        self.logger.error(value)


logger = Logger()
