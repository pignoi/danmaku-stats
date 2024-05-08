from bilibili_api import live, sync
from bilibili_api import Credential
from db_manager import live_database
import json
import os
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--platform', dest="platform", default="bilibili", type=str, help='set platform.')
parser.add_argument('-r', '--room', dest="room_id", default=3044248, type=int, help='set room id.')

# os.environ["USERINFO"]="/home/webapp/danmaku-stats/data_collect/userinfo.json"
# os.environ["DB_PATH"]="/home/webapp/danmaku-stats/dbs"
userinfo = json.load(open(os.environ.get("USERINFO")))
credential = Credential(sessdata=userinfo["sessdata"],
                        bili_jct=userinfo["bili_jct"],
                        buvid3=userinfo["buvid3"],
                        dedeuserid=userinfo["dedeuserid"])

args = parser.parse_args()
platform = args.platform
room_id = args.room_id
room = live.LiveDanmaku(room_id, credential=credential)
room_db = live_database("bilibili", room_id)

@room.on('DANMU_MSG')
async def on_danmaku(event):
    # 收到弹幕
    baseinfo = event["data"]["info"]

    content = json.loads(baseinfo[0][15]["extra"])["content"]
    username = baseinfo[0][15]["user"]["base"]["name"]

    origin_time = float(f"{baseinfo[0][4]/1000:.3f}")
    std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
    
    room_db.insert((std_time, username, content, json.dumps(event)))

sync(room.connect())
