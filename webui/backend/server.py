import sys
sys.path.append("../../")

import flask
import os 
import time
import json
from flask import request,redirect, abort, jsonify
from wsgiref.simple_server import make_server

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from tools.data_filter import GenStats

def ip_user():     # 获取访问者的ip以及useragent，判断是否在ban的范围之内，如果是返回值为0，后面会禁止访问
    with open(".banned_ip") as f:
        ip_lines = f.readlines()
    ip_ban = [i.split("\n")[0] for i in ip_lines]
    agent_ban = ["python-requests","Python-urllib","Go-http-client"]

    ip_add = request.remote_addr
    user_a = request.headers.get("User-Agent")

    if (ip_add in ip_ban):
        return 0
    else:
        for single_user in agent_ban:
            if single_user in user_a:
                return 0
        return 1

def allow_f(filename):
    all_list = ['png','jpg','jpeg','docx','doc','xls','xlsx','ppt','pptx','pdf','html','py','c','zip','']
    file_type = filename.split('.')[-1]
    if file_type in all_list:
        return 1
    else:
        return 1


interface_path = os.path.dirname(__file__)
sys.path.insert(0, interface_path)
server = flask.Flask(__name__,static_url_path='',static_folder='static',template_folder='template')

# limiter = Limiter(
# server,
# key_func=get_remote_address,
# default_limits=["10 per second", "500 per hour"],
# storage_uri="memcached://0.0.0.0:11211",
# storage_options={})

@server.errorhandler(404)    # 重定向404界面
def demo4(e):
    # ip_toban = request.remote_addr
    # with open(".banned_ip","a+") as f:
    #     f.seek(0)
    #     alban = f.readlines()
    #     if f"{ip_toban}\n" in alban:
    #         pass
    #     else:
    #         f.seek(0)
    #         f.write(f"{ip_toban}\n")
    return "404 ERROR!"

@server.errorhandler(429)    # 短时间内访问此数过多会重定向至429界面，然后加入黑名单
def demo429(e):
    ip_toban = request.remote_addr
    with open(".banned_ip","a+") as f:
        f.seek(0)
        alban = f.readlines()
        if f"{ip_toban}\n" in alban:
            pass
        else:
            f.seek(0)
            f.write(f"{ip_toban}\n")
    
    return redirect("https://bing.com")

@server.route('/', methods=["GET"])
def index():
    check = ip_user()
    if check == 1:
        with open("static/index.html") as f:
            return "".join(f.readlines())
    else:
        abort(404)

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

    StaticClass = GenStats(platform, room_id)

    message = StaticClass.normal_update(timeunit=timeunit, timevalue=timevalue)

    return message

if __name__ == '__main__':

    server.run('127.0.0.1', 8083, debug=True)