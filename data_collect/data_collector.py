import sys
sys.path.append("../")

import os
import argparse
from platforms.bilibili import biliDanmaku
from platforms.douyu import douyuDanmaku

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--platform', dest="platform", default="bilibili", type=str, help='set platform.')
parser.add_argument('-r', '--room', dest="room_id", default=3044248, type=int, help='set room id.')
parser.add_argument('-g', '--accept_gift', dest="accept_gift", default="False", type=str, help='set accept gift message or not.')

# 非docker生产环境下设置指定的环境变量，在docker环境中则自动识别为Dockerfile中设置的变量，同时满足程序调试和生产环境
try:
    os.environ["IS_DOCKER"] == None
except KeyError:
    os.environ["USERINFO"] = os.path.join(os.path.dirname(__file__), "..", "userinfo.json")
    os.environ["DB_PATH"] = os.path.join(os.path.dirname(__file__), "..", "dbs")

args = parser.parse_args()
platform = args.platform
room_id = args.room_id
accept_gift = args.accept_gift

# from BASH bool to PYTHON bool type
if accept_gift == "False" or accept_gift == "false":
    accept_gift = False
elif accept_gift == "True" or accept_gift == "true":
    accept_gift = True
else:
    raise ValueError("accept gift must be True or False.")

if __name__ == "__main__":

    if platform == "bilibili":
        room_class = biliDanmaku(room_id, accept_gift)
    
    if platform == "douyu":
        room_class = douyuDanmaku(room_id, accept_gift)

    room_class.start()
