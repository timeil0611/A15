import ffn
import matplotlib.pyplot as plt
import pandas as pd
import yfinance

yfinance.pdr_override()

# 將FSPTX與qqq在1999-03-10前融合
FSPTX_prices = ffn.get("FSPTX", start="1999-03-10", end="1999-03-11")
qqq_prices = ffn.get("qqq", start="1999-03-10", end="1999-03-11")
tqqq = ffn.get("tqqq")


# 計算倍數
times = qqq_prices["qqq"] / FSPTX_prices["fsptx"]
times = times.to_numpy()

# 相乘
adj_FSPTX_hist_prices = ffn.get("FSPTX", end="1999-03-10")
adj_FSPTX_hist_prices = adj_FSPTX_hist_prices * times

# 更改adj_FSPTX_hist_prices列為qqq
adj_FSPTX_hist_prices.rename(columns={"fsptx": "qqq"}, inplace=True)

# 合併
qqq_hist_prices = ffn.get("qqq")
adj_qqq_prices = qqq_hist_prices.combine_first(adj_FSPTX_hist_prices)

prices = adj_qqq_prices
# prices=prices['2010-02-11':]


prices.loc[:, "qqq_shift"] = prices["qqq"].shift(1)
prices.loc[:, "qqq_diff"] = prices["qqq"].diff(1)
prices.loc[:, "qqq_diff_tqqq"] = 2.8374 * (prices["qqq_diff"] / prices["qqq_shift"]) + 1
prices.loc[:, "tqqq_mock"] = 0

prices["tqqq"]=tqqq['tqqq']

nRow = 0
while nRow < prices.shape[0]:
    if nRow == 0:
        # 初始化資料
        tqqq_mock = 1
    else:
        tqqq_mock = prices["qqq_diff_tqqq"][nRow] * tqqq_mock
    prices.iloc[nRow, prices.columns.get_loc("tqqq_mock")] = tqqq_mock
    nRow = nRow + 1

print(prices)

# prices["tqqq_mock"].to_csv("tqqq_mock.csv", index=True)

prices = pd.read_csv("QQQ,mock_TQQQ.csv")
# plt.semilogy(prices["Date"], prices[["qqq", "tqqq_mock"]])
# plt.grid()
# prices = prices.set_index("Date")
prices = prices.set_index("Date")
# 價格走勢圖
prices[["qqq",'tqqq_mock']].rebase().plot(logy=True)
plt.grid()


# 最大虧損
prices[["qqq", "tqqq_mock"]].to_drawdown_series().plot()
plt.grid()

plt.show()

# 計算
stats = prices[["qqq", "tqqq_mock"]].calc_stats()
stats.display()

