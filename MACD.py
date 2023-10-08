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
    stock_id='0050', start_date='2000-10-03', end_date='2023-02-25')
# 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date", inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))

# 重新取樣日資料
days='5D'
df = df.resample(days).agg({
    'Trading_Volume': 'sum',
    'Trading_money': 'sum',
    'open': 'first',    # 開盤價使用第一天的值
    'max': 'max',       # 最高價使用五天內的最大值
    'min': 'min',       # 最低價使用五天內的最小值
    'close': 'last',    # 收盤價使用最後一天的值
    'spread': 'last',   # spread 使用最後一天的值
    'Trading_turnover': 'sum'
})

# 移除包含NaN值的列
df = df.dropna()

# backtesting.py 格式
df1 = df.rename(columns={"open": "Open", "max": "High",
                "min": "Low", "close": "Close", "Trading_Volume": "Volume"})
# ta-lib 格式
df2 = df.rename(columns={"max": "high", "min": "low",
                "Trading_Volume": "Volume"})

# 合併資料
df = pd.merge(df1, df2, on="Date")

def MACD(data):    # Data is going to be our OHLCV
    # 取得 MACD 值
    # 计算快速线 (fast_period = 12) 和慢速线 (slow_period = 26)
    df2['fast_line'] = talib.SMA(df2['close'], timeperiod=12)
    df2['slow_line'] = talib.SMA(df2['close'], timeperiod=26)
    # 计算差离值 (DIF)
    df2['dif_line'] = df2['fast_line'] - df2['slow_line']
    # 计算信号线 (DEA)，使用 DIF 的9日简单移动平均
    df2['signal_line'] = talib.SMA(df2['dif_line'], timeperiod=9)
    # 计算 MACD 柱状图 (MACD Histogram)
    df2['macd_histogram'] = df2['dif_line'] - df2['signal_line']
    return df2['macd_histogram']

def dif_line(data):    # Data is going to be our OHLCV
    # 取得 MACD 值
    # 计算快速线 (fast_period = 12) 和慢速线 (slow_period = 26)
    df2['fast_line'] = talib.SMA(df2['close'], timeperiod=12)
    df2['slow_line'] = talib.SMA(df2['close'], timeperiod=26)
    # 计算差离值 (DIF)
    df2['dif_line'] = df2['fast_line'] - df2['slow_line']
    # 计算信号线 (DEA)，使用 DIF 的9日简单移动平均
    df2['signal_line'] = talib.SMA(df2['dif_line'], timeperiod=9)
    # 计算 MACD 柱状图 (MACD Histogram)
    df2['macd_histogram'] = df2['dif_line'] - df2['signal_line']
    return df2['dif_line']

# MACD 策略
class MACDStra(Strategy):
    def init(self):
        self.macd=self.I(MACD, self.data)
        self.dif_line=self.I(dif_line, self.data)

    def next(self):
        if crossover(self.dif_line,  self.macd):  # K<20 買進
            self.buy()
        elif crossover(self.macd, self.dif_line):  # K>80 平倉
            self.position.close()


bt = Backtest(df, MACDStra, cash=10000, commission=.001798)  # 交易成本 0.1798%
output = bt.run()
print(output)
bt.plot()
