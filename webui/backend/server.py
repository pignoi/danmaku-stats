import sys
sys.path.append("../../")
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import flask
import os 
import time
import json
from flask import request, redirect, abort, jsonify

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from tools.danmaku_static import DanmakuStats
from tools.username_static import UsernameStats
from tools.desuwa import DesuwaStats
from webui.backend.tools.zywoo import ZywooStats

interface_path = os.path.dirname(__file__)
sys.path.insert(0, interface_path)
server = flask.Flask(__name__,static_url_path='',static_folder='static', template_folder='template')

# limiter = Limiter(
# server,
# key_func=get_remote_address,
# default_limits=["10 per second", "500 per hour"],
# storage_uri="memcached://0.0.0.0:11211",
# storage_options={})

@server.errorhandler(404)    # 重定向404界面
def demo4(e):
    return "404 ERROR!"

@server.route('/', methods=["GET"])
def index():
    # with open("static/index.html") as f:
    #     return "".join(f.readlines())
    return "<h1> This is the api of danmaku project</h1>"

@server.route("/check", methods=["POST"])
def check_room_exist():
    platform = request.json.get('platform')
    room_id = request.json.get('room_id')

    with open("configs/avail_room.json") as f:
        room_dict = json.load(f)

    if str(room_id) in room_dict[platform]:
        return jsonify({"message": "yes"})
    else:
        return jsonify({"message": "no"})

@server.route("/get_by_time", methods=["POST"])
def time_mes():
    platform = request.json.get('platform')
    room_id = request.json.get('room_id')
    update_info_name = request.json.get('info_name')
    timeunit = request.json.get('timeunit')
    timevalue = request.json.get('timevalue')
    info_count = request.json.get('info_count')

    try:
        # 正常的"data_status"的返回值为"Full Pass."
        if update_info_name == "username":
            StaticClass = UsernameStats(platform, room_id)
            message = StaticClass.normal_update(update_info_name=update_info_name, timeunit=timeunit, timevalue=timevalue, info_count=info_count)
        elif update_info_name == "danmaku":
            StaticClass = DanmakuStats(platform, room_id)
            message = StaticClass.normal_update(update_info_name=update_info_name, timeunit=timeunit, timevalue=timevalue, info_count=info_count)
        else:
            return {"data_status":"Update Info Name is invaild."}
        
        return message
    
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    
    except ValueError:
        return jsonify({"data_status": "No Avail Data in This Time Range."})

@server.route("/desuwa", methods=["POST"])
def desuwa_mes():
    platform = request.json.get('platform')
    room_id = request.json.get('room_id')
    timeunit = request.json.get('timeunit')
    timevalue = request.json.get('timevalue')

    if platform == "douyu" and str(room_id) == "6979222":
        StaticClass = DesuwaStats(platform, room_id)
        message = StaticClass.run_send(timevalue=timevalue, timeunit=timeunit)

        return message

    else:
        return jsonify({"data_status": "Desuwa not support this live room."})

@server.route("/zywoo", methods=["POST"])
def Zywoo_mes():
    platform = request.json.get('platform')
    room_id = request.json.get('room_id')
    timeunit = request.json.get('timeunit')
    timevalue = request.json.get('timevalue')

    if platform == "douyu" and str(room_id) == "6979222":
        StaticClass = ZywooStats(platform, room_id)
        message = StaticClass.run_send(timevalue=timevalue, timeunit=timeunit)

        return message

    else:
        return jsonify({"data_status": "Zywoo not support this live room."})

@server.route("/desuwa_force", methods=["POST"])
def desuwa_force():
    platform = request.json.get('platform')
    room_id = request.json.get('room_id')
    timeunit = request.json.get('timeunit')
    timevalue = request.json.get('timevalue')

    if platform == "douyu" and str(room_id) == "6979222":
        StaticClass = DesuwaStats(platform, room_id)
        message = StaticClass.force_update(timevalue=timevalue, timeunit=timeunit)

        return message

    else:
        return jsonify({"data_status": "Desuwa not support this live room."})

### 这里是问deepseek给的方案，试了一下不太行，还是用手动多线程吧，这个后面可以再探索下
# try:
#     import uwsgi
#     @uwsgi.postfork
#     def postfork():

#         DesuwaHistory = DesuwaStats(platform="douyu", room_id="6979222")
#         DesuwaHistory.init_update(timevalue=100000, timeunit="days")
        
#         Desuwa1Day= DesuwaStats(platform="douyu", room_id="6979222")
#         Desuwa1Day.init_update(timevalue=1, timeunit="days")

#         Desuwa10s= DesuwaStats(platform="douyu", room_id="6979222")
#         Desuwa10s.init_update(timevalue=10, timeunit="seconds")
# except:
#     pass

if __name__ == '__main__':

    # DesuwaHistory = DesuwaStats(platform="douyu", room_id="6979222")
    # DesuwaHistory.init_update(timevalue=100000, timeunit="days")
    
    # Desuwa1Day= DesuwaStats(platform="douyu", room_id="6979222")
    # Desuwa1Day.init_update(timevalue=1, timeunit="days")

    # Desuwa10s= DesuwaStats(platform="douyu", room_id="6979222")
    # Desuwa10s.init_update(timevalue=10, timeunit="seconds")

    logging.info("Start Main Process.")
    server.run('127.0.0.1', 8083, debug=False)
