import os
import argparse
from platforms.bilibili import biliDanmaku
from platforms.douyu import douyuDanmaku

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--platform', dest="platform", default="bilibili", type=str, help='set platform.')
parser.add_argument('-r', '--room', dest="room_id", default=3044248, type=int, help='set room id.')

# 非docker生产环境下设置指定的环境变量，在docker环境中则自动识别为Dockerfile中设置的变量，同时满足程序调试和生产环境
try:
    os.environ["IS_DOCKER"] == None
except KeyError:
    os.environ["USERINFO"] = os.path.join(os.path.dirname(__file__), "..", "userinfo.json")
    os.environ["DB_PATH"] = os.path.join(os.path.dirname(__file__), "..", "dbs")

args = parser.parse_args()
platform = args.platform
room_id = args.room_id

if __name__ == "__main__":

    if platform == "bilibili":
        room_class = biliDanmaku(room_id)
    
    if platform == "douyu":
        room_class = douyuDanmaku(room_id)

    room_class.start()
