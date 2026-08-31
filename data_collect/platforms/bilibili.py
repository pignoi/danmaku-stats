from bilibili_api import live, sync
from bilibili_api import Credential
from basetools.db_manager import LiveDatabase

import json
import os
import datetime
import logging

logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BiliDanmaku:
    def __init__(self, room_id, accept_gift:bool=False):
        
        userinfo = json.load(open(os.environ.get("USERINFO")))
        credential = Credential(sessdata=userinfo["sessdata"],
                                bili_jct=userinfo["bili_jct"],
                                buvid3=userinfo["buvid3"],
                                dedeuserid=userinfo["dedeuserid"])

        self.room = live.LiveDanmaku(room_id, credential=credential)
        room_db = LiveDatabase("bilibili", room_id)

        @self.room.on('DANMU_MSG')
        async def on_danmaku(event):
            # 收到弹幕
            try:
                baseinfo = event["data"]["info"]
                username = baseinfo[0][15]["user"]["base"]["name"]
                uid = baseinfo[0][15]["user"]["uid"]

                # 检测是否为直播间表情弹幕
                if baseinfo[0][12] == 1:
                    image_url = baseinfo[0][13]["url"]
                    content = json.loads(baseinfo[0][15]["extra"])["content"] + f"({image_url})"
                else:
                    content = json.loads(baseinfo[0][15]["extra"])["content"]

                origin_time = baseinfo[0][4] / 1000
                std_time = datetime.datetime.fromtimestamp(origin_time).strftime('%Y-%m-%d %H:%M:%S')

                try:
                    fans_club = baseinfo[3][1]
                    fans_level = baseinfo[3][0]
                except (IndexError, TypeError):
                    fans_club = "无"
                    fans_level = 0

            except (TypeError, KeyError, IndexError, ValueError) as e:
                # 解析失败时跳过该条弹幕，避免把 "In error" 这类脏数据写入数据库
                logging.warning("解析弹幕消息失败，已跳过: %s", e)
                return

            room_db.insert("danmaku", (std_time, username, content, uid, fans_club, fans_level))
        
        @self.room.on('SUPER_CHAT_MESSAGE')
        async def on_sc(event):
            try:
                username = event["data"]["data"]["uinfo"]["base"]["name"]
                content = event["data"]["data"]["message"]

                try:
                    fans_club = event["data"]["data"]["medal_info"]["medal_name"]
                    fans_level = event["data"]["data"]["medal_info"]["medal_level"]
                except (KeyError, IndexError, TypeError):
                    fans_club = "无"
                    fans_level = 0

                price = event["data"]["data"]["price"]
                origin_time = float(event["data"]["data"]["start_time"])
                std_time = datetime.datetime.fromtimestamp(origin_time).strftime('%Y-%m-%d %H:%M:%S')
                keep_time = event["data"]["data"]["time"]
                room_db.insert("super_chat", (std_time, username, content, \
                                              price, keep_time, \
                                              fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
            except (KeyError, IndexError, TypeError, ValueError) as e:
                logging.warning("解析SC消息失败，已跳过: %s", e)
        
        if accept_gift == True:
            @self.room.on('SEND_GIFT')
            async def on_gift(event):
                try:
                    username = event["data"]["data"]["uname"]
                    content = event["data"]["data"]["giftName"]

                    try:
                        fans_club = event["data"]["data"]["medal_info"]["medal_name"]
                        fans_level = event["data"]["data"]["medal_info"]["medal_level"]
                    except (KeyError, IndexError, TypeError):
                        fans_club = "无"
                        fans_level = 0

                    price = event["data"]["data"]["price"]
                    origin_time = float(event["data"]["data"]["timestamp"])
                    std_time = datetime.datetime.fromtimestamp(origin_time).strftime('%Y-%m-%d %H:%M:%S')

                    room_db.insert("gifts", (std_time, username, content, \
                                            price, \
                                            fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
                except (KeyError, IndexError, TypeError, ValueError) as e:
                    logging.warning("解析礼物消息失败，已跳过: %s", e)
            
            @self.room.on('GUARD_BUY')
            async def on_guard(event):
                try:
                    username = event["data"]["data"]["username"]
                    content = event["data"]["data"]["gift_name"]

                    ## 此处使用get_user_medal总会报错，暂时不做处理直接不加这个功能，后面再做相关测试。
                    fans_club = "unknown"
                    fans_level = 0

                    price = event["data"]["data"]["price"]
                    origin_time = float(event["data"]["data"]["start_time"])
                    std_time = datetime.datetime.fromtimestamp(origin_time).strftime('%Y-%m-%d %H:%M:%S')

                    room_db.insert("gifts", (std_time, username, content, \
                                            price, \
                                            fans_club, fans_level, json.dumps(event, ensure_ascii=False)))
                except (KeyError, IndexError, TypeError, ValueError) as e:
                    logging.warning("解析舰长购买消息失败，已跳过: %s", e)
    
    def start(self):
        sync(self.room.connect())
