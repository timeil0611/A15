from bs4 import BeautifulSoup
import pandas as pd
import requests

df=pd.DataFrame({"Fred_Popular_Series":[]})

for page in range(1, 31):
    # 連結網站
    response = requests.get(
    	"https://fred.stlouisfed.org/tags/series?et=&ob=pv&od=&t=&tg=&tt=&pageID="+str(page))
    
    # HTML原始碼解析
    soup = BeautifulSoup(response.text, "html.parser")
    
    titles = soup.find_all("div", class_ = "display-results-title col-xs-12 col-sm-10")

    print(f"====================第{str(page)}頁====================")
    for title in titles:
        df = df._append({'Fred_Popular_Series':title.a.text},ignore_index=True)
        
df.to_csv('Fred_Popular_Series.csv', index=True)