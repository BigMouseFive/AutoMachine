pyinstaller ../auto_amazon/deprecated.py -p ../amazon/DataManager.py -p ../auto_amazon/SpiderProcess.py -p ../auto_amazon/OperateProcess.py -i lemon.ico -n matchscale -y
xcopy scrapy dist\matchscale\scrapy /e /y /i
rd /s /q build
del /f /s /q *.spec
