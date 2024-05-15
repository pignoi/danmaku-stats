#!/bin/bash

WORK_DIR=/home/webapp/danmaku-stats    # change your workdir here
PLATFORM=bilibili
ROOM_ID=3044258
DOCKER_NAME=collect_zc    # 方便docker管理

if  [ ! -d $WORK_DIR/dbs ]; then
    mkdir $WORK_DIR/dbs
fi

if  [ ! -d $WORK_DIR/userinfo.json ] && [ $PLATFORM == bilibili ]; then
    echo "There is not your bilibili user information. Please check userinfo_sample.json and https://nemo2011.github.io/bilibili-api/#/get-credential"
    exit 1
fi

docker run -d -v $WORK_DIR/dbs/:/app/dbs -v $WORK_DIR/userinfo.json:/app/dbs -e PLATFORM=$PLATFORM -e ROOM_ID=$ROOM_ID --restart always --name $DOCKER_NAME danmaku-collector