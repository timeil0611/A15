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
    stock_id='0050', start_date='2000-8-01', end_date='2023-02-25')
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
# 合併資料
df = pd.merge(df1, df, on="Date")


def SMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA60'] = talib.SMA(df2['close'], timeperiod=60)
    return df2['SMA60']


def EMA30(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2['EMA30'] = talib.EMA(df2['close'], timeperiod=60)
    return df2['EMA30']


def WMA30(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2['WMA30'] = talib.WMA(df2['close'], timeperiod=30)
    return df2['WMA30']

def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA60'] = talib.SMA(df2['Trading_Volume'], timeperiod=60)
    return df2['SMA60']

# MA 策略
class MAStra(Strategy):
    n1 = 60
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
        
        self.ema1=self.I(EMA30, self.data)
        # self.I(WMA30, self.data)
        # 定義一個用於存儲 60 日移動平均線的 Series
        
        # self.ma_60 = df2['close'].rolling(window=60).mean()

        print(len(self.sma1))
        # print(self.data.df.index)

    def next(self):


        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data['High']
        # 獲取過去 60 天的最高價
        highest_high = self.high_prices[-80:].max()
        
        # 獲取當前價格
        current_price =self.data['Low'][-1]
        # print("cur",current_price)
        # 如果當前價格比最高價下跌 20% 或更多，賣
        if current_price <= 0.8 * highest_high and self.position.is_long:
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
        if (current_vaule >= 3 * lowest_vaule) and (self.sma1[-1]/self.sma1[-20]>=1) and not self.position: 
            self.buy()
            
        # 如果 60ma的近20個值不再下跌，買
        if  (self.sma1[-1]/self.sma1[-20]>=1) and not self.position: 
            self.buy()
           


bt = Backtest(df, MAStra, cash=10000, commission=.001798)  # 交易成本 0.1798%
stats  = bt.run()
print(stats,stats['_trades'])

bt.plot()
