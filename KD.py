from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract

## 取得資料
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
## 取得 KD 值
df_kd = abstract.STOCH(df2,fastk_period=108, slowk_period=3,slowd_period=3)
## 合併資料
df1 = pd.merge(df1, df_kd, on="Date")

## KD 策略
class KdCross(Strategy):
    def init(self):
        super().init()
        
    def next(self):
        if crossover(20, self.data.slowk): ## K<20 買進
            self.buy()
        elif crossover(self.data.slowk, 80): ## K>80 平倉
            self.position.close()
            
bt = Backtest(df1, KdCross, cash=10000, commission=.001798) ## 交易成本 0.1798%
output = bt.run()
print(output)
bt.plot()