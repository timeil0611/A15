
from FinMind.data import DataLoader
import pandas as pd

import talib
from talib import abstract
import matplotlib.pyplot as plt

import yfinance as yf


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()


start = "1980-01-01"

# 取得資料
qqq = pd.read_csv("qqq.csv")
tqqq_mock = pd.read_csv("tqqq_mock.csv")
qqq_volume = yf.download("qqq", start="1980-02-17", end="2023-10-21", interval="1d")
tqqq = yf.download("tqqq", start="1980-02-17", end="2023-10-21", interval="1d")


# 製作tqqq的candle
tqqq_mock.set_index("Date", inplace=True)
tqqq_mock.set_index(pd.DatetimeIndex(tqqq_mock.index), inplace=True)
tqqq_mock = tqqq_mock[start:]


tqqq[["Open", "High", "Low", "Close"]] = (
    tqqq[["Open", "High", "Low", "Close"]] * 15.673452585631295748931984327121
)

tqqq_mock["Open"] = tqqq_mock["tqqq_mock"]
tqqq_mock["High"] = tqqq_mock["tqqq_mock"]
tqqq_mock["Low"] = tqqq_mock["tqqq_mock"]
tqqq_mock["Close"] = tqqq_mock["tqqq_mock"]
tqqq_mock["Volume"] = tqqq_mock["tqqq_mock"]

tqqq_mock["Open"].update(tqqq["Open"])
tqqq_mock["High"].update(tqqq["High"])
tqqq_mock["Low"].update(tqqq["Low"])
tqqq_mock["Close"].update(tqqq["Close"])
tqqq_mock["Volume"].update(qqq_volume["Volume"])


df = tqqq_mock
df['Open'] = df.apply(lambda row: row['Close'] if row['Open'] == 0 else row['Open'], axis=1)
df.to_csv('TQQQ_Mock_kline.csv', index=True)