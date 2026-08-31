import datetime
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import pandas as pd

from .data_filter import GenStats

class DesuwaStats(GenStats):
    def __init__(self, platform: str, room_id):

        avail_info = "desuwa"
        update_times = {"1minutes":"", "1hours":"", "1days":"", "100000days":""}
        info_sheet_name = "danmaku"

        super().__init__(platform, room_id, avail_info, info_sheet_name, update_times)

    def get_static_data(self, **kwargs):
        # 首先对时间进行检索，再对desuwa等木柜子的后缀进行筛选
        
        now_time = datetime.datetime.now()
        time_delta = datetime.timedelta(**kwargs)
        
        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "desuwa")
        static_data_desuwa = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "desu")
        static_data_desu = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "ですわ")
        static_data_ですわ = self.rood_db.select_run()

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.rood_db.para_include("context", "这一块")
        static_data_cn = self.rood_db.select_run()

        self.static_data = pd.merge(static_data_desuwa, static_data_desu, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_ですわ, how="outer")
        self.static_data = pd.merge(self.static_data, static_data_cn, how="outer")
