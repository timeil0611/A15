import pandas as pd 
import sqlalchemy
from FinMind.data import DataLoader
stocks=[
'0050'
,'2330'
,'2317'
,'2454'
,'2308'
,'2303'
,'2412'
,'2891'
,'2881'
,'1303'
,'3711'
,'2886'
,'2882'
,'2884'
,'2002'
,'1216'
,'1301'
,'2382'
,'2885'
,'5871'
,'2892'
,'5880'
,'3034'
,'2207'
,'1101'
,'1326'
,'3008'
,'2880'
,'2357'
,'2887'
,'3037'
,'2883'
,'2890'
,'2327'
,'2379'
,'3045'
,'5876'
,'2395'
,'2912'
,'2603'
,'1590'
,'1605'
,'1402'
,'4904'
,'6505'
,'2801'
,'6415'
,'2609'
,'2615'
,'9910'
,'2408'
    
]
def stcok (id):
    stock_no = id
    dl = DataLoader()
    stock_data = dl.taiwan_stock_daily(stock_id=stock_no, start_date='2000-01-01')
    stock_data=stock_data.drop(['Trading_money', 'spread','spread','Trading_turnover'], axis=1)
    stock_data['date'] = pd.to_datetime(stock_data['date'])
    
    stock_data = stock_data.rename(columns={'stock_id': 'share_id'})
    
    print(stock_data.dtypes)
    # stock_data.insert(0, 'Sid', pd.Series(dtype=object))
    # stock_data['Sid'] = stock_data['share_id'].copy()
    return stock_data

def tosql(id):
    engine = sqlalchemy.create_engine('mysql+pymysql://root:1111@127.0.0.1:3306/stock')
    # MySQL導入DataFrame
    # DataFrame寫入MySQL
    # 新建DataFrame
    df_write = pd.DataFrame(stcok (id))
    # 將df儲存為MySQL中的表，不儲存index列
    df_write.to_sql('share_record', engine,if_exists='append', index=False)
    
num = 0
for i in stocks:
    num += 1
    print(i)
    tosql(i)