import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 參數設定 (來自程式碼2的嚴謹設定) ---
TICKER_UNDERLYING = '^NDX'
TICKER_LEVERAGED = 'TQQQ'
LEVERAGE_FACTOR = 3.0
EXPENSE_RATIO = 0.0086
TRACKING_ERROR_STD = 0.001 # 引入追蹤誤差
SIMULATION_START_DATE = '1985-01-01'

# --- 步驟 1 & 2: 下載數據、使用程式碼2的向量化方法計算回報率 ---
print(f"正在下載 {TICKER_UNDERLYING} 的數據...")
# yfinance 可能會回傳單層或多層欄位，我們需要處理這種不確定性
df_multi = yf.download(TICKER_UNDERLYING, start=SIMULATION_START_DATE, progress=False)

if df_multi.empty:
    print("無法下載NDX數據，程式終止。")
    exit()

# ---  簡化 DataFrame 結構 ---
# 檢查回傳的欄位是否為多層級
if isinstance(df_multi.columns, pd.MultiIndex):
    print("偵測到多層級欄位 (MultiIndex)，正在進行簡化...")
    # 將欄位名稱從 ('Close', '^NDX') 簡化為 'Close'
    df_base = df_multi.droplevel(1, axis=1) 
else:
    print("偵測到單層級欄位，直接使用。")
    df_base = df_multi

print(df_base.head()) # 可以取消這行的註解來確認結構

df_base['base_return'] = df_base['Close'].pct_change()
df_base.dropna(subset=['base_return'], inplace=True) # 移除第一個NaN

# --- 步驟 3: 使用程式碼2的嚴謹模型模擬回報率 ---
daily_expense = EXPENSE_RATIO / 252.0 # 將年化費用率轉換為每日費用，因為交易是每天發生的
np.random.seed(42) # 確保隨機結果可重現
tracking_errors = np.random.normal(0, TRACKING_ERROR_STD, size=len(df_base))# 生成一組符合常態分佈的隨機數(平均=0)，模擬ETF每天無法完美追蹤指數的微小誤差
tracking_errors = pd.Series(tracking_errors, index=df_base.index) # 將這組隨機數轉換為Pandas Series，並將其索引與我們的日期對齊，確保不會出錯
# 核心公式：計算模擬的每日回報率
df_base['sim_return'] = (df_base['base_return'] * LEVERAGE_FACTOR) - daily_expense + tracking_errors


# --- 步驟 4: 使用程式碼2的方法還原淨值 ---
df_base['sim_price'] = (1 + df_base['sim_return']).cumprod()

# --- 步驟 5: 使用程式碼1的拼接邏輯來創造最終序列 ---
print(f"正在下載真實 {TICKER_LEVERAGED} 數據用於拼接...")
df_real_tqqq = yf.download(TICKER_LEVERAGED, start=SIMULATION_START_DATE, progress=False)

if not df_real_tqqq.empty:
    real_start_date = df_real_tqqq.index.min()# 找到真實數據開始的日期
    
    # 切割出模擬部分 (真實數據開始前)
    df_simulated_part = df_base.loc[df_base.index < real_start_date]
    
    # 計算縮放因子
    last_sim_price = df_simulated_part.iloc[-1]['sim_price'] # 1. 取得模擬歷史的「最後一天」價格 (例如 55.2)
    first_real_price = df_real_tqqq.iloc[0]['Close'] # 2. 取得真實歷史的「第一天」價格 (例如 21.8)
    scaling_factor = last_sim_price / first_real_price # 3. 計算縮放比例 (55.2 / 21.8 = 2.53)
    
    df_real_tqqq['scaled_price'] = df_real_tqqq['Close'] * scaling_factor # 將整個「真實歷史」的價格，都乘以這個縮放比例(平移)
    print(df_simulated_part)
    print(df_real_tqqq)
    # 拼接
    final_series = pd.concat([
        df_simulated_part['sim_price'],
        df_real_tqqq['scaled_price']
    ])
    
    df_final = final_series.to_frame(name='TQQQ_Backfilled')
    print("數據拼接完成！")

else:
    df_final = df_base[['sim_price']].rename(columns={'sim_price': 'TQQQ_Backfilled'})
    print("無法下載真實TQQQ數據，僅使用模擬數據。")


# --- 結果展示 ---
print("\n最終回溯構建的 TQQQ 數據預覽：")
print(df_final.head())
print("\n...")
print(df_final.tail())

# 繪製圖表以供驗證
df_final['TQQQ_Backfilled'].plot(figsize=(14, 7), logy=True, title='Backfilled TQQQ Price (Log Scale)')
plt.ylabel('Price (Log Scale)')
plt.xlabel('Date')
plt.grid(True, which="both")
plt.show()