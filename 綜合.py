from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt
def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()
# 取得資料
dl = DataLoader()
df = dl.taiwan_stock_daily(
    stock_id='0050', start_date='2000-10-03', end_date='2023-02-25')
# 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date", inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))
# backtesting.py 格式
df1 = df.rename(columns={"open": "Open", "max": "High",
                "min": "Low", "close": "Close", "Trading_Volume": "Volume"})
# ta-lib 格式
df2 = df.rename(columns={"max": "high", "min": "low",
                "Trading_Volume": "Volume"})
# 合併資料(backtesting.py 格式)
df = pd.merge(df1, df, on="Date")


## 指標

# KD指標
# 取得 KD 值
df_kd = abstract.STOCH(df2, fastk_period=9, slowk_period=3, slowd_period=3)
# 合併資料
df = pd.merge(df, df_kd, on="Date")
def STOCH(data):
    # Data is going to be our OHLCV
    df_kd = abstract.STOCH(df2, fastk_period=9, slowk_period=3, slowd_period=3)
    return df_kd

# SMA指標
def SMA1(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA1'] = talib.SMA(df2['close'], timeperiod=10)
    return df2['SMA1']
def SMA2(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA2'] = talib.SMA(df2['close'], timeperiod=20)
    return df2['SMA2']

# EMA指標
def EMA30(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2['EMA30'] = talib.EMA(df2['close'], timeperiod=30)
    return df2['EMA30']

# WMA指標
def WMA30(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2['WMA30'] = talib.WMA(df2['close'], timeperiod=30)
    return df2['WMA30']

# VSMA指標
def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA60'] = talib.SMA(df2['Trading_Volume'], timeperiod=60)
    return df2['SMA60']

# 布林通道指標
def df_bbnds(data):  # Data is going to be our OHLCV
    # 取得值
    df_bbnds = abstract.BBANDS(df, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0)
    return df_bbnds


# MACD指標
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

# MACD(dif)指標
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

# RSI指標
def RSI(data):  # Data is going to be our OHLCV
    # 取得RSI值
    df['RSI14'] = talib.RSI(df['close'], timeperiod=6)
    return df['RSI14']

# 策略
class MAStra(Strategy):

    ## 指標函式init(要顯示指標的話需在這寫)
    n1 = 60
    def init(self):
        print(self.data)
        self.sma1 = self.I(SMA1, self.data)    # SMA指標
        self.sma2 = self.I(SMA2, self.data)    # SMA指標
        self.ema1 = self.I(EMA30, self.data)   # EMA指標
        self.wma1 =self.I(WMA30, self.data)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1) # VSMA指標
        self.df_bbnds=self.I(df_bbnds, self.data) # 布林通道指標
        self.I(STOCH, self.data) # KD指標
        self.macd=self.I(MACD, self.data) # MACD指標
        self.dif_line=self.I(dif_line, self.data) # MACD(dif)指標
        self.ris=self.I(RSI, self.data) # RSI指標

        # 定義一個用於存儲 60 日移動平均線的 Series
        
        # self.ma_60 = df2['close'].rolling(window=60).mean()

        print(len(self.sma1))
        # print(self.ma_60)
        
    ## 買賣函式
    def next(self):
        if crossover(20, self.data.slowk):  # K<20 買進
            self.buy()
        elif crossover(self.data.slowk, 80):  # K>80 平倉
            self.position.close()
        


bt = Backtest(df, MAStra, cash=10000, commission=.001798)  # 交易成本 0.1798%
stats  = bt.run()
print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
print("年化報酬 [%]       ", round(stats["Return (Ann.) [%]"], 2))
print("平均回落 [%]       ", round(stats["Avg. Drawdown [%]"], 2))
print("Sortino 比率           ", round(stats["Sortino Ratio"], 2))
print("勝率 [%]            ", round(stats["Win Rate [%]"], 2))

bt.plot()
