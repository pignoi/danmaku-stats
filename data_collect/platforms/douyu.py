## 此程序参考https://www.cnblogs.com/aadd123/p/14009467.html，在代码基础上做了适应性修改，在此处鸣谢作者来路生云烟

import websocket
import threading
import time
import requests
import json
from db_manager import live_database
import datetime
import logging

logging.basicConfig(level="INFO")

class douyuDanmaku:
    def __init__(self, roomid):
        url = 'wss://danmuproxy.douyu.com:8502/'
        self.gift_dict = self.get_gift_dict()
        self.gift_dict_keys = self.gift_dict.keys()
        self.room_id = roomid
        self.client = websocket.WebSocketApp(url, on_open=self.on_open, on_error=self.on_error,
                                            on_message=self.on_message, on_close=self.on_close)

        self.ygb = 0

        self.room_db = live_database("douyu", room_id=self.room_id)

    def start(self):
        self.stop_threads = False
        logging.info("正在尝试连接弹幕服务器...未报错则连接成功")
        self.client.run_forever()

    def stop(self):
        self.logout()
        self.client.close()

    def on_open(self, wss):
        self.login()
        self.join_group()
        # 终止心跳程序的线程，为了尽快重启将心跳间隔设为15
        self.heartbeat_thread = threading.Thread(target=self.heartbeat)
        self.stop_threads = False
        self.heartbeat_thread.setDaemon(True)
        self.heartbeat_thread.start()

    def on_error(self, wssobj, mes):
        print("error: ", mes)

    def on_close(self,wssobj, b, c):
        # print(b,c)
        logging.warning("远程服务器断开, 正在关闭当次连接...")
        self.stop_threads = True
        self.heartbeat_thread.join()
        logging.info('上一个连接已关闭，正在重连...')
        self.start()

    def send_msg(self, msg):
        msg_bytes = self.msg_encode(msg)
        self.client.send(msg_bytes)

    def on_message(self, wssobj, msg):
        message = self.msg_decode(msg)
        # print(message)
        for msg_str in message:
            msg_dict = self.msg_format(msg_str)
            
            if type(msg_dict) == dict:
                # sender info
                if "type" in msg_dict.keys():
                    if msg_dict['type'] == 'chatmsg' or msg_dict['type'] == 'dgb':
                        username = msg_dict['nn']
                        try:
                            fans_club = msg_dict["bnn"]
                            fans_level = msg_dict["bl"]
                        except KeyError:
                            fans_club = "无"
                            fans_level = 0

                        if fans_club == "":
                            fans_club = "无"
                            fans_level = 0
                                    
                    # 接受弹幕信息
                    if msg_dict['type'] == 'chatmsg':
                        content = msg_dict['txt']
                        uid = msg_dict['uid']
                        try:
                            origin_time = float(f"{int(msg_dict['cst'])/1000:.3f}")
                            std_time = datetime.datetime.strftime(datetime.datetime.fromtimestamp(origin_time), '%Y-%m-%d %H:%M:%S')
                        except KeyError:
                            std_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

                        self.room_db.insert("danmaku",(std_time, username, content, uid, fans_club, fans_level))
                    
                    # 接受礼物信息，粉丝荧光棒做统一处理
                    if msg_dict['type'] == 'dgb':
                        std_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                        if msg_dict['gfid'] in self.gift_dict_keys:
                            giftname = self.gift_dict[msg_dict['gfid']]
                            giftcount = msg_dict["gfcnt"]
                        else:
                            try:
                                giftname = msg_dict["gcn"]
                            except:
                                giftname = "未知礼物"
                            giftcount = msg_dict["gfcnt"]
                        
                        if giftname != "粉丝荧光棒":
                            self.room_db.insert("gifts", (std_time, username, giftname, \
                                        giftcount, \
                                        fans_club, fans_level, json.dumps(msg_dict, ensure_ascii=False)))
                        else:
                            self.ygb += int(giftcount)
                            if self.ygb >= 5000:
                                self.room_db.insert("gifts", (std_time, "荧光棒统计", giftname, \
                                        self.ygb, \
                                        "all fans", 0, "ygb"))
                                self.ygb = 0

    # 发送登录信息
    def login(self):
        login_msg = 'type@=loginreq/roomid@=%s/' % (self.room_id,)
        self.send_msg(login_msg)

    def logout(self):
        logout_msg = 'type@=logout/'
        self.send_msg(logout_msg)

    # 发送入组消息
    def join_group(self):
        join_group_msg = 'type@=joingroup/rid@=%s/gid@=-9999/' % (self.room_id)
        self.send_msg(join_group_msg)

    # 保持心跳线程
    def heartbeat(self):
        while True:
            # 15秒发送一个心跳包
            if self.stop_threads == True:
                break
            self.send_msg('type@=mrkl/')
            # print('发送心跳')
            time.sleep(15)

    def msg_encode(self, msg):
        # 消息以 \0 结尾，并以utf-8编码
        msg = msg + '\0'
        msg_bytes = msg.encode('utf-8')
        #消息长度 + 头部长度8
        length_bytes = int.to_bytes(len(msg) + 8, 4, byteorder='little')
        #斗鱼客户端发送消息类型 689
        type = 689
        type_bytes = int.to_bytes(type, 2, byteorder='little')
        # 加密字段与保留字段，默认 0 长度各 1
        end_bytes = int.to_bytes(0, 1, byteorder='little')
        #按顺序相加  消息长度 + 消息长度 + 消息类型 + 加密字段 + 保留字段
        head_bytes = length_bytes + length_bytes + type_bytes + end_bytes + end_bytes
        #消息头部拼接消息内容
        data = head_bytes + msg_bytes
        return data

    def msg_decode(self, msg_bytes):
        # 定义一个游标位置
        cursor = 0
        msg = []
        while cursor < len(msg_bytes):
            #根据斗鱼协议，报文 前四位与第二个四位，都是消息长度，取前四位，转化成整型
            content_length = int.from_bytes(msg_bytes[cursor: (cursor + 4) - 1], byteorder='little')
            #报文长度不包含前4位，从第5位开始截取消息长度的字节流，并扣除前8位的协议头，取出正文，用utf-8编码成字符串
            content = msg_bytes[(cursor + 4) + 8:(cursor + 4) + content_length - 1].decode(encoding='utf-8',
                                                                                        errors='ignore')
            msg.append(content)
            cursor = (cursor + 4) + content_length
        # print(msg)
        return msg

    def msg_format(self, msg_str):
        try:
            msg_dict = {}
            msg_list = msg_str.split('/')[0:-1]
            for msg in msg_list:
                msg = msg.replace('@s', '/').replace('@A', '@')
                msg_tmp = msg.split('@=')
                msg_dict[msg_tmp[0]] = msg_tmp[1]
            return msg_dict
        except Exception as e:
            logging.info(str(e))

    def get_gift_dict(self):
        gift_json = {}
        gift_json1 = requests.get('https://webconf.douyucdn.cn/resource/common/gift/flash/gift_effect.json').text
        gift_json2 = requests.get(
            'https://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json').text
        gift_json1 = gift_json1.replace('DYConfigCallback(', '')[0:-2]
        gift_json2 = gift_json2.replace('DYConfigCallback(', '')[0:-2]
        gift_json1 = json.loads(gift_json1)['data']['flashConfig']
        gift_json2 = json.loads(gift_json2)['data']
        for gift in gift_json1:
            gift_json[gift] = gift_json1[gift]['name']
        for gift in gift_json2:
            gift_json[gift] = gift_json2[gift]['name']
        return gift_json

