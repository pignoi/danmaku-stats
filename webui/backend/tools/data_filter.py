import datetime, time
import threading
import pandas as pd
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap

from tools.plot_styles import normal_style
from basetools.db_manager import LiveDatabase

# 对相同一组数据库进行不同时间粒度以及角度的提取及分析，并生成对应的小文件供前端使用
class GenStats:
    def __init__(self, platform:str, room_id):
        
        self.update_index = f"{platform}_{room_id}"
        self.update_json = f"configs/{self.update_index}_update.json"

        self.static_data = pd.DataFrame()
        
        self.rood_db = LiveDatabase(platform, room_id, collect_mode=False)

        # first check
        if Path(self.update_json).exists() == False:
            last_update_time = {"10seconds":"", "30seconds":"", "1minutes": "", "2minutes": "", "5minutes": "", "30minutes": "", "600minutes": "","history":""}
            with open(self.update_json, "a+") as f:
                f.write(json.dumps(last_update_time))

        Path(f"stats/{self.update_index}").mkdir(exist_ok=True)

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
        
        self.static_data = self.rood_db.select_by_time("danmaku", (now_time-time_delta, now_time))

    def sort_by_arg(self, arg_name: str):
        pass

    def context_static(self, normalize: bool=False, ignore_words:list=["?","？","1"], plot_top:int=10):

        """
        normalize: 是否对数据进行百分比处理
        ignore_words: 统计结果中不希望出现的词汇/关键词
        plot_top: 统计结果中希望表现出的个数
        """
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        danmaku_data = data["context"]
        danmaku_data = danmaku_data[~danmaku_data.isin(ignore_words)]
        
        danmaku_counts = danmaku_data.value_counts(normalize=normalize)
        # danmaku_percents = danmaku_counts.values / np.sum(danmaku_counts.values)
        
        counts_pdf = danmaku_counts.reset_index()
        counts_pdf.columns = ['context', 'count']

        danmaku_sorted = counts_pdf["context"]
        counts_sorted = counts_pdf["count"]

        # 前n名弹幕画图
        # danmaku_topn = danmaku_sorted[0: plot_top]
        # count_topn = danmaku_counts[0: plot_top]
        # plot_top = count_topn.shape[0]
        # for num, i in enumerate(danmaku_topn):    # 处理b站表情包的长链接
        #     if "http://i0.hdslb.com" in i:
        #         mes_list = i.split('(')[:-1]
        #         danmaku_topn[num] = f"{'('.join(mes_list)}(表情包)"
        
        # normal_style()
        # plot_labels = ['\n'.join(wrap(i, width=12)) for i in danmaku_topn[::-1]]
        # plot_values = count_topn[::-1]
        
        fig = None
        # fig, ax = plt.subplots()
        # for y, x in enumerate(plot_values):
        #     ax.text(x - 0.1, y, str(x), va='center', ha="right", fontsize=10)  # 数值标签位置
        # ax.barh(plot_labels, plot_values, color='skyblue')
        
        # ax.set_yticks(range(plot_top))  # 确保刻度位置与标签对应
        # ax.set_yticklabels(plot_labels, rotation=30, fontsize=int(80/plot_top))  # 旋转一定角度，水平对齐为右

        return {"fig":fig, "origin_data":{"danmakus":danmaku_sorted.to_list(), "counts":counts_sorted.to_list()}}
            
    def dynamic_update(self, update_interval:int):
        # 该方法在后续的完善的统计历史中可能会用到，但是目前的更新方式暂时不需要用到此方法
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

            time.sleep(sleep_interval)
            
    # 后续可以使用getattr()来进行通用的匹配

    def normal_update(self, timeunit:str, timevalue):
        
        assert timeunit in ["days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"]
        
        now_time = datetime.datetime.now()

        with open(self.update_json) as f:
            interval_dict = json.load(f)
            str_time = interval_dict[f"{timevalue}{timeunit}"]
            if str_time == "":    # 如果之前从未更新过，将更新时间划为一千年前来确保能够在后续过程中判断为更新
                str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime("%Y-%m-%d-%H-%M-%S")

            last_update = datetime.datetime.strptime(str_time, "%Y-%m-%d-%H-%M-%S")
        
        now_interval = now_time - last_update

        if now_interval > eval(f"datetime.timedelta({timeunit}={timevalue})"):    # 判断更新时间和现在的时间间隔，如果大于指定时间间隔就发生更新，并将更新时间重写入config文件中
            eval(f"self.get_by_time({timeunit}={timevalue})")
            new_results = self.context_static(normalize=False, plot_top=20)
            interval_dict[f"{timevalue}{timeunit}"] = now_time.strftime("%Y-%m-%d-%H-%M-%S")
            
            # 此处保存的手段是直接覆盖之前的结果，因为更新不是实时的，所以保留历史记录也没太大意义
            with open(f"stats/{self.update_index}/origin_data_{timevalue}{timeunit}.json", "w+") as ff:
                ff.write(json.dumps(new_results["origin_data"]))

            # new_results["fig"].savefig(f"stats/{self.update_index}/fig_{timevalue}{timeunit}.png")

            with open(self.update_json, "w+") as fff:
                fff.write(json.dumps(interval_dict))
        
        # 汇总最终的信息
        with open(f"stats/{self.update_index}/origin_data_{timevalue}{timeunit}.json") as f4:
            message = json.load(f4)
        
        all_message = {"data_status":"Full Pass.",
                       "origin_data":message, 
                       "last_update":last_update.strftime("%Y-%m-%d %H:%M:%S"), 
                       "fig":f"stats/{self.update_index}/fig_{timevalue}{timeunit}.png"}

        return all_message
