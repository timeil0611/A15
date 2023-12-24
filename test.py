from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import plot_heatmaps

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf

import seaborn as sns
import matplotlib.pyplot as plt

def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()


# 取得資料
df = yf.download("^GSPC", start="1990-6-7", end="2023-10-01", interval="1wk")

# 避免Open出現0值
df["Open"] = df.apply(
    lambda row: row["Close"] if row["Open"] == 0 else row["Open"], axis=1
)

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


def VSMA60(data):  # Data is going to be our OHLCV
    # 取得SMA值
    df2["SMA60"] = talib.SMA(df2["Volume"], timeperiod=60)
    return df2["SMA60"]


# MA 策略
class Sma4Cross(Strategy):
    n1 = 50
    n2 = 100
    n_enter = 20
    n_exit = 10
    
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        self.sma_enter = self.I(SMA, self.data.Close, self.n_enter)
        self.sma_exit = self.I(SMA, self.data.Close, self.n_exit)
        
    def next(self):
        
        if not self.position:
            
            # On upwards trend, if price closes above
            # "entry" MA, go long
            
            # Here, even though the operands are arrays, this
            # works by implicitly comparing the two last values
            if self.sma1 > self.sma2:
                if crossover(self.data.Close, self.sma_enter):
                    self.buy()
                    
            # On downwards trend, if price closes below
            # "entry" MA, go short
            
            else:
                if crossover(self.sma_enter, self.data.Close):
                    self.sell()
        
        # But if we already hold a position and the price
        # closes back below (above) "exit" MA, close the position
        
        else:
            if (self.position.is_long and
                crossover(self.sma_exit, self.data.Close)
                or
                self.position.is_short and
                crossover(self.data.Close, self.sma_exit)):
                
                self.position.close()


bt = Backtest(df, Sma4Cross, cash=10000, commission=0.0)  # 交易成本 0.0%
stats, heatmap = bt.optimize(
    n1=range(10, 110, 10),
    n2=range(20, 210, 20),
    n_enter=range(15, 35, 5),
    n_exit=range(10, 25, 5),
    constraint=lambda p: p.n_exit < p.n_enter < p.n1 < p.n2,
    maximize='Equity Final [$]',
    max_tries=200,
    random_state=0,
    return_heatmap=True)

print(heatmap,heatmap.sort_values().iloc[-3:])
hm = heatmap.groupby(['n1', 'n2']).mean().unstack()
print(hm)

# bt.plot()

sns.heatmap(hm[::-1], cmap='viridis')
plt.show()

plot_heatmaps(heatmap, agg='mean')


print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))


