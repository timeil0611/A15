
import pandas as pd
import yfinance as yf
df = pd.read_csv('qqq.csv')
df.set_index("Date", inplace=True)
df[["Column2",'sdad']] = df["qqq"]
print(df)