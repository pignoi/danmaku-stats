from bilibili_api import live, sync, user
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
            
            username = baseinfo[0][15]["user"]["base"]["name"]
            uid = baseinfo[0][15]["user"]["uid"]

            # 检测是否为直播间表情弹幕
            if baseinfo[0][12] == 1:
                image_url = baseinfo[0][13]["url"]
                content = json.loads(baseinfo[0][15]["extra"])["content"] + f"({image_url})"
            else:
                content = json.loads(baseinfo[0][15]["extra"])["content"]
            
            origin_time = float(f"{baseinfo[0][4]/1000:.3f}")
            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
            
            try:
                fans_club = baseinfo[3][1]
                fans_level = baseinfo[3][0]
            except IndexError:
                fans_club = "无"
                fans_level = 0

            room_db.insert("danmaku", (std_time, username, content, uid, fans_club, fans_level))
        
        @self.room.on('SUPER_CHAT_MESSAGE')
        async def on_sc(event):
            # print(json.dumps(event, ensure_ascii=False))
            username = event["data"]["data"]["uinfo"]["base"]["name"]
            content = event["data"]["data"]["message"]

            try:
                fans_club = event["data"]["data"]["medal_info"]["medal_name"]
                fans_level = event["data"]["data"]["medal_info"]["medal_level"]
            except:
                fans_club = "无"
                fans_level = 0

            price = event["data"]["data"]["price"]
            origin_time = float(event["data"]["data"]["start_time"])
            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
            keep_time = event["data"]["data"]["time"]
            room_db.insert("super_chat", (std_time, username, content, \
                                          price, keep_time, \
                                          fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
        
        @self.room.on('SEND_GIFT')
        async def on_gift(event):
            username = event["data"]["data"]["uname"]
            content = event["data"]["data"]["giftName"]

            try:
                fans_club = event["data"]["data"]["medal_info"]["medal_name"]
                fans_level = event["data"]["data"]["medal_info"]["medal_level"]
            except:
                fans_club = "无"
                fans_level = 0

            price = event["data"]["data"]["price"]
            origin_time = float(event["data"]["data"]["timestamp"])
            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
            
            room_db.insert("gifts", (std_time, username, content, \
                                     price, \
                                     fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
        
        @self.room.on('GUARD_BUY')
        async def on_guard(event):
            username = event["data"]["data"]["username"]
            content = event["data"]["data"]["gift_name"]

            try:
                u = user.User(event["data"]["data"]["uid"], credential=credential)
                medal_info = sync(u.get_user_medal())["list"][0]["medal_info"]
                fans_club = medal_info["medal_name"]
                fans_level = medal_info["level"]
            except:
                fans_club = "unknown"
                fans_level = 0

            price = event["data"]["data"]["price"]
            origin_time = float(event["data"]["data"]["start_time"])
            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
            
            room_db.insert("gifts", (std_time, username, content, \
                                     price, \
                                     fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
    
    def start(self):
        sync(self.room.connect())
