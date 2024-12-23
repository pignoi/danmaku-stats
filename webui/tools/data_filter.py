import datetime
import threading
import pandas as pd
import json
from pathlib import Path

from basetools.db_manager import LiveDatabase

# 对相同一组数据库进行不同时间粒度（1、2、5、10min）以及角度的提取及分析，并生成对应的小文件供前端使用
class GenStatic:
    def __init__(self, platform:str, room_id):
        
        self.update_index = f"{platform}_{room_id}"
        self.update_json = f"configs/{self.update_index}_update.json"
                
        # first check
        if Path(self.update_json).exists() == False:
            last_update_time = {"1min": "", "2min": "", "5min": "", "30min": "", "60min": "","history":""}
            with open(self.update_json, "a+") as f:
                f.write(json.dumps(last_update_time))
       
        self.rood_db = LiveDatabase(platform, room_id, collect_mode=False)

    def get_by_time(self, **kwargs):
        """可用的时间参数: 
        days: float,
        seconds: float,
        microseconds: float,
        milliseconds: float,
        minutes: float,
        hours: float,
        weeks: float"""

        now_time = datetime.datetime.now()
        time_delta = datetime.timedelta(**kwargs)
        
        return self.rood_db.select_by_time("danmaku", (now_time-time_delta, now_time))

    def sort_by_arg(self, arg_name: str):
        pass

    def get_data(self, data:pd.DataFrame):

        danmaku_data = data["context"]
        danmaku_counts = danmaku_data.value_counts(normalize=True)

        return danmaku_counts
    
    def static_child(self, update_interval:int):
        """update_interval: 子进程更新的频率，以分钟为单位"""
        sleep_interval = 60*update_interval/5
        while True:
            with open(self.update_json) as f:
                last_update_times = json.load(f)
                try:
                    child_last_update = \
                        datetime.datetime.strptime(last_update_times[f"{update_interval}min"], "%Y-%m-%d-%H-%M-%S")
                except KeyError:
                    raise KeyError(f"{update_interval}min not in plan.")
                except ValueError:
                    raise ValueError("Format error.")
            
                if child_last_update == "":
                    child_last_update = datetime.datetime.now()
                    # last_update_times[f"{update_interval}min"] = child_last_update.strftime("%Y-%m-%d-%H-%M-%S")
            
            now_time = datetime.datetime.now()
            now_interval = (now_time - child_last_update).seconds

            if now_interval > update_interval * 60:
                pass
            
            # 可能可以使用getattr()来进行通用的匹配