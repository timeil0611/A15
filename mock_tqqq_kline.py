import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf # 引入K線圖繪製庫

# --- 參數設定 ---
TICKER_UNDERLYING = '^NDX'
TICKER_LEVERAGED = 'TQQQ'
LEVERAGE_FACTOR = 3.0
EXPENSE_RATIO = 0.0086
SIMULATION_START_DATE = '1985-01-01'

# --- 步驟 1 & 2: 下載並簡化NDX數據 ---
print("正在下載 NDX 的完整 OHLCV 數據...")
df_multi = yf.download(TICKER_UNDERLYING, start=SIMULATION_START_DATE, progress=False)
if df_multi.empty:
    print("無法下載NDX數據，程式終止。")
    exit()
df_ndx = df_multi.droplevel(1, axis=1) if isinstance(df_multi.columns, pd.MultiIndex) else df_multi

# --- 步驟 3: 模擬 Close (作為錨點) ---
df_ndx['ndx_return'] = df_ndx['Close'].pct_change()
daily_expense = EXPENSE_RATIO / 252.0
df_ndx.dropna(subset=['ndx_return'], inplace=True)
df_ndx['sim_return'] = (df_ndx['ndx_return'] * LEVERAGE_FACTOR) - daily_expense
# 使用 Close 作為拼接基準，所以這裡也用 Close 來計算模擬價格
df_ndx['Sim_Adj_Close'] = (1 + df_ndx['sim_return']).cumprod() * 100

# --- 步驟 4: 模擬 Open, High, Low ---
print("正在模擬 TQQQ 的 OHLC...")
df_sim_tqqq = pd.DataFrame(index=df_ndx.index)
ndx_overnight_return = (df_ndx['Open'] / df_ndx['Close'].shift(1)) - 1
tqqq_overnight_return = ndx_overnight_return * LEVERAGE_FACTOR
df_sim_tqqq['Open'] = df_ndx['Sim_Adj_Close'].shift(1) * (1 + tqqq_overnight_return)
ndx_intraday_high_return = (df_ndx['High'] / df_ndx['Open']) - 1
ndx_intraday_low_return = (df_ndx['Low'] / df_ndx['Open']) - 1
df_sim_tqqq['High'] = df_sim_tqqq['Open'] * (1 + (ndx_intraday_high_return * LEVERAGE_FACTOR))
df_sim_tqqq['Low'] = df_sim_tqqq['Open'] * (1 + (ndx_intraday_low_return * LEVERAGE_FACTOR))
# 注意：這裡的 Close 只是臨時的，最終會被 Close 替代用於拼接
df_sim_tqqq['Close'] = df_ndx['Sim_Adj_Close'] 
df_sim_tqqq.iloc[0] = df_ndx.iloc[0]['Sim_Adj_Close'] # 簡單填充第一天空值
df_sim_tqqq['High'] = df_sim_tqqq[['Open', 'Close', 'High']].max(axis=1)
df_sim_tqqq['Low'] = df_sim_tqqq[['Open', 'Close', 'Low']].min(axis=1)

# --- 步驟 5: 模擬 Volume ---
print("正在模擬 TQQQ 的 Volume...")
df_multi_TQQQ = yf.download(TICKER_LEVERAGED, start=SIMULATION_START_DATE, progress=False)
df_real_tqqq_full = df_multi_TQQQ.droplevel(1, axis=1) if isinstance(df_multi_TQQQ.columns, pd.MultiIndex) else df_multi_TQQQ
if not df_real_tqqq_full.empty:
    df_merged = pd.concat([df_real_tqqq_full['Volume'], df_ndx['Volume']], axis=1, join='inner')
    avg_volume_ratio = (df_merged.iloc[:, 0] / df_merged.iloc[:, 1]).median()
    df_sim_tqqq['Volume'] = (df_ndx['Volume'] * avg_volume_ratio).round()
else:
    df_sim_tqqq['Volume'] = 0

# --- 步驟 6: 拼接真實數據 (OHLCV) ---
print("正在拼接模擬與真實的 OHLCV 數據...")
if not df_real_tqqq_full.empty:
    real_start_date = df_real_tqqq_full.index.min()
    
    # 1. 切割出模擬部分
    df_simulated_part = df_sim_tqqq.loc[df_sim_tqqq.index < real_start_date]
    
    # 2. 計算縮放因子 (關鍵：使用 Close 來計算，確保回報連續性)
    last_sim_adj_close = df_simulated_part.iloc[-1]['Close'] # 模擬數據的收盤價就是模擬的Adj Close
    first_real_adj_close = df_real_tqqq_full.iloc[0]['Close']
    scaling_factor = last_sim_adj_close / first_real_adj_close
    print(f"計算出的拼接縮放因子: {scaling_factor:.4f}")
    
    # 3. 縮放真實數據的價格部分 (Open, High, Low, Close)
    df_real_part = df_real_tqqq_full.copy()
    price_cols = ['Open', 'High', 'Low', 'Close']
    for col in price_cols:
        df_real_part[col] = df_real_part[col] * scaling_factor
        
    # 4. 拼接
    # 拼接價格
    df_final_prices = pd.concat([
        df_simulated_part[['Open', 'High', 'Low', 'Close']],
        df_real_part[['Open', 'High', 'Low', 'Close']]
    ])
    # 拼接成交量
    df_final_volume = pd.concat([
        df_simulated_part['Volume'],
        df_real_part['Volume'] # 成交量不需要縮放
    ])
    
    # 5. 合併成最終的 DataFrame
    df_final = df_final_prices
    df_final['Volume'] = df_final_volume
    
    print("數據拼接完成！")
else:
    df_final = df_sim_tqqq.copy()
    print("無法下載真實TQQQ數據，僅使用模擬數據。")
    
df_final.to_csv('TQQQ_Mock_kline.csv', index=True) #匯出CSV

# --- 步驟 7: 繪製 K 線圖 ---
print("\n正在繪製拼接後的 K 線圖...")

# 為了讓圖表更清晰，我們只繪製最近幾年的數據，例如從2020年開始
# 如果想看更長的歷史，可以調整 start_date
plot_start_date = '1985-01-01'
df_plot = df_final.loc[plot_start_date:]

# 找到拼接點，並在圖上標示出來
splice_point_date = df_real_tqqq_full.index.min()
vline_to_plot = []
if splice_point_date in df_plot.index:
    vline_to_plot.append(splice_point_date)

# 設置圖表樣式和標題
chart_title = f"Backfilled TQQQ OHLCV (Spliced on {splice_point_date.date()})"
mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':')

# 繪圖
mpf.plot(df_plot, 
         type='candle', 
         style=s,
         title=chart_title,
         ylabel='Price (Scaled)',
         volume=True,
         ylabel_lower='Volume',
         vlines=dict(vlines=vline_to_plot, colors='b', linestyle='-.', linewidths=1), # 標示拼接線
         figratio=(16, 9),
         figscale=1.2,
         yscale='log',
         )

print(f"\n圖表已生成。藍色虛線標示了從模擬數據切換到真實數據的拼接點: {splice_point_date.date()}")