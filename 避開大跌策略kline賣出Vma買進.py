from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import plot_heatmaps

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

from skopt.plots import plot_objective
from skopt.plots import plot_evaluations

import numpy as np

import seaborn as sns


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account n previous values.
    """
    return pd.Series(values).rolling(n).mean()


# 取得資料
dl = DataLoader()
df = dl.taiwan_stock_daily(
    stock_id="0050", start_date="2000-8-01", end_date="2023-02-25"
)
# 整理資料格式
df = df.rename(columns={"date": "Date"})
df.set_index("Date", inplace=True)
df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df.index)))
# backtesting.py 格式
df1 = df.rename(
    columns={
        "open": "Open",
        "max": "High",
        "min": "Low",
        "close": "Close",
        "Trading_Volume": "Volume",
    }
)
# ta-lib 格式
df2 = df.rename(columns={"max": "high", "min": "low", "Trading_Volume": "Volume"})
# 合併資料
df = pd.merge(df1, df, on="Date")


def SMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2["SMA60"] = talib.SMA(df2["close"], timeperiod=60)
    return df2["SMA60"]


def EMA30(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2["EMA30"] = talib.EMA(df2["close"], timeperiod=60)
    return df2["EMA30"]


def WMA30(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2["WMA30"] = talib.WMA(df2["close"], timeperiod=30)
    return df2["WMA30"]


def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2["SMA60"] = talib.SMA(df2["Trading_Volume"], timeperiod=60)
    return df2["SMA60"]


# MA 策略
class MAStra(Strategy):
    n1 = 60
    n2 = 60
    medium_term_high_prices = 80
    long_term_lowest_vsma = 750
    drop_per = 20
    Vtimes = 3
    mid_term_ema = 20

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n2)

        self.ema1 = self.I(EMA30, self.data)

    def next(self):
        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 60 天的最高價
        highest_high = self.high_prices[-self.medium_term_high_prices :].max()

        # 獲取當前價格
        current_price = self.data["Low"][-1]
        # print("cur",current_price)
        # 如果當前價格比最高價下跌 20% 或更多，賣  (可以寫一個頸線策略)
        if current_price <= (1 - (self.drop_per*0.01)) * highest_high and self.position.is_long:
            self.position.close()

        # 獲取過去3年的最低值(Vsma60)
        lowest_vaule = self.Vsma1[-self.long_term_lowest_vsma :].min()
        # 獲取當前價格
        current_vaule = self.Vsma1[-1]

        # 如果當前值比最低值大3倍、60ma的近20個值不再下跌，買
        if (
            (current_vaule >= self.Vtimes * lowest_vaule)
            and (self.sma1[-1] / self.sma1[-self.mid_term_ema] >= 1)
            and not self.position
        ):
            self.buy()

        # 如果 60ma的近20個值不再下跌，買
        if (self.sma1[-1] / self.sma1[-self.mid_term_ema] >= 1) and not self.position:
            self.buy()


bt = Backtest(df, MAStra, cash=10000, commission=0.001798)  # 交易成本 0.1798%

stats_skopt, heatmap, optimize_result  = bt.optimize(
    n1 = [30,90],
    n2 = [30,90],
    medium_term_high_prices=[40,120],
    long_term_lowest_vsma=[375,1125],
    drop_per=[0,50],
    Vtimes=[1.75,5.5],
    mid_term_ema=[10,30],

    maximize="Equity Final [$]",
    method="skopt",
    max_tries=200,
    random_state=0,
    return_heatmap=True,
    return_optimization=True
)

print(heatmap.sort_values().iloc[-3:])

# hm = heatmap.groupby(["n1", "n2"]).mean().unstack()
# sns.heatmap(hm[::-1], cmap="viridis")
# plt.show()

# plot_heatmaps(heatmap, agg='mean')
# stats  = bt.run()
bt.plot()

print("Return [%]              ", round(stats_skopt["Return [%]"], 2))
print("Buy & Hold Return [%]   ", round(stats_skopt["Buy & Hold Return [%]"], 2))
print("Return (Ann.) [%]       ", round(stats_skopt["Return (Ann.) [%]"], 2))
print("Avg. Drawdown [%]       ", round(stats_skopt["Avg. Drawdown [%]"], 2))
print("Sortino Ratio           ", round(stats_skopt["Sortino Ratio"], 2))

_ = plot_objective(optimize_result, n_points=10)
_ = plot_evaluations(optimize_result, bins=10)
plt.show()
