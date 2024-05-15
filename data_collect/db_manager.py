import os 
import sqlite3

class live_database:
    def __init__(self, platform, room_id):

        plat_dict = {"bilibili":"bili", "douyu":"douyu"}

        path_to_db = os.environ.get("DB_PATH")+f"/{plat_dict[platform]}_{room_id}.db"
        self.conn = sqlite3.connect(path_to_db)
        self.cur = self.conn.cursor()

        # 目前支持的类型：弹幕，SC(B站限定)，礼物，TBC
        # 弹幕数据量很大，不再保留原始信息，为了未来的用户画像分析需要保留用户uid。剩下的数据量较小可以保留原始信息。
        table_names = self.cur.execute("select name from sqlite_master where type='table' order by name")
        if (("danmaku",) in table_names.fetchall()) == False:
            self.cur.execute(f"""CREATE TABLE IF NOT EXISTS danmaku (
            time DATETIME, username TEXT, context TEXT,
            uid TEXT,
            fans_club TEXT, fans_level TEXT
            )""")
        if (("super_chat",) in table_names.fetchall()) == False and platform == "bilibili":
            self.cur.execute(f"""CREATE TABLE IF NOT EXISTS super_chat (
            time DATETIME, username TEXT, context TEXT,
            price INT, keep_time INT,
            fans_club TEXT, fans_level TEXT,
            origin_data TEXT
            )""")
        if (("gifts",) in table_names.fetchall()) == False:
            self.cur.execute(f"""CREATE TABLE IF NOT EXISTS gifts (
            time DATETIME, username TEXT, context TEXT,
            price INT,
            fans_club TEXT, fans_level TEXT,
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