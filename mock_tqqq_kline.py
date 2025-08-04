import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf # 導入金融繪圖庫
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- 參數設定 ---
TICKER_UNDERLYING = '^NDX'
TICKER_LEVERAGED = 'TQQQ'
LEVERAGE_FACTOR = 3.0
EXPENSE_RATIO = 0.0086
SIMULATION_START_DATE = '1985-01-01'

# --- 步驟 1: 下載包含 OHLCV 的基礎數據 ---
print(f"正在下載 {TICKER_UNDERLYING} 的完整 OHLCV 數據...")
df_multi = yf.download(TICKER_UNDERLYING, start=SIMULATION_START_DATE, progress=False)

if df_multi.empty:
    print("無法下載NDX數據，程式終止。")
    exit()

# --- 步驟 2: 簡化 DataFrame 結構 ---
if isinstance(df_multi.columns, pd.MultiIndex):
    df_ndx = df_multi.droplevel(1, axis=1)
else:
    df_ndx = df_multi

# --- 步驟 3: 計算模擬的 Close (最可靠的部分) ---
# 這是我們回測的「錨」，確保長期回報的準確性
df_ndx['ndx_return'] = df_ndx['Close'].pct_change()
daily_expense = EXPENSE_RATIO / 252.0
df_ndx.dropna(subset=['ndx_return'], inplace=True) # 清理第一個NaN

# 為了簡化，我們暫不考慮追蹤誤差，專注於OHLC的結構
df_ndx['sim_return'] = (df_ndx['ndx_return'] * LEVERAGE_FACTOR) - daily_expense
df_ndx['Sim_Close'] = (1 + df_ndx['sim_return']).cumprod() * 100 # 假設從100開始

# --- 步驟 4: 模擬 Open, High, Low ---
print("開始模擬 TQQQ 的 OHLC...")

# 創建新的DataFrame來存放模擬的OHLCV
df_sim_tqqq = pd.DataFrame(index=df_ndx.index)

# 4.1 模擬 Open
# 計算NDX的隔夜回報率
ndx_overnight_return = (df_ndx['Open'] / df_ndx['Close'].shift(1)) - 1
# 模擬TQQQ的隔夜回報率
tqqq_overnight_return = ndx_overnight_return * LEVERAGE_FACTOR
# 模擬TQQQ的開盤價 = 前一天的模擬收盤價 * (1 + 模擬的隔夜回報)
df_sim_tqqq['Sim_Open'] = df_ndx['Sim_Close'].shift(1) * (1 + tqqq_overnight_return)

# 4.2 模擬 High 和 Low (以開盤價為基準)
# 計算NDX從開盤到最高/最低點的日內回報率
ndx_intraday_high_return = (df_ndx['High'] / df_ndx['Open']) - 1
ndx_intraday_low_return = (df_ndx['Low'] / df_ndx['Open']) - 1

# 模擬TQQQ的日內高低點回報率
tqqq_intraday_high_return = ndx_intraday_high_return * LEVERAGE_FACTOR
tqqq_intraday_low_return = ndx_intraday_low_return * LEVERAGE_FACTOR

# 模擬TQQQ的最高/最低價
df_sim_tqqq['Sim_High'] = df_sim_tqqq['Sim_Open'] * (1 + tqqq_intraday_high_return)
df_sim_tqqq['Sim_Low'] = df_sim_tqqq['Sim_Open'] * (1 + tqqq_intraday_low_return)

# 4.3 填入並校準 Close
# 將我們在步驟3中計算出的、最可靠的Close值填入
df_sim_tqqq['Sim_Close'] = df_ndx['Sim_Close']

# 處理第一天的 NaN 值
df_sim_tqqq.iloc[0] = df_sim_tqqq.iloc[1] # 用第二天的数据简单填充第一天空值
df_sim_tqqq.iloc[0, df_sim_tqqq.columns.get_loc('Sim_Open')] = df_ndx.iloc[0]['Sim_Close'] # 讓第一天開盤=收盤

# 確保 High 是最高的，Low 是最低的
df_sim_tqqq['Sim_High'] = df_sim_tqqq[['Sim_Open', 'Sim_Close', 'Sim_High']].max(axis=1)
df_sim_tqqq['Sim_Low'] = df_sim_tqqq[['Sim_Open', 'Sim_Close', 'Sim_Low']].min(axis=1)


