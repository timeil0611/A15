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
df = yf.download("spy")
# backtesting.py
# ta-lib 格式
df2 = df.rename(
    columns={
        "High": "high",
        "Low": "low",
    }
)


def SMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2["SMA60"] = talib.SMA(df2["Close"], timeperiod=60)
    return df2["SMA60"]


def EMA30(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2["EMA30"] = talib.EMA(df2["Close"], timeperiod=60)
    return df2["EMA30"]


def WMA30(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2["WMA30"] = talib.WMA(df2["Close"], timeperiod=30)
    return df2["WMA30"]


# MA 策略
class MAStra(Strategy):
    n1 = 60

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.ma_60 = self.I(SMA60, self.data)
        self.ema1 = self.I(EMA30, self.data)
        # self.I(WMA30, self.data)

    def next(self):
        if self.data["Open"][-1] == 37.09:
            self.buy()

        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 60 天的最高價
        highest_high = self.high_prices[-100:].max()
        

        # 獲取當前價格
        current_price = self.data["Low"][-1]
        
        # 如果當前價格比最高價下跌 10% 或更多，則平倉
        if current_price <= 0.9 * highest_high:
            self.position.close()
            

        
        # 獲取當前價格和 60 日移動平均線
        current_price = self.sma1[-1]
        lowest_price = self.sma1[-400:].min()

        # 如果 60 日移動平均線在200值內從低點上漲 10%，則進行買入
        if (current_price / lowest_price) >= 1.10 and (
            self.ema1[-1] / self.ema1[-20] >= 1
        ):
            self.buy()

        # 如果 60ma的近20個值不再下跌，買
        if (self.ema1[-1] / self.ema1[-20] >= 1) and not self.position:
            self.buy()


bt = Backtest(df, MAStra, cash=10000, commission=0.0)  # 交易成本 0.0%
stats = bt.run()

print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))
print("Win Rate [%]            ", round(stats["Win Rate [%]"], 2))

bt.plot()
