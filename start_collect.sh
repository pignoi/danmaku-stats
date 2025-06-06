## 此脚本可以用于快速开启收集程序，如果需要用到bilibili的收集程序，需要先在指定目录下修改对应的userinfo_sample.json。该脚本提供一个模版，如果需要循环等功能请自行添加。
#!/bin/bash

WORK_DIR=`pwd`    # change your workdir here
DB_DROP_INTERVAL=5
PLATFORM=bilibili
ROOM_ID=3044248
DOCKER_NAME=collect_zc    # 方便docker管理

if  [ ! -d $WORK_DIR/dbs ]; then
    mkdir $WORK_DIR/dbs
fi

if  [ ! -f $WORK_DIR/userinfo.json ] && [ $PLATFORM == bilibili ]; then
    echo "There is not your bilibili user information. Please check userinfo_sample.json and https://nemo2011.github.io/bilibili-api/#/get-credential"
    exit 1
fi

docker run -d -v $WORK_DIR/dbs/:/app/dbs \
 -v $WORK_DIR/userinfo.json:/app/userinfo.json \
 -e PLATFORM=$PLATFORM \
 -e ROOM_ID=$ROOM_ID \
 -e DB_DROP_INTERVAL=$DB_DROP_INTERVAL \
 --name $DOCKER_NAME \
 --restart always pignoi/danmaku_collector:v0.1.3
