#TQQQ策略(九月賣出+停損+周線上揚買入)簡單版

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from backtesting.test import SMA

import pandas as pd

import talib

import yfinance as yf

def prepare_data(start_date="2020-05-12", end_date="2025-11-30"):
    """
    加載、合併並準備策略所需的所有數據。
    這個函式現在可以被其他檔案導入和使用。
    """
    print("--- [Data Prep] Preparing strategy data... ---")
    
    # 取得資料
    qqq = pd.read_csv("qqq.csv")
    tqqq_mock = pd.read_csv("TQQQ_Mock_kline.csv")
    df = tqqq_mock

    # 設定Index
    df.set_index("Date", inplace=True)
    df.set_index(pd.DatetimeIndex(df.index), inplace=True)

    # 合併資料
    qqq.set_index("Date", inplace=True)
    qqq.set_index(pd.DatetimeIndex(qqq.index), inplace=True)
    # 注意：這裡的 start="1980-01-01" 似乎是舊的，我們將其移除，
    # 因為最終的篩選由 start_date 和 end_date 決定
    df = pd.concat([df, qqq], axis=1, join='inner') # 使用 inner join 確保數據對齊

    # 篩選時間範圍
    window_df = df[(df.index >= start_date) & (df.index <= end_date)].copy()
    
    print("--- [Data Prep] Data ready. ---")
    return window_df


# MA 策略
class TQQQStra(Strategy):
    # --- 策略參數 ---
    n_sma_qqq = 8       # QQQ的日線SMA週期
    n_sma_weekly = 7    # QQQ的週線SMA週期
    n_highest_high = 80 # 最高價的回看週期
    stop_loss_pct = 88 # 止損百分比
    
    # 如果您想使用 TA-Lib 指標，也可以將它們的參數放在這裡
    talib_sma_period = 60
    talib_ema_period = 60 # 注意：您的舊函式 EMA30 用的是 60
    talib_wma_period = 30
    talib_vsma_period = 60

    def init(self):
        # --- 使用 backtesting.py 的內建 SMA ---
        self.qqq_sma = self.I(SMA, self.data.qqq, self.n_sma_qqq)
        # --- 使用 lambda 函式定義滾動最高價 ---
        self.qqq_highest_high = self.I(lambda x: pd.Series(x).rolling(self.n_highest_high).max(), self.data.qqq)
        # --- 使用 resample_apply 定義週線指標 ---
        self.w_qqq_sma = resample_apply('W-FRI', SMA, self.data.qqq, self.n_sma_weekly)
        # --- 直接使用 self.I 和 TA-Lib 函式 ---
        # 這是正確且高效的方式來整合 TA-Lib
        # backtesting.py 會自動處理數據格式 (傳遞 np.array)
        self.sma60 = self.I(talib.SMA, self.data.Close, self.talib_sma_period)
        self.ema60 = self.I(talib.EMA, self.data.Close, self.talib_ema_period)
        self.wma30 = self.I(talib.WMA, self.data.Close, self.talib_wma_period)
        self.vsma60 = self.I(talib.SMA, self.data.Volume, self.talib_vsma_period)

    def next(self):
        # 當前qqq價格
        qqq_current_price = self.data["qqq"][-1]
        # 定義一個用於存儲最高價的 Series
        self.qqq_high_prices = self.data["qqq"]
        # print(self.qqq_high_prices)
        # 獲取過去 80 天的最高價
        qqq_highest_high = self.qqq_high_prices[-80:].max()

        # 獲取當前Tqqq價格
        current_price = self.data["Low"][-1]
        # 定義一個用於存儲最高價的 Series
        self.high_prices = self.data["High"]
        # 獲取過去 80 天的最高價
        highest_high = self.high_prices[-80:].max()
        # 賣的策略
        if (
            (
            (self.data.index[-1].month==9)
            or
            ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
            or
            (qqq_current_price <= self.stop_loss_pct/100 * qqq_highest_high)
            )
            and (self.position.is_long)):
            # print(f"SELL ALERT: {self.data.index[-1]} - Closing position due to sell condition.")
            self.position.close()
        # 買的策略
        if (
            not(
            (self.data.index[-1].month==9)
                or(
                    (self.data.index[-1].month==8)
                    and(self.data.index[-1].day==31)
                )
                or (qqq_current_price <= self.stop_loss_pct/100 * qqq_highest_high)
            )
            and
            (self.w_qqq_sma[-1] - self.w_qqq_sma[-2] > 0)
            and
            (not self.position)
        ):
            # print(f"BUY ALERT: {self.data.index[-1]} - Initiating buy due to buy condition.")
            self.buy()
            # print(self.data.index[-1],"buy",self.data.Close[-1])


if __name__ == "__main__":

    window_df=prepare_data()
    bt = Backtest(window_df, TQQQStra, cash=10000000, commission=0.0002,exclusive_orders=True)  # 交易成本 0.0%
    stats = bt.run()

    print(stats)
    print("Buy & Hold Return [%]   ", round(stats["Buy & Hold Return [%]"], 2))
    print("Return [%]              ", round(stats["Return [%]"], 2))
    print("Return (Ann.) [%]       ", round(stats["Return (Ann.) [%]"], 2))
    print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
    print("Max. Drawdown [%]       ", round(stats["Max. Drawdown [%]"], 2))
    # print("Avg. Drawdown [%]       ", round(stats["Avg. Drawdown [%]"], 2))
    print("Sortino Ratio           ", round(stats["Sortino Ratio"], 2))
    print("Win Rate [%]            ", round(stats["Win Rate [%]"], 2))
    if(round(stats["Buy & Hold Return [%]"], 2)-round(stats["Return [%]"], 2))>0:
        print("Lose Buy & Hold Return",round(stats["Buy & Hold Return [%]"], 2)-round(stats["Return [%]"], 2), "%")

    print("\n")


    bt.plot()