import numpy as np

#parameter setting
np.random.seed(111)
S = 14460 #現貨價
K = 14650 #履約價
r = 0.01 #無風險利率
sigma = 0.05 #現貨的報酬標準差
T = 1 #假設到期1年
days = 1 #每幾天抽樣一次
steps = int(365/days)#切割期數
N = 10000 #模擬路徑
dt = T/steps #delta t

epsilon = np.random.normal(size=(steps, N))
ST = np.log(S) + np.cumsum((r - 0.5*sigma**2)*dt + sigma  * epsilon * np.sqrt(dt), axis=0)
ST = np.exp(ST)

import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['xtick.labelsize'] = 16 
mpl.rcParams['ytick.labelsize'] = 16 

plt.plot(ST)
plt.xlabel('Period', fontsize=14)
plt.ylabel('Underlying price', fontsize=14)
plt.title('Monte Carlo simulation', fontsize=16)
# plt.savefig('/CallOption.png', bbox_inches='tight')#save fig
plt.show()