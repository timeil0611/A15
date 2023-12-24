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
    n1 = 12
    period_high=12
    drop=0.9
    short_period=25
    long_period=50
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.ma_12=self.I(SMA12, self.data)
        self.ema1=self.I(EMA6, self.data)
        # self.I(WMA6, self.data)
        

    def next(self):
        
        ## 賣出清倉條件
        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data['High']
        
        # 獲取過去 60 天的最高價
        highest_price = self.high_prices[-self.period_high:].max()
        
        # 獲取當前價格
        current_price =self.data['Low'][-1]

        # 如果當前價格比最高價下跌 x% 或更多、破區間新低，則清倉
        if current_price <= self.drop * highest_price and self.position.is_long :
            self.position.close()

       # 定義一個用於存儲最低價的 Series
        self.low_price = self.data['Low']
        if (len(self.low_price)>self.short_period):
            # 獲取過去兩區間的最低價
            lowest_prices = self.low_price[-self.short_period:].min()
            lowest_prices2 = self.low_price[-self.long_period:-self.short_period].min()
            
            # 如果最近一區間跌破上一區間最低價，清倉
            if(lowest_prices<=lowest_prices2) and self.position.is_long:
                self.position.close()



        ## 買進條件
        # 定義一個用於存儲最低價的 Series
        self.low_price = self.data['Low']
        if (len(self.low_price)>self.short_period):
            # 獲取過去兩區間的最低價
            lowest_prices = self.low_price[-self.short_period:].min()
            lowest_prices2 = self.low_price[-self.long_period:-self.short_period].min()
            # 如果最近一區間內價格都不跌破上一區間最低價，買進
            if(lowest_prices>=lowest_prices2):
                self.buy()

        # 如果 12wk ma的近4個值不再下跌，買
        # if  (self.ema1[-1]/self.ema1[-4]>=1) and not self.position: 
        #     self.buy()


bt = Backtest(df, MAStra, cash=10000, commission=.0)  # 交易成本 0.0%
stats_skopt, heatmap, optimize_result = bt.optimize(
    period_high=[5,20],
    drop=[0.5,1],
    short_period=[10,40],
    long_period=[30,70],
    constraint=lambda p: p.short_period<p.long_period,
    maximize='Equity Final [$]',
    method='skopt',
    max_tries=200,
    random_state=0,
    return_heatmap=True,
    return_optimization=True)

print(heatmap.sort_values().iloc[-3:])

bt.plot()

print('Return [%]              ',round(stats_skopt['Return [%]'], 2))
print('Buy & Hold Return [%]   ',round(stats_skopt['Buy & Hold Return [%]'], 2))
print('Return (Ann.) [%]       ',round(stats_skopt['Return (Ann.) [%]'], 2))
print('Avg. Drawdown [%]       ',round(stats_skopt['Avg. Drawdown [%]'], 2))
print('Sortino Ratio           ',round(stats_skopt['Sortino Ratio'], 2))

_ = plot_objective(optimize_result, n_points=10)
_ = plot_evaluations(optimize_result, bins=10)
plt.show()




