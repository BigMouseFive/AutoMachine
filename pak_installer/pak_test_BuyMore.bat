copy "..\BuyMore.db" "dist\deprecated\"
copy "..\DataBase.db" "dist\deprecated\"
copy "..\chromedriver.exe" "dist\deprecated\"
xcopy "..\scrapy" "dist\deprecated\scrapy" /e
"dist\deprecated\deprecated.exe" BuyMore
pause