import os 
import sqlite3

class live_database:
    def __init__(self, platform, room_id):
        path_to_db = os.environ.get("DB_PATH")+f"/{platform}.db"
        self.conn = sqlite3.connect(path_to_db)
        self.cur = self.conn.cursor()

        self.sheet_name = f"db_{room_id}"

        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.sheet_name} (
        time DATETIME,
        username TEXT,
        context TEXT,
        origin_data TEXT
        )""")
    
    def insert(self, data):
        sql_insert = f"INSERT INTO {self.sheet_name}(time,username,context,origin_data) values(?,?,?,?)"
        self.cur.execute(sql_insert, data)
        self.conn.commit()
    
    def select_by_time(self, time_span):
        start_time = time_span[0]
        end_time = time_span[1]

        sql_select = f"SELECT * FROM {self.sheet_name} WHERE time BETWEEN ? AND ?"
        result = self.cur.execute(sql_select, (start_time, end_time))

        return result.fetchall()