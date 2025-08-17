import pandas as pd
import numpy as np
import yfinance as yf

# 1. 選擇股票池和時間範圍
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN'] # 範例股票池
start_date = '2015-01-01'
end_date = '2024-12-31'

# 2. 下載基礎數據
# yfinance 會返回一個多層索引的 DataFrame
data = yf.download(tickers, start=start_date, end=end_date)

# 3. 創建特徵 (Features)
# 我們需要將數據從寬格式轉換為長格式，以便處理
# 每一行是 "一個股票在一天" 的數據
df = data.stack().reset_index()
df = df.rename(columns={'level_1': 'Ticker', 'Date': 'date', 'Close': 'adj_close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'})

# --- 開始創建特徵 ---
# 特徵1：動能 (Momentum) - 過去 N 個月的滾動回報率
# .pct_change(N) 計算 N 天的回報率。21約為一個月，63約為一季
df['return_1m'] = df.groupby('Ticker')['adj_close'].pct_change(21)
df['return_3m'] = df.groupby('Ticker')['adj_close'].pct_change(63)
df['return_6m'] = df.groupby('Ticker')['adj_close'].pct_change(126)

# 特徵2：波動率 (Volatility) - 過去 N 個月的滾動波動率
df['volatility_1m'] = df.groupby('Ticker')['return_1m'].transform(lambda x: x.rolling(21).std())

# 特徵3：移動平均線交叉 (Moving Average Cross)
df['ma_20'] = df.groupby('Ticker')['adj_close'].transform(lambda x: x.rolling(20).mean())
df['ma_60'] = df.groupby('Ticker')['adj_close'].transform(lambda x: x.rolling(60).mean())
df['ma_signal'] = np.where(df['ma_20'] > df['ma_60'], 1, -1)

# ... 在這裡您可以盡情發揮創意，加入數十甚至數百個特徵 ...

# 最終，我們得到一個巨大的特徵數據庫
features_df = df[['date', 'Ticker', 'return_1m', 'return_3m', 'volatility_1m', 'ma_signal']]
print("特徵數據庫預覽:")
print(features_df.tail())

# 我們的目標是預測未來一個月 (21個交易日) 的回報率
df['target_return'] = df.groupby('Ticker')['adj_close'].transform(lambda x: x.shift(-21) / x - 1)

# 將特徵和目標合併
final_df = pd.merge(features_df, df[['date', 'Ticker', 'target_return']], on=['date', 'Ticker'])

# 處理數據中的缺失值 (NaN)，這是特徵工程初期會產生的
final_df = final_df.dropna()

# 定義分割點
split_date = '2023-01-01'

# 分割數據
train_df = final_df[final_df['date'] < split_date]
test_df = final_df[final_df['date'] >= split_date]

# 定義模型的輸入 (X) 和輸出 (y)
features = ['return_1m', 'return_3m', 'volatility_1m', 'ma_signal']
X_train = train_df[features]
y_train = train_df['target_return']

X_test = test_df[features]
y_test = test_df['target_return']

print(f"訓練數據筆數: {len(X_train)}")
print(f"測試數據筆數: {len(X_test)}")


from sklearn.ensemble import RandomForestRegressor

# 1. 選擇並初始化模型
# RandomForestRegressor 是一個強大且常用的樹模型
# n_estimators 是決策樹的數量，random_state 確保結果可重現
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

# 2. 訓練模型
print("開始訓練模型...")
model.fit(X_train, y_train)
print("模型訓練完成！")


# 1. 在測試集上進行預測
test_df['predicted_return'] = model.predict(X_test)

# 2. 形成一個簡單的多空策略 (Long-Short Strategy)
# 在每個交易日，我們根據預測的回報率對股票進行排名
# 做多 (Long) 預測回報率最高的股票
# 做空 (Short) 預測回報率最低的股票

daily_returns = []
# 遍歷測試集中的每一個交易日
for date, group in test_df.groupby('date'):
    # 按預測回報率降序排序
    sorted_group = group.sort_values('predicted_return', ascending=False)
    
    # 做多排名第一的股票 (獲取其真實的未來回報)
    long_return = sorted_group.iloc[0]['target_return']
    
    # 做空排名最後的股票 (獲取其真實的未來回報的負值)
    # short_return = -sorted_group.iloc[-1]['target_return']
    
    # 假設等權重，當日策略回報為兩者平均
    strategy_return = long_return
    # strategy_return = (long_return + short_return) / 2
    daily_returns.append(strategy_return)

# 3. 計算並可視化策略的累積回報 (權益曲線)
strategy_returns_df = pd.DataFrame({
    'date': test_df['date'].unique(),
    'strategy_return': daily_returns
})
strategy_returns_df['cumulative_return'] = (1 + strategy_returns_df['strategy_return']).cumprod()

print("策略在樣本外的表現:")
print(strategy_returns_df.tail())

# 繪圖
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(strategy_returns_df['date'], strategy_returns_df['cumulative_return'])
plt.title('Machine Learning Strategy - Out-of-Sample Performance')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.grid(True)
plt.show()

# 查看特徵重要性
feature_importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("\n特徵重要性排名:")
print(feature_importances)