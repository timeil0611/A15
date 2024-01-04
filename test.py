import pandas as pd
import pymysql

# 創建一個 df
df = pd.DataFrame({
    "name": ["John", "Jane", "Mary"],
    "age": [30, 25, 20]
})

# 連接到 MySQL 伺服器
conn = pymysql.connect(host="localhost", port=3307, user="root", password="0611", database="icecream")

# 將 df 寫入到 MySQL 表
df.to_sql("my_table", conn, if_exists="replace", index=True)

# 關閉連接
conn.close()
