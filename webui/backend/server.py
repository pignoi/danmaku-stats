import sys
sys.path.append("../../")

import flask
import os 
import time
import json
from flask import request, redirect, abort, jsonify

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from tools.data_filter import GenStats

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
    with open("static/index.html") as f:
        return "".join(f.readlines())


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
    timeunit = request.json.get('timeunit')
    timevalue = request.json.get('timevalue')

    try:
        StaticClass = GenStats(platform, room_id)
        message = StaticClass.normal_update(timeunit=timeunit, timevalue=timevalue)

        return message
    
    except FileExistsError:
        return jsonify({"data_status": "Live Room not Exist."})
    
    except ValueError:
        return jsonify({"data_status": "No Avail Data in This Time Range."})



if __name__ == '__main__':

    server.run('127.0.0.1', 8083, debug=True)
