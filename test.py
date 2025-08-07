import pandas as pd
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# --- 步驟 1: 準備數據 (下載日線並轉換為週線) ---

# 下載 TQQQ 的日線數據
# 我們需要下載比回測週期更長的數據，以確保移動視窗計算的準確性
print("正在下載 TQQQ 日線數據...")
df_multi = yf.download('TQQQ', start='2010-01-01', progress=False)

# ---  簡化 DataFrame 結構 ---
# 檢查回傳的欄位是否為多層級
if isinstance(df_multi.columns, pd.MultiIndex):
    print("偵測到多層級欄位 (MultiIndex)，正在進行簡化...")
    # 將欄位名稱從 ('Close', '^NDX') 簡化為 'Close'
    data_daily = df_multi.droplevel(1, axis=1) 
else:
    print("偵測到單層級欄位，直接使用。")
    data_daily = df_multi

# 將日線數據重サンプリング (Resample) 為週線數據
# 'W-FRI' 表示以每週的星期五作為該週的結束點
print("將日線數據轉換為週線數據...")
resample_rules = {
    'Open': 'first',  # 週開盤價 = 該週第一天的開盤價
    'High': 'max',    # 週最高價 = 該週所有天中的最高價
    'Low': 'min',     # 週最低價 = 該週所有天中的最低價
    'Close': 'last',   # 週收盤價 = 該週最後一天的收盤價
    'Volume': 'sum'    # 週成交量 = 該週所有天的成交量總和
}
data_weekly = data_daily.resample('W-FRI').agg(resample_rules)

# 移除可能因重サンプリング產生的空值行
data_weekly.dropna(inplace=True)

print("週線數據準備完成：")
print(data_weekly.tail())


# --- 步驟 2: 定義策略 (帶有重置機制的版本) ---

class AdaptivePlatformStrategy(Strategy):
    # 平台觀察期
    N = 10
    # 平台失效後的重置/冷卻期 (單位：週)
    # 這個時間必須小於 N，才有意義
    reset_period = 5

    def init(self):
        # 平台指標定義不變
        self.upper_band = self.I(lambda x: pd.Series(x).rolling(self.N).max(), self.data.High)
        self.lower_band = self.I(lambda x: pd.Series(x).rolling(self.N).min(), self.data.Low)

        # 初始化狀態變數
        self.in_cooldown = False
        self.cooldown_counter = 0

    def next(self):
        # --- 狀態管理：處理冷卻期 ---
        if self.in_cooldown:
            self.cooldown_counter -= 1
            if self.cooldown_counter <= 0:
                self.in_cooldown = False
                print(f"{self.data.index[-1].date()}: 冷卻期結束，策略重新啟動。")
            else:
                # 在冷卻期內，不做任何交易決策
                return

        price = self.data.Close[-1]

        # --- 賣出邏輯 ---
        if self.position.is_long and price < self.lower_band[-2]:
            print(f"{self.data.index[-1].date()}: 價格 {price:.2f} 跌破舊平台 {self.lower_band[-2]:.2f}，賣出。")
            self.position.close()
            # 觸發冷卻期！
            print(f"--- 觸發 {self.reset_period} 週的冷卻期 ---")
            self.in_cooldown = True
            self.cooldown_counter = self.reset_period

        # --- 買入邏輯 ---
        elif not self.position and price > self.upper_band[-2]:
            print(f"{self.data.index[-1].date()}: 價格 {price:.2f} 突破平台 {self.upper_band[-2]:.2f}，買入。")
            self.buy()
            # 向上突破也代表舊平台結束，但不立即觸發冷卻，因為我們希望跟隨趨勢
            # 冷卻只在趨勢失敗（跌破）時觸發，讓我們尋找下一個底部平台


# --- 步驟 3: 執行回測 ---

print("\n開始執行回測...")
bt = Backtest(
    data_weekly,              # 使用我們準備好的週線數據
    AdaptivePlatformStrategy, # 使用我們定義的策略
    cash=100000,              # 初始資金
    commission=.002           # 手續費 (0.2%)
)

# 執行回測，並可以傳入策略參數進行測試
stats = bt.run(N=20) # 您可以改變 N 的值，例如 bt.run(N=52)

print("\n回測結果統計：")
print(stats)

# 繪製回測結果圖表
# 圖表會自動包含買賣點、權益曲線，以及我們自定義的平台上下軌！
print("\n正在生成回測圖表...")
bt.plot()