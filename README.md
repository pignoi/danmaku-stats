<p align="center">
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

### 可用直播间

目前做了B站和斗鱼的收集接口。B站平台使用了[bilibili-api](https://github.com/Nemo2011/bilibili-api)中的接口进行开发，斗鱼平台使用官方的ws弹幕流服务器进行收集。

目前自己在做的收集：

斗鱼：[玩机器丶Machine (最佳实践例)](https://douyu.com/6979222)、[33Svan](https://douyu.com/11073934)、[Gemini](https://douyu.com/36252)

B站：[魔法Zc目录](https://live.bilibili.com/3044248)、[血狼破军](https://live.bilibili.com/8432038)、[废物弟弟汉堡包](https://live.bilibili.com/8604981)、[温润如玉祖国宁](https://live.bilibili.com/22782128)

因此这些直播间的统计信息在上面的网站中均可找到。（需要直播间的原始房间号，房间靓号还没有做适配~如玩出的直播间号应当是6979222而不是6657~）

## 🪄 技术栈

收集部分：python3

后端：Flask + sqlite + uWSGI

前端：vue3 + vite + axios ~~+ (DeepSeek)~~

打包部署：Docker + Nginx

## 声明

该项目目前由个人开发，因此可能存在很多bug，特别是个人初次接触的前端部分，敬请谅解。

作者：

斗鱼ID: YPCouragE

B站ID: [pigno1roko](https://space.bilibili.com/442819260)

QQ: 404663951

更多直播间的弹幕统计项目可以联系作者进行部署~

## 致谢

项目的灵感来源：[sb6657.cn](https://github.com/SEhzm/sb6657/)

B站api-python接口支持：[bilibili-api](https://github.com/Nemo2011/bilibili-api)


-----

## 部署

收集部分部署：
```bash
bash start_collect.sh
```
此处后面同样会改为`docker compose`的部署方式~

后端部署：
```bash
docker compose -f backend-compose.yml up -d
```

前端部署：

参考[vue的部署方式](./webui/frontend-vue/README.md)