# --- 步驟 5: 模擬 Volume (最具推測性的部分) ---
print("開始模擬 TQQQ 的 Volume...")
# 下載真實數據以計算成交量比例
df_real_tqqq = yf.download(TICKER_LEVERAGED, start=SIMULATION_START_DATE, progress=False)
if not df_real_tqqq.empty:
    # 合併真實TQQQ和NDX數據，以計算重疊期間的成交量比例
    df_merged = pd.concat([df_real_tqqq['Volume'], df_ndx['Volume']], axis=1, join='inner')
    df_merged.columns = ['TQQQ_Volume', 'NDX_Volume']
    
    # 計算平均成交量比例 (忽略極端值可能有助於穩定性)
    avg_volume_ratio = (df_merged['TQQQ_Volume'] / df_merged['NDX_Volume']).median()
    print(f"計算出的成交量中位數比例 (TQQQ/NDX): {avg_volume_ratio:.4f}")

    # 使用這個比例來模擬歷史成交量
    df_sim_tqqq['Sim_Volume'] = (df_ndx['Volume'] * avg_volume_ratio).round()
else:
    # 如果無法下載真實數據，則無法模擬成交量
    df_sim_tqqq['Sim_Volume'] = 0
    print("無法下載真實TQQQ數據，成交量模擬失敗。")


# --- 步驟 6: 拼接真實數據 (可選，但推薦) ---
# 這部分邏輯與之前類似，但現在我們要拼接整個OHLCV數據塊
# 這裡為了簡化，我們先只展示模擬的結果

# 重新排列欄位順序
df_sim_tqqq = df_sim_tqqq[['Sim_Open', 'Sim_High', 'Sim_Low', 'Sim_Close', 'Sim_Volume']]
ordered_columns = ['Sim_Open', 'Sim_High', 'Sim_Low', 'Sim_Close', 'Sim_Volume']# 1. 定義要選取和排序的欄位
new_names = ['Open', 'High', 'Low', 'Close', 'Volume']# 2. 定義新的欄位名稱列表 (順序必須與上面完全對應)
df_sim_tqqq = df_sim_tqqq[ordered_columns].copy() # 3. 選取出子 DataFrame 使用 .copy() 避免 SettingWithCopyWarning
df_sim_tqqq.columns = new_names# 4. 直接將新名字列表賦值給 .columns

# --- 結果展示 ---
print("\n模擬完成的 TQQQ OHLCV 數據預覽：")
print(df_sim_tqqq.head())
print("\n...")
print(df_sim_tqqq.tail())
df_sim_tqqq.to_csv('TQQQ_Mock_kline.csv', index=True)

# 檢查是否有任何空值
print(f"\n數據中是否存在任何空值: {df_sim_tqqq.isnull().values.any()}")

# --- 步驟 7: 數據可視化 ---
print("\n開始繪製圖表...")

# 圖 1: 長期收盤價走勢圖 (Matplotlib)
print("正在繪製長期收盤價走勢圖 (對數座標)...")
plt.style.use('seaborn-v0_8-whitegrid') # 使用一個好看的樣式
plt.figure(figsize=(14, 7))
df_sim_tqqq['Close'].plot(logy=True, color='blue')
plt.title('Simulated TQQQ Close Price Since 1985 (Log Scale)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Simulated Price (Log Scale)', fontsize=12)
plt.grid(True, which="both", linestyle='--')
plt.legend(['Simulated TQQQ Close'])
plt.show()


# 圖 2:  K 線圖 (Plotly)
print("正在繪製的 K 線圖...")
# 選取數據來繪圖
df_plot = df_sim_tqqq.tail(25200)

fig = go.Figure(data=[go.Candlestick(x=df_plot.index,
                open=df_plot['Open'],
                high=df_plot['High'],
                low=df_plot['Low'],
                close=df_plot['Close'],
                name='Simulated TQQQ')])

fig.update_layout(
    title={
        'text': 'Simulated TQQQ Candlestick Chart (on Log Scale)',
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    xaxis_title='Date',
    yaxis_title='Simulated Price (Log Scale)',
    yaxis_type="log",
    xaxis_rangeslider_visible=True, # 隱藏下方的範圍滑桿，讓圖表更簡潔
    template='plotly_white' # 使用簡潔的白色模板
)
# 顯示圖表
# fig.show()

# 如果您想保存為 HTML 檔案
fig.write_html("tqqq_full_history_log_chart.html")

