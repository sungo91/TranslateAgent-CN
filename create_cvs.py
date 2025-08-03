"""
@File    : create_cvs
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/08/03 00:18
"""
import csv

# 数据
data = [
    {"source": "aaa", "target": "bbb"}
]

# 写入 CSV
with open('name_mapping.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["source", "target"])
    writer.writeheader()
    writer.writerows(data)

print("CSV 文件已生成：xxx_mapping.csv")