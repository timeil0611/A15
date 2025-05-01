import yfinance as yf

# 設定股票代碼

# 下載歷史數據
data = yf.download('AAPL', start='2024-01-01', end='2024-06-01')

# 輸出數據的前五筆記錄
print(data)