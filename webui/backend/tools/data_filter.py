# 定义基本的统计方法，能够方便地访问数据库并返回便于后期处理的数值

import datetime, time
import threading
import pandas as pd
import json
from pathlib import Path

# import numpy as np
# import matplotlib.pyplot as plt
# from textwrap import wrap

from tools.plot_styles import normal_style
from basetools.db_manager import LiveDatabase

# 对相同一组数据库进行不同时间粒度以及角度的提取及分析，并生成对应的小文件供前端使用
class GenStats:
    def __init__(self, platform: str, 
                 room_id, 
                 avail_info: str,
                 info_sheet_name:str,
                 update_times: dict = {"10seconds":"", "30seconds":"", "1minutes": "", "2minutes": "", "5minutes": "", "30minutes": "", "600minutes": "","history":""}):
        
        self.update_room_name = f"{platform}_{room_id}"
        self.update_json_file = f"configs/{self.update_room_name}_update.json"
        # 设置可以统计的变量名称
        self.avail_info = avail_info
        self.info_sheet_name = info_sheet_name
        # 设置可以访问的统计时间区间
        self.avail_update_times = update_times

        self.static_data = pd.DataFrame()
        
        self.rood_db = LiveDatabase(platform, room_id, collect_mode=False)

        # first check
        last_update_time = {}
        if Path(self.update_json_file).exists() == False:
            last_update_time[self.avail_info] = self.avail_update_times
            with open(self.update_json_file, "a+") as f:
                f.write(json.dumps(last_update_time))

        else:
            with open(self.update_json_file) as rf:
                last_update_time = json.load(rf)
                dict_keys = list(last_update_time.keys())
                if self.avail_info not in dict_keys:
                    last_update_time[self.avail_info] = self.avail_update_times
                # 增加对可用时间的更新处理
                else:
                    for update_time in self.avail_update_times:
                        if update_time not in last_update_time[self.avail_info]:
                            last_update_time[self.avail_info][update_time] = ""            

            with open(self.update_json_file, "w") as wf:
                wf.write(json.dumps(last_update_time))

        Path(f"stats/{self.update_room_name}").mkdir(exist_ok=True)

    def get_static_data(self, sheet_name, **kwargs):
        """
        最基础的获取原本的数据的函数，会返回对应时间范围的弹幕数据，在引用中可以进行完全的更改。
        可用的时间参数: 
        days: float,
        seconds: float,
        microseconds: float,
        milliseconds: float,
        minutes: float,
        hours: float,
        weeks: float"""

        now_time = datetime.datetime.now()
        time_delta = datetime.timedelta(**kwargs)
        
        # self.static_data = self.rood_db.select_by_time(sheet_name, (now_time-time_delta, now_time))
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.static_data = self.rood_db.select_run(sheet_name=sheet_name)

    def sort_by_arg(self, arg_name: str):
        pass
    
    def update_function(self, **kwargs) -> dict:
        
        return_dict = {"origin_data":{}}

        return return_dict
    
    # 后续可以使用getattr()来进行通用的匹配

    def normal_update(self,
                      update_info_name:str,    # 这个变量后续或许可以考虑去掉，没有实际的价值了
                      timeunit:str, 
                      timevalue,
                      info_count:int=100):
        
        assert update_info_name == self.avail_info
        assert timeunit in ["days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"]
        assert f"{timevalue}{timeunit}" in self.avail_update_times
        
        # 对应信息下的时间尺度的信息存储文件位置
        status_file_path = f"stats/{self.update_room_name}/{self.avail_info}_data_{timevalue}{timeunit}.json"

        now_time = datetime.datetime.now()

        with open(self.update_json_file) as f:
            interval_dict = json.load(f)
            str_time = interval_dict[self.avail_info][f"{timevalue}{timeunit}"]
            if str_time == "":    # 如果之前从未更新过，将更新时间划为一千年前来确保能够在后续过程中判断为更新
                str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime("%Y-%m-%d-%H-%M-%S")

            try:
                last_update = datetime.datetime.strptime(str_time, "%Y-%m-%d-%H-%M-%S")                    
            except ValueError:
                raise ValueError("Format error.")
        
        now_interval = now_time - last_update

        # 此处判断应该更新的条件，并执行更新操作
        if now_interval > eval(f"datetime.timedelta({timeunit}={timevalue})")/10 and now_interval > datetime.timedelta(seconds=60):    # 判断更新时间和现在的时间间隔，如果大于指定时间间隔就发生更新，并将更新时间重写入config文件中
            eval(f"self.get_static_data({timeunit}={timevalue}, sheet_name='{self.info_sheet_name}')")
            new_results = self.update_function(normalize_bool=False,
                                           send_count=info_count)
            
            interval_dict[self.avail_info][f"{timevalue}{timeunit}"] = now_time.strftime("%Y-%m-%d-%H-%M-%S")
            
            # 写入状态存储文件。此处保存的手段是直接覆盖之前的结果，因为更新不是实时的，所以保留历史记录也没太大意义
            with open(status_file_path, "w+") as ff:
                ff.write(json.dumps(new_results["origin_data"]))

            # new_results["fig"].savefig(f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png")

            with open(self.update_json_file, "w+") as fff:
                fff.write(json.dumps(interval_dict))
            
            last_update = now_time
        
        # 无论是否更新，都应该读取对应的信息存储文件，并提取信息
        with open(status_file_path) as f4:
            message = json.load(f4)
        
        all_message = {"data_status":"Full Pass.",
                       "data_info_name":self.avail_info,
                       "origin_data":message, 
                       "last_update":last_update.strftime("%Y-%m-%d %H:%M:%S"), 
                       "fig":f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png"}

        return all_message
