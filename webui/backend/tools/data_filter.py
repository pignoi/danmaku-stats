# 定义基本的统计方法，能够方便地访问数据库并返回便于后期处理的数值

import datetime
import json
import logging
import os
import threading
from pathlib import Path

import fcntl
import pandas as pd

from basetools.db_manager import LiveDatabase

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 使用文件所在位置锚定配置/统计目录，避免依赖启动时的工作目录
BACKEND_DIR = Path(__file__).resolve().parents[1]
CONFIGS_DIR = BACKEND_DIR / "configs"
STATS_DIR = BACKEND_DIR / "stats"

UPDATE_TIME_FMT = "%Y-%m-%d-%H-%M-%S"
RESPONSE_TIME_FMT = "%Y-%m-%d %H:%M:%S"
TIME_UNITS = ("days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks")


def _read_json_locked(path) -> dict:
    """带共享锁读取 JSON 配置文件。"""
    with open(path, "r", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _write_json_locked(path, data) -> None:
    """带排他锁覆盖写入 JSON 配置文件（文件必须已存在）。"""
    with open(path, "r+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        f.truncate()
        json.dump(data, f)
        f.flush()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path, data) -> None:
    """先写临时文件再原子替换，避免读取方看到写了一半的 JSON。"""
    path = Path(path)
    tmp_path = path.with_name(f".{path.name}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
    os.replace(tmp_path, path)


# 对相同一组数据库进行不同时间粒度以及角度的提取及分析，并生成对应的小文件供前端使用
class GenStats:
    def __init__(self, platform: str,
                 room_id,
                 avail_info: str,
                 info_sheet_name: str,
                 update_times: dict = None):

        """
        :param platform: 统计的平台
        :param room_id: 房间号
        :param avail_info: 筛选的统计变量名称，这个可以是自定义的，只用于规定存储信息当中名称
        :param info_sheet_name: 从数据库的哪一种表当中提取信息
        :param update_times: 可以更新的时间尺度字典
        """

        if update_times is None:
            update_times = {"10seconds": "", "30seconds": "", "1minutes": "", "2minutes": "",
                            "5minutes": "", "30minutes": "", "600minutes": "", "history": ""}

        self.update_room_name = f"{platform}_{room_id}"
        self.update_json_file = CONFIGS_DIR / f"{self.update_room_name}_update.json"
        # 设置可以统计的变量名称
        self.avail_info = avail_info
        self.info_sheet_name = info_sheet_name
        # 设置可以访问的统计时间区间
        self.avail_update_times = update_times

        self.static_data = pd.DataFrame()

        self.rood_db = LiveDatabase(platform, room_id, collect_mode=False, flit_table=self.info_sheet_name)

        # 登记当前统计类型的时间刻度，文件锁内完成读-改-写
        CONFIGS_DIR.mkdir(exist_ok=True)
        if not self.update_json_file.exists():
            self.update_json_file.write_text("{}", encoding="utf-8")
        self._ensure_update_times()

        self.stats_dir = STATS_DIR / self.update_room_name
        self.stats_dir.mkdir(parents=True, exist_ok=True)

        self._dynamic_running = False
        self.dynamic_thread = None

    def _ensure_update_times(self) -> None:
        """把当前统计类型对应的更新时间刻度登记进配置文件。"""
        with open(self.update_json_file, "r+", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.seek(0)
            try:
                interval_dict = json.load(f)
            except json.JSONDecodeError:
                interval_dict = {}
            f.seek(0)
            f.truncate()
            interval_dict.setdefault(self.avail_info, {})
            for update_time in self.avail_update_times:
                interval_dict[self.avail_info].setdefault(update_time, "")
            json.dump(interval_dict, f)
            f.flush()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _read_update_times(self) -> dict:
        return _read_json_locked(self.update_json_file)

    def _set_update_time(self, time_key: str, value_str: str) -> None:
        """在排他锁内更新当前统计类型某个时间刻度的更新时间。"""
        with open(self.update_json_file, "r+", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.seek(0)
            interval_dict = json.load(f)
            f.seek(0)
            f.truncate()
            interval_dict.setdefault(self.avail_info, {})[time_key] = value_str
            json.dump(interval_dict, f)
            f.flush()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def init_dynamic_update(self,
                            timevalue: int,
                            timeunit: str):

        self.update_timevalue = timevalue
        self.update_timeunit = timeunit
        if f"{self.update_timevalue}{self.update_timeunit}" not in self.avail_update_times:
            raise ValueError(f"{self.update_timevalue}{self.update_timeunit} not in avail update times.")

        if not self._dynamic_running:
            logging.info(f"Start the dynamic update method of {self.update_timevalue}{self.update_timeunit}.")

            self._dynamic_running = True
            self.dynamic_thread = threading.Thread(target=self.dynamic_update, daemon=True)
            self.dynamic_thread.start()

    def get_static_data(self, **kwargs):
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

        self.rood_db.para_time(now_time-time_delta, now_time)
        self.static_data = self.rood_db.select_run()

    def sort_by_arg(self, arg_name: str):
        pass

    def update_function(self, normalize_bool: bool = False, send_count: int = 100, plot_top: int = 10) -> dict:
        """
        通用统计：对弹幕文本和用户名分别计数，返回各自的 TopN。
        desuwa/zywoo 等需要同时统计两类信息的子类直接复用此方法。
        """

        if self.static_data.empty:
            return {"fig": "", "origin_data": {"showinfos": [[], []], "counts": [[], []]}}

        data = self.static_data
        danmaku_counts = data["context"].value_counts(normalize=normalize_bool).head(send_count)
        userinfo_counts = data["username"].value_counts(normalize=normalize_bool).head(send_count)

        return {
            "fig": None,
            "origin_data": {
                "showinfos": [danmaku_counts.index.to_list(), userinfo_counts.index.to_list()],
                "counts": [danmaku_counts.to_list(), userinfo_counts.to_list()],
            },
        }

    def _coerce_timevalue(self, timevalue):
        try:
            return int(timevalue)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid timevalue: {timevalue}")

    def normal_update(self,
                      update_info_name: str,    # 这个变量后续或许可以考虑去掉，没有实际的价值了
                      timeunit: str,
                      timevalue,
                      info_count: int = 100):

        """访问的行为促进更新的方法，能够保证数据在访问的时候是最新的。"""

        if update_info_name != self.avail_info:
            raise ValueError("Update Info Name is invalid.")
        if timeunit not in TIME_UNITS:
            raise ValueError(f"Invalid timeunit: {timeunit}")
        timevalue = self._coerce_timevalue(timevalue)
        time_key = f"{timevalue}{timeunit}"
        if time_key not in self.avail_update_times:
            raise ValueError(f"Invalid time range: {time_key}")
        try:
            info_count = int(info_count) if info_count else 100
        except (TypeError, ValueError):
            info_count = 100

        # 对应信息下的时间尺度的信息存储文件位置
        status_file_path = self.stats_dir / f"{self.avail_info}_data_{time_key}.json"

        now_time = datetime.datetime.now()
        interval_dict = self._read_update_times()
        str_time = interval_dict[self.avail_info].get(time_key, "")
        if not str_time:
            # 如果之前从未更新过，将更新时间划为一千年前来确保能够在后续过程中判断为更新
            str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime(UPDATE_TIME_FMT)
        last_update = datetime.datetime.strptime(str_time, UPDATE_TIME_FMT)

        now_interval = now_time - last_update
        update_interval = datetime.timedelta(**{timeunit: timevalue})

        # 此处判断应该更新的条件，并执行更新操作
        if now_interval > update_interval / 10 and now_interval > datetime.timedelta(seconds=60):
            self.get_static_data(**{timeunit: timevalue})
            new_results = self.update_function(normalize_bool=False, send_count=info_count)

            # 原子写入状态文件，避免读端拿到写了一半的 JSON
            _atomic_write_json(status_file_path, new_results["origin_data"])
            self._set_update_time(time_key, now_time.strftime(UPDATE_TIME_FMT))
            last_update = now_time

        # 无论是否更新，都应该读取对应的信息存储文件，并提取信息
        with open(status_file_path, "r", encoding="utf-8") as f4:
            message = json.load(f4)

        return {
            "data_status": "Full Pass.",
            "data_info_name": self.avail_info,
            "origin_data": message,
            "last_update": last_update.strftime(RESPONSE_TIME_FMT),
            "fig": f"stats/{self.update_room_name}/fig_{time_key}.png",
        }

    def dynamic_update(self):
        """动态实时更新的方法，可以固定时间进行更新。"""
        # 将输入的更新间隔转化为python变量，如果大于一天则将更新时间定为1天
        update_interval = datetime.timedelta(**{self.update_timeunit: self.update_timevalue})
        if update_interval > datetime.timedelta(days=1):
            update_interval = datetime.timedelta(days=1)

        if update_interval >= datetime.timedelta(days=0.5):
            sleep_interval = (update_interval/20).total_seconds()
        elif update_interval >= datetime.timedelta(hours=1):
            sleep_interval = (update_interval/10).total_seconds()
        else:
            sleep_interval = update_interval.total_seconds()

        time_key = f"{self.update_timevalue}{self.update_timeunit}"
        status_file_path = self.stats_dir / f"{self.avail_info}_data_{time_key}.json"

        while self._dynamic_running:
            now_time = datetime.datetime.now()
            interval_dict = self._read_update_times()
            str_time = interval_dict[self.avail_info].get(time_key, "")
            if not str_time:
                str_time = (now_time - datetime.timedelta(days=int(365*1000))).strftime(UPDATE_TIME_FMT)
            last_update = datetime.datetime.strptime(str_time, UPDATE_TIME_FMT)

            now_interval = (now_time - last_update)

            # 如果现有的时间间隔大于预定的时间间隔，对信息进行更新
            if now_interval >= update_interval:
                logging.info(f"Dynamic update the {time_key} data.")
                self.get_static_data(**{self.update_timeunit: self.update_timevalue})
                new_results = self.update_function(normalize_bool=False, send_count=100)

                # 原子写入状态文件
                _atomic_write_json(status_file_path, new_results["origin_data"])
                # 时间记录在锁内完成读-改-写，避免并发丢失更新
                self._set_update_time(time_key, now_time.strftime(UPDATE_TIME_FMT))
                last_update = now_time
            else:
                logging.info(f"The {time_key} data have not updated.")

            time.sleep(sleep_interval)

    # 强制更新的函数
    def force_update(self,
                     timeunit: str,
                     timevalue,
                     info_count: int = 100):

        if timeunit not in TIME_UNITS:
            raise ValueError(f"Invalid timeunit: {timeunit}")
        timevalue = self._coerce_timevalue(timevalue)
        time_key = f"{timevalue}{timeunit}"
        if time_key not in self.avail_update_times:
            raise ValueError(f"Invalid time range: {time_key}")
        try:
            info_count = int(info_count) if info_count else 100
        except (TypeError, ValueError):
            info_count = 100

        now_time = datetime.datetime.now()
        status_file_path = self.stats_dir / f"{self.avail_info}_data_{time_key}.json"

        logging.info(f"Force updating the {time_key} data.")
        self.get_static_data(**{timeunit: timevalue})
        new_results = self.update_function(normalize_bool=False, send_count=info_count)

        _atomic_write_json(status_file_path, new_results["origin_data"])
        self._set_update_time(time_key, now_time.strftime(UPDATE_TIME_FMT))

        return {
            "data_status": "Full Pass.",
            "data_info_name": self.avail_info,
            "origin_data": new_results["origin_data"],
            "last_update": now_time.strftime(RESPONSE_TIME_FMT),
            "fig": f"stats/{self.update_room_name}/fig_{time_key}.png",
        }

    def run_send(self,
                 timevalue: str,
                 timeunit: str):
        """直接发送信息的函数。"""

        time_key = f"{timevalue}{timeunit}"
        status_file_path = self.stats_dir / f"{self.avail_info}_data_{time_key}.json"

        # 数据尚未生成时返回友好状态，而不是抛 FileNotFoundError 导致 500
        if not status_file_path.exists():
            return {
                "data_status": "Data not ready.",
                "data_info_name": self.avail_info,
                "origin_data": {"showinfos": [[], []], "counts": [[], []]},
                "last_update": "",
            }

        with open(status_file_path, "r", encoding="utf-8") as f4:
            message = json.load(f4)

        interval_dict = self._read_update_times()
        if time_key not in interval_dict.get(self.avail_info, {}):
            raise KeyError(f"{time_key} not in plan.")
        last_update = datetime.datetime.strptime(interval_dict[self.avail_info][time_key], UPDATE_TIME_FMT)

        return {
            "data_status": "Full Pass.",
            "data_info_name": self.avail_info,
            "origin_data": message,
            "last_update": last_update.strftime(RESPONSE_TIME_FMT),
            "fig": f"stats/{self.update_room_name}/fig_{time_key}.png",
        }
