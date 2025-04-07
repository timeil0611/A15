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


start = "1980-01-01"

# 取得資料
df = yf.download("^GSPC", start="1984-02-17", end="2023-10-20", interval="1d")
qqq = pd.read_csv("qqq.csv")
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


# MA 策略
class MAStra(Strategy):
    n1 = 60
    cooldown_days = 4

    def init(self):
        # 顯示線圖
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
        self.ema1 = self.I(EMA30, self.data)
        self.qqq = self.I(QQQ, qqq["qqq"])
        print(self.data)
        self.cooldown_weeks = 6
        self.last_trade_date = pd.to_datetime("1981-07-31")  # 設定初值

    def next(self):
        # self.buy()
        
        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 80 天的最高價
        highest_high = self.high_prices[-80:].max()

        # 獲取當前價格
        # current_price = self.data["Low"][-1]

        # 獲取過去3年的最低值(Vsma60)
        lowest_vaule = self.Vsma1[-750:].min()
        # 獲取當前價格
        current_vaule = self.Vsma1[-1]

        # 獲取當前價格和 60 日移動平均線
        current_price = self.sma1[-1]
        
        # print(self.sma1[-200:].min())
        lowest_price = self.sma1[-400:].min()

        # # 如果當前價格比最高價下跌 10% 或更多，賣
        # if current_price <= 0.9 * highest_high and self.position.is_long:
        #     self.position.close()
        #     self.last_trade_date = self.data.index[-1]

        # # 如果當前交易量放大(比最低值大3倍)、60ma的近20個值不再下跌，經過冷卻，買
        if(current_price>10):
            self.buy()
        # if (
        #     (current_vaule >= 3.5 * lowest_vaule)
        #     and
        #       (
        #         (self.data.index[-1] - self.last_trade_date).days / 5
        #         > self.cooldown_weeks
        #     )
        #     and (self.ema1[-1] / self.ema1[-20] >= 1)
        #     and not self.position
        # ):
        #     self.buy()

        # # 如果 60ma的近20個值不再下跌，買
        # if (
        #     (self.ema1[-1] / self.ema1[-20] >= 1)
        #     and (
        #         (self.data.index[-1] - self.last_trade_date).days / 5
        #         > self.cooldown_weeks
        #     )
        #     and not self.position
        # ):
        #     self.buy()
        


bt = Backtest(df, MAStra, cash=10000, commission=0.0)  # 交易成本 0.0%
stats = bt.run()

# print(stats)
print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))
print("Win Rate [%]            ", round(stats["Win Rate [%]"], 2))


bt.plot(resample='1W')
