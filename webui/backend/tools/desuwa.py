import threading
import datetime, time
import json
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import portalocker
import gc

import numpy as np

from .data_filter import GenStats

class DesuwaStats(GenStats):
    def __init__(self, platform: str, room_id):

        avail_info = "desuwa"
        update_times = {"1hours":"","1days":"", "100000days":""}
        info_sheet_name = "danmaku"

        super().__init__(platform, room_id, avail_info, info_sheet_name, update_times)

        self._running = False
        self.thread = None

    def init_update(self,
                    timevalue:int, 
                    timeunit:str):
        
        self.update_timevalue = timevalue
        self.update_timeunit = timeunit
        assert f"{self.update_timevalue}{self.update_timeunit}" in self.avail_update_times

        if not self._running:
            logging.info(f"Start the dynamic update method of {self.update_timevalue}{self.update_timeunit}.")
            
            self._running = True
            self.thread = threading.Thread(target=self.dynamic_update)
            self.thread.setDaemon(True)  # 设置为守护线程，主程序退出时自动结束
            self.thread.start()

    def update_function(self, normalize: bool=False, send_count:int=100, plot_top:int=10):

        """
        对弹幕的文本信息进行提取的函数。
        normalize: 是否对数据进行百分比处理
        plot_top: 统计结果中希望表现出的个数
        """
        
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        danmaku_data = data["context"]
        userinfo_data = data["username"]

        desuwa_filter = danmaku_data.str.contains("desuwa")

        danmaku_data = danmaku_data[desuwa_filter]
        userinfo_data = userinfo_data[desuwa_filter]

        # 对desuwa弹幕信息和发送desuwa弹幕的神人id进行计数和后处理 
        danmaku_counts = danmaku_data.value_counts(normalize=normalize)
        userinfo_counts = userinfo_data.value_counts(normalize=normalize)
        
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

    def dynamic_update(self):
        # 将输入的更新间隔转化为python变量，如果大于一天则将更新时间定为1天
        update_interval = eval(f"datetime.timedelta({self.update_timeunit}={self.update_timevalue})")
        if update_interval > datetime.timedelta(days=1):
            update_interval = datetime.timedelta(days=1)
        
        sleep_interval = (update_interval/5).total_seconds()
        
        status_file_path = f"stats/{self.update_room_name}/{self.avail_info}_data_{self.update_timevalue}{self.update_timeunit}.json"
        
        while self._running:
            now_time = datetime.datetime.now()
            with open(self.update_json_file) as f:
                
                interval_dict = json.load(f)
                str_time = interval_dict[self.avail_info][f"{self.update_timevalue}{self.update_timeunit}"]
                if str_time == "":
                    str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime("%Y-%m-%d-%H-%M-%S")
                                
                try:
                    last_update = datetime.datetime.strptime(str_time, "%Y-%m-%d-%H-%M-%S")                    
                except ValueError:
                    raise ValueError("Format error.")
            
            now_interval = (now_time - last_update)
            
            # 如果现有的时间间隔大于预定的时间间隔，对信息进行更新
            if now_interval >= update_interval:
                time.sleep(np.random.randint(10))
                logging.info(f"Dynamic update the {self.update_timevalue}{self.update_timeunit} data.")
                eval(f"self.get_by_time({self.update_timeunit}={self.update_timevalue}, sheet_name='{self.info_sheet_name}')")    # 这里和update_interval做区分，能够确保获得的数据时间远点和更新是独立的
                new_results = self.update_function(normalize=False,
                                            send_count=100)
                
                # interval_dict[self.avail_info][f"{self.update_timevalue}{self.update_timeunit}"] = now_time.strftime("%Y-%m-%d-%H-%M-%S")
                
                # 写入状态存储文件。此处保存的手段是直接覆盖之前的结果，因为更新不是实时的，所以保留历史记录也没太大意义
                with open(status_file_path, "w") as ff:
                    ff.write(json.dumps(new_results["origin_data"]))

                # new_results["fig"].savefig(f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png")
                
                # 写入时间记录文件，因为这里涉及多线程对文件的操作，需要再加载一遍实时的结果进行保存
                with open(self.update_json_file, "r") as rfff:
                    after_update_interval_dict = json.load(rfff)
                    after_update_interval_dict[self.avail_info][f"{self.update_timevalue}{self.update_timeunit}"] = now_time.strftime("%Y-%m-%d-%H-%M-%S")
                
                with open(self.update_json_file, "w") as wfff:
                    wfff.write(json.dumps(after_update_interval_dict))
                
                last_update = now_time

            else:
                logging.info(f"The {self.update_timevalue}{self.update_timeunit} data have not updated.")

            time.sleep(sleep_interval)
    
    def run_send(self, 
                 timevalue: str,
                 timeunit:str):
        
        status_file_path = f"stats/{self.update_room_name}/{self.avail_info}_data_{timevalue}{timeunit}.json"

        # 访问时打开对应的信息存储文件，包括返回信息存储和时间状态存储
        with open(status_file_path) as f4:
            message = json.load(f4)
        
        with open(self.update_json_file) as f:
            interval_dict = json.load(f)
            try:
                last_update = \
                    datetime.datetime.strptime(interval_dict[self.avail_info][f"{timevalue}{timeunit}"], "%Y-%m-%d-%H-%M-%S")
            except KeyError:
                raise KeyError(f"{timevalue}{timeunit} not in plan.")
            except ValueError:
                raise ValueError("Format error.")
        
            if last_update == "":
                last_update = datetime.datetime.now()

        all_message = {"data_status":"Full Pass.",
                       "data_info_name":self.avail_info,
                       "origin_data":message, 
                       "last_update":last_update.strftime("%Y-%m-%d %H:%M:%S"), 
                       "fig":f"stats/{self.update_room_name}/fig_{timevalue}{timeunit}.png"}

        return  all_message

    # normal_update的函数应该还可以用
