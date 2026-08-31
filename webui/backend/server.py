import json
import logging
import os
import sys
import time
from pathlib import Path

import flask
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 用文件位置锚定路径，保证无论从哪个目录启动都能找到依赖包
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from tools.danmaku_static import DanmakuStats
from tools.username_static import UsernameStats
from tools.desuwa import DesuwaStats
from tools.zywoo import ZywooStats
from tools.data_filter import TIME_UNITS

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

server = flask.Flask(__name__, static_url_path='', static_folder='static', template_folder='template')

# 简单的内存限流；uWSGI 多进程下各进程独立计数，如需精确控制可换用共享存储（如 memcached/redis）
limiter = Limiter(
    get_remote_address,
    app=server,
    default_limits=["10 per second", "500 per hour"],
)

ROOM_CONFIG_PATH = BACKEND_DIR / "configs" / "avail_room.json"
ROOM_CACHE_TTL = 60
_room_dict = None
_room_dict_loaded_at = 0.0

# 配置 FORCE_UPDATE_TOKEN 环境变量后，force 接口需要携带 token（body 的 token 字段或 X-Force-Token 请求头）
FORCE_UPDATE_TOKEN = os.environ.get("FORCE_UPDATE_TOKEN", "")

SPECIAL_ROOM_ID = "6979222"

STATS_CLASSES = {
    "username": UsernameStats,
    "danmaku": DanmakuStats,
}


def _get_avail_rooms() -> dict:
    global _room_dict, _room_dict_loaded_at
    now = time.time()
    if _room_dict is None or now - _room_dict_loaded_at > ROOM_CACHE_TTL:
        with open(ROOM_CONFIG_PATH, "r", encoding="utf-8") as f:
            _room_dict = json.load(f)
        _room_dict_loaded_at = now
    return _room_dict


def _is_special_room(platform, room_id) -> bool:
    return platform == "douyu" and str(room_id) == SPECIAL_ROOM_ID


def _force_token_ok() -> bool:
    """未配置 FORCE_UPDATE_TOKEN 时保持原有开放行为，配置后强制校验 token。"""
    if not FORCE_UPDATE_TOKEN:
        return True
    token = (request.json or {}).get("token") or request.headers.get("X-Force-Token")
    return token == FORCE_UPDATE_TOKEN


@server.errorhandler(404)    # 重定向404界面
def demo4(e):
    return "404 ERROR!"


@server.route('/', methods=["GET"])
def index():
    return "<h1> This is the api of danmaku project</h1>"


@server.route("/check", methods=["POST"])
def check_room_exist():
    payload = request.json or {}
    platform = payload.get('platform')
    room_id = payload.get('room_id')

    room_dict = _get_avail_rooms()
    rooms = room_dict.get(platform, {})

    if str(room_id) in rooms:
        return jsonify({"message": "yes"})
    else:
        return jsonify({"message": "no"})


@server.route("/get_by_time", methods=["POST"])
def time_mes():
    payload = request.json or {}
    platform = payload.get('platform')
    room_id = payload.get('room_id')
    update_info_name = payload.get('info_name')
    timeunit = payload.get('timeunit')
    timevalue = payload.get('timevalue')
    info_count = payload.get('info_count')

    if not platform or room_id is None:
        return jsonify({"data_status": "Invalid parameters."})
    if timeunit not in TIME_UNITS or timevalue is None:
        return jsonify({"data_status": "Invalid time range."})

    StaticClass = STATS_CLASSES.get(update_info_name)
    if StaticClass is None:
        return jsonify({"data_status": "Update Info Name is invaild."})

    try:
        message = StaticClass(platform, room_id).normal_update(
            update_info_name=update_info_name,
            timeunit=timeunit,
            timevalue=timevalue,
            info_count=info_count,
        )
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    except FileNotFoundError:
        return jsonify({"data_status": "Data not ready."})
    except (ValueError, KeyError) as e:
        return jsonify({"data_status": str(e) or "No Avail Data in This Time Range."})

    return jsonify(message)


@server.route("/desuwa", methods=["POST"])
def desuwa_mes():
    payload = request.json or {}
    if not _is_special_room(payload.get('platform'), payload.get('room_id')):
        return jsonify({"data_status": "Desuwa not support this live room."})

    try:
        message = DesuwaStats("douyu", SPECIAL_ROOM_ID).run_send(
            timevalue=payload.get('timevalue'), timeunit=payload.get('timeunit'))
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    except (ValueError, KeyError) as e:
        return jsonify({"data_status": str(e)})

    return jsonify(message)


@server.route("/zywoo", methods=["POST"])
def Zywoo_mes():
    payload = request.json or {}
    if not _is_special_room(payload.get('platform'), payload.get('room_id')):
        return jsonify({"data_status": "Zywoo not support this live room."})

    try:
        message = ZywooStats("douyu", SPECIAL_ROOM_ID).run_send(
            timevalue=payload.get('timevalue'), timeunit=payload.get('timeunit'))
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    except (ValueError, KeyError) as e:
        return jsonify({"data_status": str(e)})

    return jsonify(message)


@server.route("/desuwa_force", methods=["POST"])
def desuwa_force():
    if not _force_token_ok():
        return jsonify({"data_status": "Forbidden."}), 403

    payload = request.json or {}
    if not _is_special_room(payload.get('platform'), payload.get('room_id')):
        return jsonify({"data_status": "Desuwa not support this live room."})

    try:
        message = DesuwaStats("douyu", SPECIAL_ROOM_ID).force_update(
            timevalue=payload.get('timevalue'), timeunit=payload.get('timeunit'))
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    except (ValueError, KeyError) as e:
        return jsonify({"data_status": str(e)})

    return jsonify(message)


@server.route("/zywoo_force", methods=["POST"])
def zywoo_force():
    if not _force_token_ok():
        return jsonify({"data_status": "Forbidden."}), 403

    payload = request.json or {}
    if not _is_special_room(payload.get('platform'), payload.get('room_id')):
        return jsonify({"data_status": "Zywoo not support this live room."})

    try:
        message = ZywooStats("douyu", SPECIAL_ROOM_ID).force_update(
            timevalue=payload.get('timevalue'), timeunit=payload.get('timeunit'))
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    except (ValueError, KeyError) as e:
        return jsonify({"data_status": str(e)})

    return jsonify(message)


if __name__ == '__main__':
    logging.info("Start Main Process.")
    server.run('127.0.0.1', 8083, debug=False)
