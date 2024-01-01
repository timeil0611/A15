import ffn
import matplotlib.pyplot as plt
import pandas as pd
import yfinance

yfinance.pdr_override()

# prices = ffn.get('qqq', start='2004-01-01')

prices = pd.read_csv("qqq.csv")
tqqq_mock = pd.read_csv("tqqq_mock.csv")

prices = pd.merge(prices, tqqq_mock, on=["Date"], how="left")
prices['Date'] = pd.to_datetime(prices['Date'])
# prices = prices[prices['Date'] >= '2010-02-12']
# prices = prices[prices['Date'] <= '2007-07-24']
prices = prices.set_index("Date")
print(prices.dtypes)

# 計算
stats=prices[["qqq","tqqq_mock"]].calc_stats()
stats.display()

# 價格走勢圖
prices[["qqq","tqqq_mock"]].rebase().plot(logy=True)
plt.grid()

# 最大虧損
prices[["qqq","tqqq_mock"]].to_drawdown_series().plot()
plt.grid()

plt.show()