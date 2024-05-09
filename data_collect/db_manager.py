import os 
import sqlite3

class live_database:
    def __init__(self, platform, room_id):

        plat_dict = {"bilibili":"bili", "douyu":"douyu"}

        path_to_db = os.environ.get("DB_PATH")+f"/{plat_dict[platform]}_{room_id}.db"
        self.conn = sqlite3.connect(path_to_db)
        self.cur = self.conn.cursor()

        # 目前支持的类型：弹幕，TBC
        table_names = self.cur.execute("select name from sqlite_master where type='table' order by name")
        if (("danmaku",) in table_names.fetchall()) == False:
            self.cur.execute(f"""CREATE TABLE IF NOT EXISTS danmaku (
            time DATETIME,
            username TEXT,
            context TEXT,
            origin_data TEXT
            )""")
    
    def insert(self, sheet_name, data):
        data_numb = len(data)
        sql_insert = f"INSERT INTO {sheet_name} values ({','.join(['?' for _ in range(data_numb)])})"
        self.cur.execute(sql_insert, data)
        self.conn.commit()
    
    def select_by_time(self, sheet_name, time_span):
        start_time = time_span[0]
        end_time = time_span[1]

        sql_select = f"SELECT * FROM {sheet_name} WHERE time BETWEEN ? AND ?"
        result = self.cur.execute(sql_select, (start_time, end_time))

        return result.fetchall()