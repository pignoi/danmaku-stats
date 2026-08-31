import datetime
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import pandas as pd

from .data_filter import GenStats

class ZywooStats(GenStats):
    def __init__(self, platform: str, room_id):

        avail_info = "zywoo"
        update_times = {"1minutes":"", "1hours":"", "1days":"", "100000days":""}
        info_sheet_name = "danmaku"

        super().__init__(platform, room_id, avail_info, info_sheet_name, update_times)

    def get_static_data(self, **kwargs):
        # 首先对时间进行检索
        # TODO: 这块说明代码需要再次完善重构一下
        
        now_time = datetime.datetime.now()
        time_delta = datetime.timedelta(**kwargs)

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "zywoo")
        static_data_zywoo = self.rood_db.select_run()
        
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "485")
        static_data_485 = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "误 触")
        static_data_wuchu = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "fywoo")
        static_data_fywoo = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "冰粉")
        static_data_bingfen = self.rood_db.select_run()
        
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "🧊粉")
        static_data_bingfen2 = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "贼物")
        static_data_zeiwu = self.rood_db.select_run()
        
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "冰清玉洁")
        static_data_bqyj = self.rood_db.select_run()
        
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "人品")
        static_data_rp = self.rood_db.select_run()

        self.static_data = pd.merge(static_data_485, static_data_wuchu, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_fywoo, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_bingfen, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_bingfen2, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_zeiwu, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_bqyj, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_rp, how="outer")
