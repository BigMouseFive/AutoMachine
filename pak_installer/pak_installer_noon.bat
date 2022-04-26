rd /s /q dist\deprecated
pyinstaller ../auto_noon/deprecated.py -p ../auto_noon -i lemon.ico -n deprecated -y
xcopy scrapy dist\deprecated\scrapy /e /y /i
rd /s /q build
del /f /s /q *.spec
