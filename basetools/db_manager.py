import os 
import datetime
import sqlite3
import threading
import time
import logging
from pathlib import Path

import pandas as pd

class LiveDatabase:
    def __init__(self, platform, room_id, collect_mode:bool=True):

        plat_dict = {"bilibili":"bili", "douyu":"douyu"}

        try:
            path_to_db = f"{os.environ.get('DB_PATH')}/{plat_dict[platform]}_{room_id}.db"
        except KeyError:
            raise FileExistsError(f"Platform {platform} Do Not Exist.")
    
        # 在 collect_mode==False 的情况下需要路径下存在对应的数据库再执行后续任务，否则就不会执行
        if (collect_mode == False and Path(path_to_db).exists() == True) or (collect_mode == True):
            # 如果不是收集模式，在连接数据库的时候要以只读模式打开，防止和写入过程的连接产生冲突
            if collect_mode == False:
                file_uri = f"file:{path_to_db}?mode=ro"
                self.conn = sqlite3.connect(file_uri, check_same_thread=False, uri=True)
                self.cur = self.conn.cursor()

                self.table_names = self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()

            elif collect_mode == True:
                self.conn = sqlite3.connect(path_to_db, check_same_thread=False)
                self.cur = self.conn.cursor()
                # 目前支持的类型：弹幕，SC(B站限定)，礼物，TBC
                # 弹幕数据量很大，不再保留原始信息，为了未来的用户画像分析需要保留用户uid。剩下的数据量较小可以保留原始信息。
                self.table_names = self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()
                
                if (("danmaku",) in self.table_names) == False:
                    self.cur.execute(f"""CREATE TABLE IF NOT EXISTS danmaku (
                    time DATETIME, username TEXT, context TEXT,
                    uid TEXT,
                    fans_club TEXT, fans_level TEXT
                    )""")                
                
                if (("super_chat",) in self.table_names) == False and platform == "bilibili":
                    self.cur.execute(f"""CREATE TABLE IF NOT EXISTS super_chat (
                    time DATETIME, username TEXT, context TEXT,
                    price INT, keep_time INT,
                    fans_club TEXT, fans_level TEXT,
                    origin_data TEXT
                    )""")                

                if (("gifts",) in self.table_names) == False:
                    self.cur.execute(f"""CREATE TABLE IF NOT EXISTS gifts (
                    time DATETIME, username TEXT, context TEXT,
                    price INT,
                    fans_club TEXT, fans_level TEXT,
                    origin_data TEXT
                    )""")

                try:
                    self.drop_interval = float(os.environ["DB_DROP_INTERVAL"])
                except KeyError:
                    self.drop_interval = 5

                self.cache_danmaku = []
                self.cache_thread = threading.Thread(target=self.drop_cache, daemon=True)
                self.cache_thread.start()

                monitor_thread = threading.Thread(target=self.monitor_danmaku, daemon=True)
                monitor_thread.start()

            self.danmaku_keys = ["time", "username", "context", "uid", "fans_club", "fans_level"]
            self.sc_keys = ["time", "username", "context", "price", "keep_time", "uid", "fans_club", "fans_level"]
            
            # 为筛选模式初始化变量
            self._select_init()

        elif (collect_mode == False and Path(path_to_db).exists() == False):
            raise FileExistsError(f"Collect Mode is False but {path_to_db} do Not Exist.")
    
    def _select_init(self):
        self.select_sentence = ""
        self.select_paramters = []

    def insert(self, sheet_name, data):
        if sheet_name != "danmaku":
            data_numb = len(data)
            sql_insert = f"INSERT INTO {sheet_name} values ({','.join(['?' for _ in range(data_numb)])})"
            try:
                self.cur.execute(sql_insert, data)
            except Exception as e:
                self.conn.rollback()
            finally:
                self.conn.commit()
        else:
            self.cache_danmaku.append(data)
    
    def drop_cache(self):
        logging.info("start cache child threading.")
        start_time = time.time()
        sql_insert = f"INSERT INTO danmaku values ({','.join(['?' for _ in range(6)])})"
        while True:
            now_time = time.time()
            if len(self.cache_danmaku) > 50 or now_time - start_time >= self.drop_interval:
                try:
                    self.cur.executemany(sql_insert, self.cache_danmaku)
                except Exception as e:
                    self.conn.rollback()
                finally:
                    self.conn.commit()
                    
                start_time = time.time()
                self.cache_danmaku = []
            
            time.sleep(self.drop_interval/2)
    
    def monitor_danmaku(self):
        """对drop到数据库的线程进行手动监控的方法，防止意外终止，但是好像加了daemon之后就还好"""
        while True:
            if self.cache_thread.is_alive() == False:
                logging.info("danmaku drop cache child process died.")
                # self.cache_thread.join()
                self.cache_thread = threading.Thread(target=self.drop_cache, daemon=True)
                self.cache_thread.start()
            time.sleep(0.5)

    def split_sheet(self):
        # 定义一段时间后分表的方法
        # 因为一段时间内的总弹幕量不会非常大，目前的想法是每隔一段时间对本表中第一条数据进行和现在的时间进行比较，如果超出一定阈值就将**一定时间范围**的数据放到一个新表，然后将对应的数据在本表中删除
        # 需要更新的内容: self.table_names，后续的功能需要根据这个变量的内容进行匹配修改，如history的数值需要对符合name的所有表进行遍历
        while True:
            pass

    def _format_results(self, keys:list, values:list) -> dict:         
        dict = {}
        for index, key in enumerate(keys):
            value_list = [i[index] for i in values]
            dict[key] = value_list
        
        return dict

    def select_by_time(self, sheet_name, time_span) -> pd.DataFrame:
        """原本的根据时间进行筛选的方法"""
        if (sheet_name,) in self.table_names:
            start_time = time_span[0]
            end_time = time_span[1]

            assert start_time <= end_time

            sql_select = f"SELECT * FROM {sheet_name} WHERE time BETWEEN ? AND ?"
            result = self.cur.execute(sql_select, (start_time, end_time)).fetchall()
        
            keys = getattr(self, f"{sheet_name}_keys")
            
            result_dict = self._format_results(keys, result)
            result_frame = pd.DataFrame.from_dict(result_dict)
        
        else:
            raise KeyError(f"There is no table named {sheet_name}")
        
        return result_frame
    
    # 对常用的参数进行灵活的组合，使得筛选方法变为可拓展的方法
    def para_time(self, start_time:datetime.datetime, end_time:datetime.datetime):

        assert start_time <= end_time

        if self.select_sentence == "":
            sql_select = "time BETWEEN ? AND ? "
        else:
            sql_select = "AND time BETWEEN ? AND ? "
        self.select_sentence += sql_select
        
        self.select_paramters.append(start_time)
        self.select_paramters.append(end_time)
        
    def para_include(self, field_name, include_para):
        
        if self.select_sentence == "":
            sql_select = rf"{field_name} LIKE ? ESCAPE '\' "
        else:
            sql_select = rf"AND {field_name} LIKE ? ESCAPE '\' "
        self.select_sentence += sql_select
        self.select_paramters.append(f"%{include_para}%")

    def select_run(self, sheet_name):
        """
        运行筛选方法的主函数。
        """
        if (sheet_name,) in self.table_names:
            select_head = f"SELECT * FROM {sheet_name} WHERE "
            sql_select = select_head + self.select_sentence

            result = self.cur.execute(sql_select, self.select_paramters).fetchall()

            keys = getattr(self, f"{sheet_name}_keys")
                
            result_dict = self._format_results(keys, result)
            result_frame = pd.DataFrame.from_dict(result_dict)
        
        else:
            raise KeyError(f"There is no table named {sheet_name}")
        
        # 在运行完一轮筛选后对语句和参数进行清除
        self._select_init()

        return result_frame        
