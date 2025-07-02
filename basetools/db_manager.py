import os 
import datetime
import sqlite3
import threading
import time
import logging
from pathlib import Path

import pandas as pd

class LiveDatabase:
    def __init__(self, platform, room_id,
                 collect_mode: bool=True,
                 flit_table: str="If not in collect mode, must set!"):

        plat_dict = {"bilibili":"bili", "douyu":"douyu"}

        try:
            path_to_db = f"{os.environ.get('DB_PATH')}/{plat_dict[platform]}_{room_id}.db"
        except KeyError:
            raise FileExistsError(f"Platform {platform} Do Not Exist.")
    
        # 在 collect_mode==False 的情况下需要路径下存在对应的数据库再执行后续任务，否则就不会执行
        if (collect_mode == False and Path(path_to_db).exists() == True) or (collect_mode == True):
            # 如果不是收集模式，在连接数据库的时候要以只读模式打开，防止和写入过程的连接产生冲突
            if collect_mode == False:
                if flit_table == "If not in collect mode, must set!":
                    raise NotImplementedError("必须设置统计所需要的表的名称！")
                elif flit_table not in ["danmaku", "super_chat", "gifts"]:
                    raise ValueError("不合法的统计表名称")
                else:
                    self.flit_table = flit_table

                file_uri = f"file:{path_to_db}?mode=ro"
                self.conn = sqlite3.connect(file_uri, check_same_thread=False, uri=True)
                self.cur = self.conn.cursor()

                self.operate_table_names = [i[0] for i in self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]
                self.table_names = ["danmaku", "super_chat", "gifts"]

            elif collect_mode == True:
                self.conn = sqlite3.connect(path_to_db, check_same_thread=False)
                self.cur = self.conn.cursor()
                # 目前支持的类型：弹幕，SC(B站限定)，礼物，TBC
                # 弹幕数据量很大，不再保留原始信息，为了未来的用户画像分析需要保留用户uid。剩下的数据量较小可以保留原始信息。
                self.operate_table_names = [i[0] for i in self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]
                self.table_names = ["danmaku", "super_chat", "gifts"]
                
                if ("danmaku" in self.table_names) == False:
                    self.cur.execute(f"""CREATE TABLE IF NOT EXISTS danmaku (
                    time DATETIME, username TEXT, context TEXT,
                    uid TEXT,
                    fans_club TEXT, fans_level TEXT
                    )""")                
                
                if ("super_chat" in self.table_names) == False:
                    self.cur.execute(f"""CREATE TABLE IF NOT EXISTS super_chat (
                    time DATETIME, username TEXT, context TEXT,
                    price INT, keep_time INT,
                    fans_club TEXT, fans_level TEXT,
                    origin_data TEXT
                    )""")                

                if ("gifts" in self.table_names) == False:
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

                self._lock_tables = False
                split_thread = threading.Thread(target=self.split_sheet, daemon=True)
                split_thread.start()

            self.danmaku_keys = ["time", "username", "context", "uid", "fans_club", "fans_level"]
            self.super_chat_keys = ["time", "username", "context", "price", "keep_time", "uid", "fans_club", "fans_level"]
            
            # 为筛选模式初始化变量
            self._select_init()

        elif (collect_mode == False and Path(path_to_db).exists() == False):
            raise FileExistsError(f"Collect Mode is False but {path_to_db} do Not Exist.")

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
                # 如果正在进行分表操作，需要等到锁解除
                while self._lock_tables == True:
                    time.sleep(1)
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
            self._lock_tables = True
            for table_name in self.table_names:
                
                first_time_row = self.cur.execute(f"SELECT time FROM {table_name} LIMIT 1").fetchone()
                if not first_time_row:
                    time_diff = datetime.timedelta(minutes=1)
                else:
                    first_time_str = first_time_row[0]
                    logging.info(f"First time of {table_name} is {first_time_str}.")
                    now_time = datetime.datetime.now()
                    first_time = datetime.datetime.strptime(first_time_str, "%Y-%m-%d %H:%M:%S")
                    time_diff = now_time - first_time

                if time_diff > datetime.timedelta(weeks=1):
                    to_split_time_start = first_time
                    to_split_time_end = datetime.datetime(year=now_time.year, month=now_time.month, day=now_time.day-1, hour=23, minute=59, second=59)
                    new_table_name = f"{table_name}_{to_split_time_start.strftime('%Y%m%d')}_{to_split_time_end.strftime('%Y%m%d')}"
                    
                    self.conn.execute("BEGIN TRANSACTION")
                    # 创建存储旧数据的新的表
                    self.cur.execute(f"CREATE TABLE {new_table_name} AS SELECT * FROM {table_name} WHERE 1=0")
                    # 将老表中的数据迁移到新表，只迁移截止到今天0点的数据，减少数据重叠信息损失带来的问题
                    self.cur.execute(f"INSERT INTO {new_table_name} SELECT * FROM {table_name} WHERE time BETWEEN ? AND ?", (to_split_time_start, to_split_time_start))
                    # 删除原表中的数据
                    self.cur.execute(f"DELETE FROM {table_name} WHERE time BETWEEN ? AND ?", (to_split_time_start, to_split_time_start))
                    self.conn.commit()

                    logging.info(f"已创建新表 {new_table_name}")
                
                self.operate_table_names = [i[0] for i in self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]
                
            self._lock_tables = False
            time.sleep(3600*24)

    # 以下是对筛选模式功能的一些定义
    def _select_init(self):
        self.select_sentence = ""
        self.select_paramters = []

    def _format_results(self, keys:list, values:list) -> dict:         
        dict = {}
        for index, key in enumerate(keys):
            value_list = [i[index] for i in values]
            dict[key] = value_list
        
        return dict

    def select_by_time(self, sheet_name, time_span) -> pd.DataFrame:
        """原本的根据时间进行筛选的方法"""
        if sheet_name in self.table_names:
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
            # 如果这是第一条设置筛选的指令，对可以进行筛选的table进行初步划定
            self.operate_table_names = [i[0] for i in self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]
            self.avail_tables = [i for i in self.operate_table_names if self.flit_table in i]    # 在后面的处理中，这里取并集，对最小的需要筛选的表进行筛选运算

            sql_select = "time BETWEEN ? AND ? "
        else:
            sql_select = "AND time BETWEEN ? AND ? "
        
        # 根据时间进行筛选表的动作
        time_table_fliter = []
        for avail_table in self.avail_tables:
            if avail_table == self.flit_table:    # 判断是否为目前更新的总表，如果是的话就直接加入到待处理的表当中
                time_table_fliter.append(avail_table)
            else:
                table_start_time = datetime.datetime.strptime(avail_table.split("_")[-2], "%Y%m%d")
                table_end_time = datetime.datetime.strptime(avail_table.split("_")[-1], "%Y%m%d")

                if (table_start_time > start_time) and (table_end_time < end_time):
                    time_table_fliter.append(avail_table)
                elif (table_start_time < start_time) and (table_end_time < end_time) and (table_end_time > start_time):
                    time_table_fliter.append(avail_table)
                elif (table_start_time > start_time) and (table_end_time > end_time) and (table_start_time < end_time):
                    time_table_fliter.append(avail_table)
        
        # 对全局的变量进行修改
        self.select_sentence += sql_select
        
        self.select_paramters.append(start_time)
        self.select_paramters.append(end_time)

        self.avail_tables = list(set(self.avail_tables) & set(time_table_fliter))
        
    def para_include(self, field_name, include_para):
        
        if self.select_sentence == "":
            # 如果这是第一条设置筛选的指令，对可以进行筛选的table进行初步划定
            self.operate_table_names = [i[0] for i in self.cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]
            self.avail_tables = [i for i in self.operate_table_names if self.flit_table in i]    # 在后面的处理中，这里取并集，对最小的需要筛选的表进行筛选运算
            
            sql_select = rf"{field_name} LIKE ? ESCAPE '\' "
        else:
            sql_select = rf"AND {field_name} LIKE ? ESCAPE '\' "
        
        include_table_fliter = self.avail_tables

        self.select_sentence += sql_select
        self.select_paramters.append(f"%{include_para}%")
        self.avail_tables = list(set(self.avail_tables) & set(include_table_fliter))

    def select_run(self):
        """
        运行筛选方法的主函数，对传递过来的table进行逐一处理，并将其加入到结果frame当中。
        """
        keys = getattr(self, f"{self.flit_table}_keys")
        result_frame = pd.DataFrame([], columns=keys)
        try:
            for sheet_name in self.avail_tables:
                select_head = f"SELECT * FROM {sheet_name} WHERE "
                sql_select = select_head + self.select_sentence

                result = self.cur.execute(sql_select, self.select_paramters).fetchall()    
                
                result_dict = self._format_results(keys, result)
                result_frame = pd.merge(pd.DataFrame.from_dict(result_dict), result_frame, how="outer")
        
        except Exception as e:
            raise e("You should run para_methods first!")
        
        # 在运行完一轮筛选后对语句和参数进行清除
        self._select_init()

        return result_frame        
