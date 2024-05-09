from bilibili_api import live, sync
from bilibili_api import Credential
from db_manager import live_database
import json
import os
import datetime

class biliDanmaku:
    def __init__(self, room_id):
        
        userinfo = json.load(open(os.environ.get("USERINFO")))
        credential = Credential(sessdata=userinfo["sessdata"],
                                bili_jct=userinfo["bili_jct"],
                                buvid3=userinfo["buvid3"],
                                dedeuserid=userinfo["dedeuserid"])

        self.room = live.LiveDanmaku(room_id, credential=credential)
        room_db = live_database("bilibili", room_id)

        @self.room.on('DANMU_MSG')
        async def on_danmaku(event):
            # 收到弹幕
            baseinfo = event["data"]["info"]

            content = json.loads(baseinfo[0][15]["extra"])["content"]
            username = baseinfo[0][15]["user"]["base"]["name"]

            origin_time = float(f"{baseinfo[0][4]/1000:.3f}")
            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
            
            room_db.insert((std_time, username, content, json.dumps(event)))
    
    def start(self):
        sync(self.room.connect())
