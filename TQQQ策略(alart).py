import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import resample_apply
from backtesting.test import SMA

import yfinance as yf

    
# 下載歷史數據
df = yf.download('QQQ',start='1950-05-8')

# 移除 Ticker 層級
qqq = df.copy()
qqq.columns = qqq.columns.droplevel('Ticker')

# 假設你的 DataFrame 名為 'df'，n 為要新增的天數
def add_n_days(qqq, n):
    last_row = qqq.iloc[-1].copy()  # 複製最後一行的值
    last_date = qqq.index[-1]  # 取得最後日期
    
    # 迴圈新增 n 天的資料
    for i in range(1, n + 1):
        new_date = last_date + pd.Timedelta(days=i)  # 計算新日期
        qqq.loc[new_date] = last_row  # 以新日期為索引新增一行
    
    return qqq

# 新增 n 天
n = 0
qqq = add_n_days(qqq, n)


class TQQQ(Strategy):

    def init(self):
        self.w_qqq_sma = resample_apply(
                    'W', SMA, self.data.Close, 8, plot=True)
    
    def next(self):
        # 當前qqq價格
        qqq_current_price = self.data.Close[-1]
        # 獲取過去 80 天的最高價
        qqq_highest_high = self.data.Close[-80:].max()
        
        #賣的條件
        if (
            (
            (self.data.index[-1].month==9)
            or
            ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
            or
            (qqq_current_price <= 0.88 * qqq_highest_high)
            )
            and (self.position.is_long)):
            print(f"SELL ALERT: {self.data.index[-1]}")

            self.position.close()
            
        # 買的策略
        if (
            not(
            (self.data.index[-1].month==9)
                or(
                    (self.data.index[-1].month==8)
                    and(self.data.index[-1].day==31)
                )
                or (qqq_current_price <= 0.88 * qqq_highest_high)
            )

            
            and
            (self.w_qqq_sma[-1] - self.w_qqq_sma[-2] > 0)
            and
            (not self.position)
            
        ):
            print(f"BUY ALERT: {self.data.index[-1]}")

            self.buy()


bt = Backtest(qqq, TQQQ,
              cash=10000, commission=.002,
              exclusive_orders=True,)

output = bt.run()
stats = bt.run()
print(output)
bt.plot()