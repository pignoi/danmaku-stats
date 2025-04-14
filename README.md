<p align="center">
    <img src="https://media.axuan.wang/favicon.jpg" width="155" height="150"/>
    <h3 align="center">stats.axuan.wang</h3>
    <p align="center">
        <a href="https://github.com/pignoi/danmaku-stats"><img src="https://img.shields.io/github/languages/code-size/pignoi/danmaku-stats?color=blueviolet"></a>
        <a href="https://github.com/pignoi/danmaku-stats"><img src="https://img.shields.io/github/stars/pignoi/danmaku-stats?color=green"></a>
        <a href="https://github.com/pignoi/danmaku-stats"><img src="https://img.shields.io/github/commit-activity/m/pignoi/danmaku-stats?color=9cf"></a>
        <a href="https://github.com/pignoi/danmaku-stats"><img src="https://img.shields.io/github/last-commit/pignoi/danmaku-stats"></a>
        <a href="https://github.com/pignoi/danmaku-stats"><img src="https://img.shields.io/github/languages/count/pignoi/danmaku-stats
"></a>
    </p>
    <p align="center"">
    这是一个使用统计视角进行弹幕<del>（烂梗）</del>展示的项目，从弹幕收集到展示一应俱全。
    </p>    
</p>

-----

## 🌐 部署网站

[https://wjq6657.top](https://wjq6657.top)

[https://stats.axuan.wang](https://stats.axuan.wang)

### 🪩 可用直播间

目前做了B站和斗鱼的收集接口。B站平台使用了[bilibili-api](https://github.com/Nemo2011/bilibili-api)中的接口进行开发，斗鱼平台使用官方的ws弹幕流服务器进行收集。

目前自己在做的收集，点击名称即可直接跳转到统计界面哦：

斗鱼：[玩机器丶Machine (最佳实践例)](https://wjq6657.top)、[Gemini](https://stats.axuan.wang/stats?platform=douyu&room_id=36252)

B站：[魔法Zc目录](https://stats.axuan.wang/stats?platform=bilibili&room_id=3044248)、[血狼破军](https://stats.axuan.wang/stats?platform=bilibili&room_id=8432038)、[废物弟弟汉堡包](https://stats.axuan.wang/stats?platform=bilibili&room_id=8604981)

因此这些直播间的统计信息在上面的网站中均可找到。（需要直播间的原始房间号，房间靓号还没有做适配~如玩出的直播间号应当是6979222而不是6657~）

## 🪄 技术栈

收集部分：python3 + sqlite

后端：Flask + sqlite + uWSGI

前端：vue3 + vite + axios ~~+ (DeepSeek)~~

打包部署：Docker + Nginx

## 🚩 声明

有任何想法都可以在PR中提出，也欢迎在页面中多多复制弹幕！

该项目目前由个人开发，因此可能存在很多bug，特别是个人初次接触的前端部分，敬请谅解。

作者：

斗鱼ID: YPCouragE

B站ID: [浮云飘95](https://space.bilibili.com/442819260)

QQ: 404663951

更多直播间的弹幕统计项目可以联系作者进行部署~

## 🎈 致谢

项目的灵感来源：[sb6657.cn](https://github.com/SEhzm/sb6657/)

B站api-python接口支持：[bilibili-api](https://github.com/Nemo2011/bilibili-api)

感谢小z同学提供的斗鱼21级+账号支持，让我能在玩机器直播间刷wjq6657.top的弹幕，才得到一定的点击量，也得以借此机会找到一些问题和更多的待实现功能~

-----

## 🕒️ 待添加的功能

### 收集部分：
- [ ] 进一步完善`basetools/db_manager.py`的功能：
  - [ ] 分表：一段时间或者数据量达到一定量后进行分表操作
- [ ] 对系统的日志进行重整，使用`logging`库，现在存在多重日志的问题
- [ ] 最近b站的收集频繁需要更新`userinfo`，排查一下可能的问题

### 呈现部分：
- [x] 添加一段时间内发送弹幕数id的统计，看看谁天天刷烂梗刷的最多（注意保护隐私）
- [x] 后端发送数据只需要排名前若干的信息，完全的排名是没有必要的，同时优化带宽连接
- [ ] B站部分对历史SC进行呈现，斗鱼是否有类似SC的功能？
- [ ] 对直播间靓号/短号和原始直播间id进行匹配，使得跳转更加方便
- [x] 在选择后或者正在加载中的统计进行说明，防止选了没有反应导致多次重复点击
- [ ] 优化手机端的呈现方式，对前端`vue`的使用更优雅一些
- [ ] 更灵活的时间选择方式，方便前端的调整
- [ ] （待定）加入一定时间间隔的心跳机制，统计同时访问界面的人数

### 部署部分
- [ ] 找合适的国内服务器进行部署，现在的方式延迟略大

-----

## 部署

### 收集部分部署：
```bash
bash start_collect.sh
```
当然更推荐通过`docker compose`的方式进行部署，只需要修改`environment`当中的环境变量信息就可以指定直播间进行弹幕收集（当然，需要注意直播间的房间号是原始的房间号），此后在命令行中执行（如果版本`docker`版较老可以安装并使用`docker-compose`）：
```bash
docker compose -f collect-compose.yml up -d
```

### 后端部署：
```bash
docker compose -f backend-compose.yml up -d
```

### 前端部署：

参考[vue的部署方式](./webui/frontend-vue/README.md)
