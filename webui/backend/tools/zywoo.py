import datetime
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# import portalocker
import gc

import pandas as pd

from .data_filter import GenStats

class ZywooStats(GenStats):
    def __init__(self, platform: str, room_id):

        avail_info = "485"
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

    def update_function(self, normalize_bool: bool=False, send_count:int=100, plot_top:int=10):

        """
        对弹幕的文本信息进行提取的函数。
        normalize: 是否对数据进行百分比处理的布尔值
        plot_top: 统计结果中希望表现出的个数
        """
        
        if self.static_data.empty:
            return {"fig":'', "origin_data":{"showinfos":[[],[]], "counts":[[],[]]}}
        else:
            data = self.static_data

        danmaku_data = data["context"]
        userinfo_data = data["username"]

        danmaku_counts = danmaku_data.value_counts(normalize=normalize_bool)
        userinfo_counts = userinfo_data.value_counts(normalize=normalize_bool)
        
        danmaku_counts_pdf = danmaku_counts.reset_index()
        danmaku_counts_pdf.columns = ['context', 'count']

        danmaku_sorted = danmaku_counts_pdf["context"]
        danmaku_counts_sorted = danmaku_counts_pdf["count"]

        to_send_danmakus = danmaku_sorted.to_list()[:send_count]
        to_send_danmaku_counts = danmaku_counts_sorted.to_list()[:send_count]

        userinfo_counts_pdf = userinfo_counts.reset_index()
        userinfo_counts_pdf.columns = ['context', 'count']

        userinfo_sorted = userinfo_counts_pdf["context"]
        userinfo_counts_sorted = userinfo_counts_pdf["count"]

        to_send_userinfo = userinfo_sorted.to_list()[:send_count]
        to_send_userinfo_counts = userinfo_counts_sorted.to_list()[:send_count]
        
        fig = None

        del data, self.static_data, danmaku_counts, userinfo_counts, danmaku_counts_pdf, danmaku_sorted, danmaku_counts_sorted, userinfo_counts_pdf, userinfo_sorted, userinfo_counts_sorted
        gc.collect()

        return {"fig":fig, "origin_data":{"showinfos":[to_send_danmakus, to_send_userinfo], "counts":[to_send_danmaku_counts, to_send_userinfo_counts]}}
