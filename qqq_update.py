import yfinance as yf
import pandas as pd
qqq = pd.read_csv("qqq.csv")
print(qqq.info())
print(qqq)


df = pd.read_csv("test.csv")
print("_______________________________________")
print(df.info())
print(df)

df_combined = pd.concat([qqq, df], axis=0, ignore_index=True)
print(df_combined)
df_combined.to_csv('test.csv', index=True)