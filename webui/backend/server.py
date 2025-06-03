import sys
sys.path.append("../../")

import flask
import os 
import time
import json
from flask import request, redirect, abort, jsonify

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from tools.danmaku_static import DanmakuStats
from tools.username_static import UsernameStats

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
        if update_info_name == "username":
            StaticClass = UsernameStats(platform, room_id)
            message = StaticClass.normal_update(update_info_name=update_info_name, timeunit=timeunit, timevalue=timevalue, info_count=info_count)
        elif update_info_name == "danmaku":
            StaticClass = DanmakuStats(platform, room_id)
            message = StaticClass.normal_update(update_info_name=update_info_name, timeunit=timeunit, timevalue=timevalue, info_count=info_count)
        elif update_info_name == "desuwa":
            
            raise NotImplementedError
        else:
            return {"data_status":"Update Info Name is invaild."}
        
        

        return message
    
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    
    except ValueError:
        return jsonify({"data_status": "No Avail Data in This Time Range."})

if __name__ == '__main__':

    server.run('127.0.0.1', 8083, debug=True)
