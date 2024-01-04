from fredapi import Fred
from ratelimit import limits, sleep_and_retry
import urllib.request

import os

import pandas as pd

pd.set_option("display.max_columns", None)

import time


# 設定 API Key
api_key = "b6e37a82c73f13022853af515b5875fd"
fred = Fred(api_key=api_key)

Series = pd.read_csv("Fred_Popular_Series.csv")


i = 0
for serie in Series["Fred_Popular_Series"][697:]:  # 取得熱門大類title
    id = fred.search(str(serie), order_by="popularity", limit=100)

    print("========================", i, ".", serie, "============================")
    print(id["id"])
    i += 1

    retry_count = 0
    max_backoff = 60  # 設定最大重試時間為 60 秒
    for id in id["id"]:  # 取得熱門大類title裡子類的id
        try:
            data = fred.get_series(series_id=id)  # 取得fred series
            print(id)

            data = pd.DataFrame(data)  # 轉換為 DataFrame
            data.columns = [id]  # 重命名欄位

            fred_dir = "C:\\Users\\timei\\Downloads\\專題code\\FRED"
            output_file = os.path.join(fred_dir, str(id) + ".csv")
            data.to_csv(output_file, index=True)
        except (urllib.error.URLError, ValueError) as e:
            if "Too Many Requests" or "Service Unavailable" in str(e):
                print("Too many requests, waiting...")
                time.sleep(2**retry_count)  # 指數退避
                retry_count += 1
                if retry_count > max_backoff:
                    # 超過最大重試次數，放棄
                    raise e
            elif isinstance(e, TimeoutError):
                print("Timeout, waiting...")
                time.sleep(2**retry_count)  # 指數退避
                retry_count += 1
                if retry_count > max_backoff:
                    # 超過最大重試次數，放棄
                    raise e
            else:
                raise e
