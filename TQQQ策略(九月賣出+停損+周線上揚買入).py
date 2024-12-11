from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply

from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt
import plotly.express as px

import yfinance as yf

from datetime import datetime





start = "1980-01-01"

# 取得資料
qqq = pd.read_csv("qqq_19830810.csv")
tqqq_mock = pd.read_csv("TQQQ_Mock_kline _19830810.csv")
df=tqqq_mock

# 設定Index
df.set_index("Date", inplace=True)
df.set_index(pd.DatetimeIndex(df.index), inplace=True)

#合併資料
qqq.set_index("Date", inplace=True)
qqq.set_index(pd.DatetimeIndex(qqq.index), inplace=True)
qqq = qqq[start:]
df = pd.concat([df, qqq], axis=1)

i=1
k=1

# 為了畫圖
years = list(range(1993, 2024)) # range中。第一個要與end_date年份相同，第二個要與final_date年份+1相同
str_result = []
b_h_result= []

# 不同windows
start_date = "1983-08-10"
end_date = "1993-08-10"
final_date = "2023-10-20"
rolling_years= int(end_date.split("-")[0])-int(start_date.split("-")[0])

while pd.to_datetime(end_date) <= pd.to_datetime(final_date):
    # 篩選時間範圍
    window_df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    # backtesting.py
    # ta-lib 格式
    df2 = window_df.rename(
        columns={
            "High": "high",
            "Low": "low",
        }
    )

    

    def QQQ(data):  # Data is going to be our OHLCV
        # 取得qqq值
        return data

    def SMA(values, n):
        """
        Return simple moving average of `values`, at
        each step taking into account `n` previous values.
        """
        return pd.Series(values).rolling(n).mean()
    
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
    class TQQQStra(Strategy):
        n1 = 10
        cooldown_days = 4

        def init(self):
            self.qqq_sma1 = self.I(SMA, self.data.qqq, self.n1)
            self.sma1 = self.I(SMA, self.data.Close, self.n1)
            # self.Vsma1 = self.I(SMA, self.data.Volume, self.n1)
            # self.ema1 = self.I(EMA30, self.data)
            self.qqq = self.I(QQQ, window_df["qqq"])
            self.cooldown_weeks = 6
            self.last_trade_date = pd.to_datetime("1981-07-31")  # 設定初值
            # 周範圍
            self.w_qqq_sma = resample_apply(
                        'W', SMA, self.data.qqq, 6, plot=True)
        def next(self): # buy ,close 要互斥
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




            if (
                (
                (self.data.index[-1].month==9)
                or
                ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
                or
                (qqq_current_price <= 0.88 * qqq_highest_high)
                )
                and 
                (self.position.is_long)
            ):
                self.position.close()

            # 如果 60ma的近20個值不再下跌，買
            if (
                not
                (
                (self.data.index[-1].month==9)
                or
                ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
                or
                (qqq_current_price <= 0.88 * qqq_highest_high)
                )

                
                and
                (self.w_qqq_sma[-1] - self.w_qqq_sma[-2] > 0)
                and
                (not self.position)
                
            ):
                self.buy()
                # print(self.data.index[-1],"buy",self.data.Close[-1])
                
    # start_date 和 end_date 加一年
    start_date = (pd.to_datetime(start_date) + pd.DateOffset(years=1)).strftime("%Y-%m-%d")
    end_date = (pd.to_datetime(end_date) + pd.DateOffset(years=1)).strftime("%Y-%m-%d")
    print(window_df.index[0],"-",window_df.index[-1])
            



    bt = Backtest(window_df, TQQQStra, cash=10000, commission=0.0002,exclusive_orders=True)  # 交易成本 0.0%
    stats = bt.run()

    # print(stats)
    print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
    print("Return [%]              ", round(stats["Return [%]"], 2))
    print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
    print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
    print("Max. Drawdown [%]       ", round(stats["Max. Drawdown [%]"], 2))
    # print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
    print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))
    print("Win Rate [%]            ", round(stats["Win Rate [%]"], 2))
    # 策略贏B&H次數計算
    if(round(stats["Buy & Hold Return [%]"], 2)-round(stats["Return [%]"], 2))>0:
        print("Lose ",round(stats["Buy & Hold Return [%]"], 2)-round(stats["Return [%]"], 2), "%")
        i+=1
    k+=1
    
    #畫return跟B_H的圖
    str_result.append(round(stats["Return [%]"], 2))
    b_h_result.append( round(stats["Buy & Hold Return [%]"], 2))
    
    print("\n")


    # bt.plot(resample='1W')
print("lose times",i)
print("total ",k)

# 百份位數統計表
def quantile(str_result,b_h_result):
    df = pd.DataFrame({"str_result": str_result,"B&H_result":b_h_result})
    
        # 計算百分位數、最大值、最小值、平均值
    summary = {
        "Return [%]": ["Min", "25th Percentile", "50th Percentile (Median)", "75th Percentile", "Max", "Mean"],
        "B&H_result": [
            df["B&H_result"].min(),
            df["B&H_result"].quantile(0.25),
            df["B&H_result"].median(),
            df["B&H_result"].quantile(0.75),
            df["B&H_result"].max(),
            df["B&H_result"].mean(),
        ],
        "str_result": [
            df["str_result"].min(),
            df["str_result"].quantile(0.25),
            df["str_result"].median(),
            df["str_result"].quantile(0.75),
            df["str_result"].max(),
            df["str_result"].mean(),
        ],
    }

    summary_df = pd.DataFrame(summary)

    print(summary_df)

def plot(years,str_result,b_h_result):
    # 創建DataFrame
    df = pd.DataFrame({"Year": years, "str_result": str_result,"B&H_result":b_h_result})

    # 繪製折線
    fig = px.line(df, x="Year", y=["str_result", "B&H_result"], 
              labels={"value": "return [%]", "variable": "strategy"},
              title=f"滾動 {rolling_years} 年最終報酬",# 使用 f-string
              )
    
    # 啟用十字軸游標
    fig.update_layout(hovermode="x",  # 十字軸的模式
        xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1),
        yaxis=dict(showspikes=True, spikethickness=1),
        )

    fig.show()
    
quantile(str_result,b_h_result)    
plot(years,str_result,b_h_result)