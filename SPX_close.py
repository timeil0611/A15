import yfinance as yf
import pandas as pd

# --- 步驟 1: 下載 ^NDX 數據 ---
TICKER = '^SPX'
print(f"正在下載 {TICKER} 的數據...")
# 下載數據，yfinance 可能回傳單層或多層欄位
df_original = yf.download(TICKER, progress=False)

if df_original.empty:
    print("無法下載數據，程式終止。")
    exit()

print("\n下載的原始數據結構預覽：")
print(df_original.head(3))

# --- 步驟 2: 處理欄位結構，提取並重命名 ---
# 這是最關鍵的一步，確保無論 yfinance 回傳什麼格式都能正確處理

# 檢查是否為多層級欄位 (MultiIndex)
if isinstance(df_original.columns, pd.MultiIndex):
    print("\n偵測到多層級欄位，正在提取 ('Close', '^spx')...")
    # 先提取出 'Close' 這一層，結果會是一個以 Ticker 為欄位的 DataFrame
    df_temp = df_original['Close']
    # 再從中選取 '^spx' 欄位，並直接轉換為 DataFrame
    df_spx = df_temp[[TICKER]].rename(columns={TICKER: 'spx'})

# 如果是標準的單層級欄位
else:
    print("\n偵測到單層級欄位，正在提取 'Close'...")
    # 直接選取 'Close' 欄位，並用 .to_frame() 轉換為 DataFrame
    df_spx = df_original['Close'].to_frame(name='spx')


# --- 步驟 3: 驗證結果 ---
print("\n成功提取並重命名！")
print("最終 'spx' DataFrame 的結構預覽：")
print(df_spx.head())
print("\n...")
print(df_spx.tail())

# 檢查欄位名稱是否正確
print(f"\n最終的欄位名稱為: {df_spx.columns.tolist()}")
df_spx.to_csv('SPX.csv', index=True) #匯出CSV
