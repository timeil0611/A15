import pandas as pd
import pymysql
Series = pd.read_csv("Fred_Popular_Series.csv")
for serie in Series["Fred_Popular_Series"][517:]:#取得熱門大類title    
    print("========================",serie.index[0],".",serie,"============================")

