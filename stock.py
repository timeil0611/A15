import pandas as pd
from FinMind.data import DataLoader
stock_no = '0050'
dl = DataLoader()
stock_data = dl.taiwan_stock_daily(stock_id=stock_no, start_date='2000-01-01')
stock_data=stock_data.drop(['Trading_money', 'spread','spread','Trading_turnover'], axis=1)
stock_data['date'] = pd.to_datetime(stock_data['date'])

stock_data.insert(0, 'Sid', pd.Series(dtype=object))

stock_data['Sid'] = stock_data['stock_id'].copy()

print(stock_data)

print(stock_data.dtypes)