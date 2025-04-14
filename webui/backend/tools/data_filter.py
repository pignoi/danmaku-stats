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
    def __init__(self, platform:str, room_id, ignore_words:list=["?","？","1"]):
        
        self.update_room_name = f"{platform}_{room_id}"
        self.update_json_file = f"configs/{self.update_room_name}_update.json"
        # 设置可以统计的变量名称
        self.avail_info = ["danmaku", "username"]

        self.static_data = pd.DataFrame()
        self.ignore_words = ignore_words
        
        self.rood_db = LiveDatabase(platform, room_id, collect_mode=False)

        # first check
        if Path(self.update_json_file).exists() == False:
            last_update_time = {
                "danmaku":{"10seconds":"", "30seconds":"", "1minutes": "", "2minutes": "", "5minutes": "", "30minutes": "", "600minutes": "","history":""},
                "username":{"10seconds":"", "30seconds":"", "1minutes": "", "2minutes": "", "5minutes": "", "30minutes": "", "600minutes": "","history":""}
            }
            with open(self.update_json_file, "a+") as f:
                f.write(json.dumps(last_update_time))

        else:
            with open(self.update_json_file) as rf:
                last_update_time = json.load(rf)
                dict_keys = list(last_update_time.keys())
                for info_name in self.avail_info:
                    if info_name not in dict_keys:
                        last_update_time[info_name] = {"10seconds":"", "30seconds":"", "1minutes": "", "2minutes": "", "5minutes": "", "30minutes": "", "600minutes": "","history":""}

            with open(self.update_json_file, "w") as wf:
                wf.write(json.dumps(last_update_time))

        Path(f"stats/{self.update_room_name}").mkdir(exist_ok=True)

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

    def context_static(self, normalize: bool=False, send_count:int=100, plot_top:int=10):

        """
        对弹幕的文本信息进行提取的函数。
        normalize: 是否对数据进行百分比处理
        ignore_words: 统计结果中不希望出现的词汇/关键词
        plot_top: 统计结果中希望表现出的个数
        """
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        danmaku_data = data["context"]
        danmaku_data = danmaku_data[~danmaku_data.isin(self.ignore_words)]
        
        danmaku_counts = danmaku_data.value_counts(normalize=normalize)
        # danmaku_percents = danmaku_counts.values / np.sum(danmaku_counts.values)
        
        counts_pdf = danmaku_counts.reset_index()
        counts_pdf.columns = ['context', 'count']

        danmaku_sorted = counts_pdf["context"]
        counts_sorted = counts_pdf["count"]

        to_send_danmakus = danmaku_sorted.to_list()[:send_count]
        to_send_counts = counts_sorted.to_list()[:send_count]

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

        return {"fig":fig, "origin_data":{"showinfos":to_send_danmakus, "counts":to_send_counts}}

    def username_static(self, normalize: bool=False, send_count:int=100, plot_top:int=10):

        """
        对发送弹幕的用户id信息进行提取的函数。
        normalize: 是否对数据进行百分比处理
        plot_top: 统计结果中希望表现出的个数
        """
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        username_data = data["username"]
        
        username_counts = username_data.value_counts(normalize=normalize)
        # danmaku_percents = danmaku_counts.values / np.sum(danmaku_counts.values)
        
        counts_pdf = username_counts.reset_index()
        counts_pdf.columns = ['context', 'count']

        username_sorted = counts_pdf["context"]
        counts_sorted = counts_pdf["count"]

        to_send_usernames = username_sorted.to_list()[:send_count]
        to_send_counts = counts_sorted.to_list()[:send_count]

        # 对用户名进行部分打码处理
        for list_index, username in enumerate(to_send_usernames):
            username_length = len(username)
            username_str_list = [i for i in username]
            
            # 将第一个字符和最后一个字符打码
            username_str_list[0] = "*"
            username_str_list[-1] = "*"

            # 如果用户名称总数大于5，则将其中间的一个字符也打码
            if username_length > 5:
                mid_index = int(username_length/2)
                username_str_list[mid_index] = "*"
            
            final_username = "".join(username_str_list)
            to_send_usernames[list_index] = final_username

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

        return {"fig":fig, "origin_data":{"showinfos":to_send_usernames, "counts":to_send_counts}}
    
    def dynamic_update(self, update_interval:int):
        # 该方法在后续的完善的统计历史中可能会用到，但是目前的更新方式暂时不需要用到此方法
        """update_interval: 子进程更新的频率，以分钟为单位"""
        sleep_interval = 60*update_interval/5
        while True:
            with open(self.update_json_file) as f:
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

    def normal_update(self,
                      update_info_name:str,
                      timeunit:str, 
                      timevalue,
                      info_count:int=100):
        
        assert update_info_name in self.avail_info
        assert timeunit in ["days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"]
        
        status_file_path = f"stats/{self.update_room_name}/{update_info_name}_data_{timevalue}{timeunit}.json"
        update_dict = {"danmaku":self.context_static,
                       "username":self.username_static}
        update_function = update_dict[update_info_name]

        now_time = datetime.datetime.now()

        with open(self.update_json_file) as f:
            interval_dict = json.load(f)
            str_time = interval_dict[update_info_name][f"{timevalue}{timeunit}"]
            if str_time == "":    # 如果之前从未更新过，将更新时间划为一千年前来确保能够在后续过程中判断为更新
                str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime("%Y-%m-%d-%H-%M-%S")

            last_update = datetime.datetime.strptime(str_time, "%Y-%m-%d-%H-%M-%S")
        
        now_interval = now_time - last_update

        # 此处判断应该更新的条件，并执行更新操作
        if now_interval > eval(f"datetime.timedelta({timeunit}={timevalue})")/10 and now_interval > datetime.timedelta(seconds=10):    # 判断更新时间和现在的时间间隔，如果大于指定时间间隔就发生更新，并将更新时间重写入config文件中
            eval(f"self.get_by_time({timeunit}={timevalue})")
            new_results = update_function(normalize=False,
                                           send_count=info_count)
            
            interval_dict[update_info_name][f"{timevalue}{timeunit}"] = now_time.strftime("%Y-%m-%d-%H-%M-%S")
            
            # 写入状态存储文件。此处保存的手段是直接覆盖之前的结果，因为更新不是实时的，所以保留历史记录也没太大意义
            with open(status_file_path, "w+") as ff:
                ff.write(json.dumps(new_results["origin_data"]))

            # new_results["fig"].savefig(f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png")

            with open(self.update_room_name, "w+") as fff:
                fff.write(json.dumps(interval_dict))
            
            last_update = now_time
        
        # 无论是否更新，都应该读取对应的状态存储文件，并提取信息
        with open(status_file_path) as f4:
            message = json.load(f4)
        
        all_message = {"data_status":"Full Pass.",
                       "data_info_name":update_info_name,
                       "origin_data":message, 
                       "last_update":last_update.strftime("%Y-%m-%d %H:%M:%S"), 
                       "fig":f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png"}

        return all_message
