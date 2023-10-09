from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf 

def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()
# 取得資料
dl = DataLoader()
df = dl.taiwan_stock_daily(
    stock_id='0050', start_date='2000-08-07', end_date='2023-02-25')
# 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date", inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))
df=yf.download('spy')
# backtesting.py
# ta-lib 格式
df2 = df.rename(columns={"High": "high", "Low": "low",})


def SMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA60'] = talib.SMA(df2['Close'], timeperiod=60)
    return df2['SMA60']


def EMA30(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2['EMA30'] = talib.EMA(df2['Close'], timeperiod=60)
    return df2['EMA30']


def WMA30(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2['WMA30'] = talib.WMA(df2['Close'], timeperiod=30)
    return df2['WMA30']

def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA60'] = talib.SMA(df2['Volume'], timeperiod=60)
    return df2['SMA60']

# MA 策略
class MAStra(Strategy):
    n1 = 60
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
        
        self.ema1=self.I(EMA30, self.data)
        # self.I(WMA30, self.data)




    def next(self):


        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data['High']
        # 獲取過去 60 天的最高價
        highest_high = self.high_prices[-80:].max()
        
        # 獲取當前價格
        current_price =self.data['Low'][-1]
        # print("cur",current_price)
        # 如果當前價格比最高價下跌 20% 或更多，賣
        if current_price <= 0.9 * highest_high and self.position.is_long:
            self.position.close()


        # 獲取過去3年的最低值(Vsma60)
        lowest_vaule = self.Vsma1[-750:].min()
        # 獲取當前價格
        current_vaule =self.Vsma1[-1]

        # 獲取當前價格和 60 日移動平均線
        current_price = self.sma1[-1]
        # print(self.sma1[-200:].min())
        lowest_price = self.sma1[-400:].min()

        # 如果當前值比最低值大3倍、60ma的近20個值不再下跌，買
        if (current_vaule >= 3 * lowest_vaule) and (self.ema1[-1]/self.ema1[-20]>=1) and not self.position: 
            self.buy()
            
        # 如果 60ma的近20個值不再下跌，買
        if  (self.ema1[-1]/self.ema1[-20]>=1) and not self.position: 
            self.buy()
           


bt = Backtest(df, MAStra, cash=10000, commission=.0)  # 交易成本 0.0%
stats  = bt.run()
print(stats,stats['_trades'])

bt.plot()
