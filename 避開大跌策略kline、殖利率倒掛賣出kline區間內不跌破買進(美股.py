from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf 

import csv

# 讀取CSV
dfT10Y2Y = pd.read_csv('T10Y2Y(W).csv')
dfT10Y2Y = dfT10Y2Y.rename(columns={"DATE": "Date"})
dfT10Y2Y.set_index("Date", inplace=True)


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()

# 取得資料
df=yf.download('^GSPC',start='1978-6-7',end='2023-10-01',interval='1wk')

#避免Open出現0值
df['Open'] = df.apply(lambda row: row['Close'] if row['Open'] == 0 else row['Open'], axis=1)

# ta-lib 格式
df2 = df.rename(columns={"High": "high", "Low": "low",})

# #合併資料
dfT10Y2Y.set_index(pd.DatetimeIndex(dfT10Y2Y.index), inplace=True)
dfT10Y2Y = pd.concat([df, dfT10Y2Y], axis=1, join='inner')
dfT10Y2Y = dfT10Y2Y[['T10Y2Y']]

# 將T10Y2Y['T10Y2Y']轉為numeric
dfT10Y2Y['T10Y2Y'] = pd.to_numeric(dfT10Y2Y['T10Y2Y'], errors='coerce')

def T10Y2Y(data):  # Data is going to be our OHLCV
    # 取得T10Y2Y值
    return data

def SMA12(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2['SMA12'] = talib.SMA(df2['Close'], timeperiod=12)
    return df2['SMA12']

def EMA12(data):  # Data is going to be our OHLCV
    # 取得EMA值
    df2['EMA12'] = talib.EMA(df2['Close'], timeperiod=12)
    return df2['EMA12']

def WMA12(data):  # Data is going to be our OHLCV
    # 取得WMA值
    df2['WMA12'] = talib.WMA(df2['Close'], timeperiod=12)
    return df2['WMA12']



# MA 策略
class MAStra(Strategy):
    n1 = 12
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.ma_12=self.I(SMA12, self.data)
        self.ema1=self.I(EMA12, self.data)
        # self.I(WMA12, self.data)
        self.T10Y2Y=self.I(T10Y2Y,dfT10Y2Y['T10Y2Y'])
        
    def next(self):
        # if crossover(97,self.data.Close):
        #     self.buy()
        # 獲取過去3年的最高價
        self.lowest_T10Y2Y = self.T10Y2Y[-150:].min()
        if (0>self.lowest_T10Y2Y):

            ## 賣出清倉條件

            # 定義一個用於存儲最高價的 Series
            self.high_prices = self.data['High']

            # 獲取過去 100 天的最高價
            self.highest_price = self.high_prices[-20:].max()

            # 獲取當前價格
            self.current_price =self.data['Low'][-1]


            # 如果當前價格比最高價下跌 x% 或更多、破區間新低，則清倉
            # if current_price <= 0.9 * highest_price and self.position.is_long :
            #     self.position.close()

            # 定義一個用於存儲最低價的 Series
            self.low_price = self.data['Low']
            if (len(self.low_price)>25):
                # 獲取過去兩區間的最低價
                lowest_prices = self.low_price[-25:].min()
                lowest_prices2 = self.low_price[-50:-25].min()

                # 如果最近一區間跌破上一區間最低價，清倉
                if(lowest_prices<=lowest_prices2) and self.position.is_long:
                    self.position.close()



        ## 買進條件
        
        # 定義一個用於存儲最低價的 Series
        self.low_price = self.data['Low']
        if (len(self.low_price)>25):
            # 獲取過去兩區間的最低價
            self.lowest_prices = self.low_price[-25:].min()
            self.lowest_prices2 = self.low_price[-50:-25].min()
            # 如果最近一區間內價格都不跌破上一區間最低價，買進
            if(self.lowest_prices>=self.lowest_prices2):
                self.buy()

        # 如果 12ma的近20個值不再下跌，買
        # if  (self.ema1[-1]/self.ema1[-4]>=1) and not self.position: 
        #     self.buy()


bt = Backtest(df, MAStra, cash=10000, commission=.0)  # 交易成本 0.0%
stats  = bt.run()
print(stats)
print('Buy & Hold Return [%]   ',round(stats['Buy & Hold Return [%]'], 2))
print('Return (Ann.) [%]       ',round(stats['Return (Ann.) [%]'], 2))
print('Avg. Drawdown [%]       ',round(stats['Avg. Drawdown [%]'], 2))
print('Sortino Ratio           ',round(stats['Sortino Ratio'], 2))
bt.plot()
