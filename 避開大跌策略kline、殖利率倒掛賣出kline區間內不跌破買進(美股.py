from backtesting import Backtest, Strategy
import seaborn as sns

from skopt.plots import plot_objective
from skopt.plots import plot_evaluations

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf 

import csv


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()
# 取得資料
df=yf.download('^GSPC',start='1920-6-7',end='2023-10-01',interval='1wk')

#避免Open出現0值
df['Open'] = df.apply(lambda row: row['Close'] if row['Open'] == 0 else row['Open'], axis=1)

# ta-lib 格式
df2 = df.rename(columns={"High": "high", "Low": "low",})



def SMA12(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA12'] = talib.SMA(df2['Close'], timeperiod=12)
    return df2['SMA12']


def EMA6(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2['EMA6'] = talib.EMA(df2['Close'], timeperiod=12)
    return df2['EMA6']


def WMA6(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2['WMA6'] = talib.WMA(df2['Close'], timeperiod=6)
    return df2['WMA6']

# MA 策略
class MAStra(Strategy):
    n1 = 60
    cooldown_days = 4

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
        self.ema1 = self.I(EMA6, self.data)
        # self.qqq = self.I(QQQ, qqq["qqq"])

        self.cooldown_weeks = 6
        self.last_trade_date = pd.to_datetime("1950-01-01")  # 設定初值

    def next(self):
        # # self.buy()

        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 60 天的最高價
        highest_high = self.high_prices[-80:].max()

        # 獲取當前價格
        current_price = self.data["Low"][-1]
        # print("cur",current_price)

        # 獲取過去3年的最低值(Vsma60)
        lowest_vaule = self.Vsma1[-750:].min()
        # 獲取當前價格
        current_vaule = self.Vsma1[-1]

        # 獲取當前價格和 60 日移動平均線
        
        # print(self.sma1[-200:].min())
        lowest_price = self.sma1[-400:].min()
        
        # 如果當前價格比最高價下跌 10% 或更多，賣
        if current_price <= 0.9 * highest_high and self.position.is_long:
            self.position.close()
            self.last_trade_date = self.data.index[-1]


        # 如果當前交易量放大(比最低值大3倍)、60ma的近20個值不再下跌，經過冷卻，買
        if (
            (current_vaule >= 3.5 * lowest_vaule)
            and (
                (self.data.index[-1] - self.last_trade_date).days / 5
                > self.cooldown_weeks
            )
            and (self.ema1[-1] / self.ema1[-20] >= 1)
            and not self.position
        ):
            self.buy()

        # 如果 60ma的近20個值不再下跌，買
        if (
            (self.ema1[-1] / self.ema1[-20] >= 1)
            and (
                (self.data.index[-1] - self.last_trade_date).days / 5
                > self.cooldown_weeks
            )
            and not self.position
        ):
            self.buy()


bt = Backtest(df, MAStra, cash=10000, commission=.0)  # 交易成本 0.0%
# stats_skopt, heatmap, optimize_result = bt.optimize(
#     period_high=[5,20],
#     drop=[0.5,1],
#     short_period=[10,40],
#     long_period=[30,70],
#     constraint=lambda p: p.short_period<p.long_period,
#     maximize='Equity Final [$]',
#     method='skopt',
#     max_tries=200,
#     random_state=0,
#     return_heatmap=True,
#     return_optimization=True)

# print(heatmap.sort_values().iloc[-3:])
stats  = bt.run()
bt.plot()

print('Return [%]              ',round(stats['Return [%]'], 2))
print('Buy & Hold Return [%]   ',round(stats['Buy & Hold Return [%]'], 2))
print('Return (Ann.) [%]       ',round(stats['Return (Ann.) [%]'], 2))
print('Avg. Drawdown [%]       ',round(stats['Avg. Drawdown [%]'], 2))
print('Sortino Ratio           ',round(stats['Sortino Ratio'], 2))

# _ = plot_objective(optimize_result, n_points=10)
# _ = plot_evaluations(optimize_result, bins=10)
# plt.show()




