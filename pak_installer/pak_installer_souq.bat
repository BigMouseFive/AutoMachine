pyinstaller ../auto_souq/deprecated.py -p ../auto_souq/DataManager.py -p ../auto_souq/SpiderProcess.py -p ../auto_souq/OperateProcess.py -i lemon.ico -n handledata -y
xcopy scrapy dist\handledata\scrapy /e /y /i
rd /s /q build
del /f /s /q *.spec
