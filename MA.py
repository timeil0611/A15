from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt
# 取得資料
dl = DataLoader()
df = dl.taiwan_stock_daily(stock_id='0050', start_date='2008-10-03', end_date='2023-02-25')
## 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date" , inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))
## backtesting.py 格式
df1 = df.rename(columns={"open": "Open", "max": "High", "min": "Low", "close": "Close", "Trading_Volume": "Volume"})
## ta-lib 格式
df2 = df.rename(columns={"max": "high", "min": "low", "Trading_Volume": "Volume"})
df2['SMA30'] = talib.SMA(df2['close'], timeperiod=30)
df2['EMA30'] = talib.EMA(df2['close'], timeperiod=30)
df2['WMA30'] = talib.WMA(df2['close'], timeperiod=30)
plt.plot(df2[['close','SMA30','EMA30','WMA30']])
plt.show()