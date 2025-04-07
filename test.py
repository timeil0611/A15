from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf
    
import numpy as np


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()


start = "1980-01-01"

# 取得資料
qqq = pd.read_csv("qqq.csv")
print
tqqq_mock = pd.read_csv("TQQQ_Mock_kline.csv")
df=tqqq_mock

# 設定Index
df.set_index("Date", inplace=True)
df.set_index(pd.DatetimeIndex(df.index), inplace=True)



# backtesting.py
# ta-lib 格式
df2 = df.rename(
    columns={
        "High": "high",
        "Low": "low",
    }
)


# #合併資料
qqq.set_index("Date", inplace=True)
qqq.set_index(pd.DatetimeIndex(qqq.index), inplace=True)
qqq = qqq[start:]
df = pd.concat([df, qqq], axis=1)
qqq = qqq[["qqq"]]






def QQQ(data):  # Data is going to be our OHLCV
    # 取得qqq值
    return data

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

def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2["SMA60"] = talib.SMA(df2["Volume"], timeperiod=60)
    return df2["SMA60"]



class TrailingStrategy(Strategy):

    __sl_amount = 6.

    def init(self):
        super().init()

    def set_trailing_sl(self, sl_amount: float = 6):
        """
    Set the trailing stop loss as $n below the current price (for long positions)
        Works for future bars only
        """
        self.__sl_amount = sl_amount

    def next(self):
        super().next()
        # Can't use index=-1 because self.__atr is not an Indicator type
        index = len(self.data)-1

        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(trade.sl or -np.inf,
                               self.data.Close[index] -  self.__sl_amount)
            else:
                trade.sl = min(trade.sl or np.inf,
                               self.data.Close[index] +  self.__sl_amount)

    
# MA 策略
class MAStra(TrailingStrategy):
    n1 = 20 # days
    cooldown_days = 4
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
        self.ema1 = self.I(EMA30, self.data)
        self.qqq = self.I(QQQ, qqq["qqq"])
        print(self.data)
        self.cooldown_weeks = 4
        self.last_trade_date = pd.to_datetime("1981-07-31")  # 設定初值

    def next(self):  # buy ,close 要互斥
        # 當前qqq價格
        qqq_current_price = self.data["qqq"][-1]
         # 定義一個用於存儲最高價的 Series
        self.qqq_high_prices = self.data["qqq"]
        # 獲取過去 80 天的最高價
        qqq_highest_high = self.qqq_high_prices[-80:].max()
        
        # 獲取當前Tqqq價格
        current_price = self.data["Low"][-1]
         # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 80 天的最高價
        highest_high = self.high_prices[-80:].max()
        
        # 如果當前價格比買入價下跌 10% 或更多，賣
        if (
            ((self.data.index[-1].month==9)
            or
            ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
            or
            (qqq_current_price <= 0.9 * qqq_highest_high)
            )
            and 
            (self.position.is_long)
        ):
            self.position.close()
            # print(self.data.index[-1],"close")
            # print('buy_price',buy_price)
        # 如果 60ma的近20個值不再下跌，買
        if (
            not
            ((self.data.index[-1].month==9)
            or
            ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
            or
            (current_price <= 0.9 * highest_high)
            )

            
            and
            (self.sma1[-1] - self.sma1[-2] > 0)
            and
            (not self.position)
            
        ):
            self.buy()
            # 定義一個用於存儲買入價的 Series
            buy_price = self.data["Close"][-1]
            # print(self.data.index[-1],"buy")
            # print(buy_price)
        
        
        


bt = Backtest(df, MAStra, cash=10000, commission=0.0002,exclusive_orders=True)  # 交易成本 0.0%
stats = bt.run()

# print(stats)
print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))
print("Win Rate [%]            ", round(stats["Win Rate [%]"], 2))


# bt.plot(resample='1W')
