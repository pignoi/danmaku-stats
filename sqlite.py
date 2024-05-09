import os
import sqlite3
import datetime
from data_collect.db_manager import live_database

now = datetime.datetime.now()
before = now - datetime.timedelta(days=10)
os.environ["DB_PATH"] = "/home/webapp/danmaku-stats/dbs"

con = sqlite3.connect('dbs/bilibili.db')
cur = con.cursor()
aaa = cur.execute("select name from sqlite_master where type='table' order by name")
# print(("db_3044248",) in aaa.fetchall())
# cur.execute('''CREATE TABLE IF NOT EXISTS timedb (
#     id INTEGER PRIMARY KEY,
#     time DATETIME)''')

insert_sql = "insert into db_3044248 values(?,?,?,?)"
cur.execute(insert_sql, (now - datetime.timedelta(days=5),"","",""))
# cur.execute(insert_sql, (now - datetime.timedelta(days=15)))
con.commit()

# # result = conn.execute('SELECT * FROM my_table WHERE name = ?', ('xiaoming',))
# result = cur.execute("SELECT * FROM timedb WHERE time >= ?", (now - datetime.timedelta(days=10),))
# print(result.fetchall())
# print(cur.description)

# con.close()
# room_id = 3044248
# room_db = live_database("bilibili", room_id)

# a = room_db.cur.execute(f"SELECT * FROM {room_db.sheet_name}")
# print(a.fetchall())

# print(room_db.select_by_time((before, now)))
