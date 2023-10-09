import pandas as pd

# 假设 df1 和 df2 是两个 DataFrame，它们具有相同的索引
df1 = pd.DataFrame({'A': [1, 2]}, index=pd.Index([10, 20]))
df2 = pd.DataFrame({'B': [3, 4]}, index=pd.Index([10, 30]))

# 使用 pd.concat 合并两个 DataFrame，保留相同索引的行
result = pd.concat([df1, df2], axis=1, join='inner')

print(result)
