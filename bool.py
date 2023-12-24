from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt
# 取得資料
dl = DataLoader()
df = dl.taiwan_stock_daily(
    stock_id='2618', start_date='2020-1-03', end_date='2023-02-25')
# 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date", inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))

# 重新取樣為五日資料
# days='10D'
# df = df.resample(days).agg({
#     'Trading_Volume': 'sum',
#     'Trading_money': 'sum',
#     'open': 'first',    # 開盤價使用第一天的值
#     'max': 'max',       # 最高價使用五天內的最大值
#     'min': 'min',       # 最低價使用五天內的最小值
#     'close': 'last',    # 收盤價使用最後一天的值
#     'spread': 'last',   # spread 使用最後一天的值
#     'Trading_turnover': 'sum'
# })

# 移除包含NaN值的列
df = df.dropna()

# backtesting.py 格式
df1 = df.rename(columns={"open": "Open", "max": "High",
                "min": "Low", "close": "Close", "Trading_Volume": "Volume"})
# # ta-lib 格式
# df2 = df.rename(columns={"max": "high", "min": "low",
#                 "Trading_Volume": "Volume"})
# 合併資料
df = pd.merge(df1, df, on="Date")


def df_bbnds(data):  # Data is going to be our OHLCV
    # 取得值
    df_bbnds = abstract.BBANDS(df, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0)
    return df_bbnds

# 策略
class BoolStra(Strategy):
    def init(self):
        self.df_bbnds=self.I(df_bbnds, self.data)
        

    def next(self):
        if crossover(self.data.Close, self.df_bbnds[2]):  # Close>lowerband 買進 
            self.buy()
        elif crossover(self.df_bbnds[0], self.data.Close):  # Close>upperband 平倉
            self.position.close()
            
            


bt = Backtest(df, BoolStra, cash=10000, commission=.001798)  # 交易成本 0.1798%
output = bt.run()
print(output)
bt.plot()
