from bilibili_api import live, sync
from bilibili_api import Credential
import json

credential = Credential(sessdata="44c8f999,1730621079,2915c*52CjBPTV-8n00kkMLP1ZKZLbX7IT1J_05JgsaSipeAj71vx73T8grj8otySceZ5dd3tTkSVmZfODJEQ2otTThUNnMyMS11TVp5dENkMHU5cHdUZHVpdWJ4a3pVel9veEtnV3l4RVFhZFdEdndnei1xczRPSkVJX0NxY3doUlotb0ZmMHVYaFJCS0xnIIEC",
                        bili_jct="64037da1ad8b5fac1ba529f649041a1b",
                        buvid3="7EB6F4F7-E0ED-BEE7-15F4-882ECFE50EFF59553infoc",
                        dedeuserid="442819260")
room = live.LiveDanmaku(8604981, credential=credential)

@room.on('DANMU_MSG')
async def on_danmaku(event):
    # 收到弹幕
    baseinfo = event["data"]["info"]
    include_content = json.loads(baseinfo[0][15]["extra"])
    content = include_content["content"]
    username = baseinfo[0][15]["user"]["base"]["name"]
    print(f"{username}: {content}")

#@room.on('SEND_GIFT')
#async def on_gift(event):
#    # 收到礼物
#    print(event)

sync(room.connect())
