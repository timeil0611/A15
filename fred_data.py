from fredapi import Fred
import os

import pandas as pd
pd.set_option('display.max_columns', None)


# 設定 API Key
api_key = 'b6e37a82c73f13022853af515b5875fd'
fred = Fred(api_key=api_key)

Series = pd.read_csv("Fred_Popular_Series.csv")
for serie in Series["Fred_Popular_Series"][10:]:
    id = fred.search(str(serie),order_by='popularity')
    
    print("========================",serie,"============================")
    print(id['id'])

    # for id in id['id']:
    #     data=fred.get_series(series_id=id)#取得fred series
    #     print(id)

    #     data = pd.DataFrame(data)  # 轉換為 DataFrame
    #     data.columns = [id]  # 重命名欄位

    #     fred_dir = "C:\\Users\\timei\\Downloads\\專題code\\FRED"
    #     output_file = os.path.join(fred_dir, str(id) + ".csv")
    #     data.to_csv(output_file, index=True)
