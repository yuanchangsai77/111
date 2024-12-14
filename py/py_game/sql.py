import sqlite3

# 连接到 SQLite 数据库（如果文件不存在，会自动创建）
conn = sqlite3.connect('pacman.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(tables)

# 查看某个表的数据
cursor.execute("SELECT * FROM maps;")
rows = cursor.fetchall()
for row in rows:
    print(row)

# 关闭连接
conn.close()
