FROM python:3.9

RUN apt update \
    && DEBIAN_FRONTEND=noninteractive apt install -y tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV DB_PATH=/app/dbs
ENV USERINFO=/app/userinfo.json
ENV TZ=Asia/Shanghai

ADD . /app
WORKDIR /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

ENV IS_DOCKER=True
ENV PLATFORM="bilibili"
ENV ROOM_ID=3044248
ENV ACCEPT_GIFT=False

CMD python3 data_collector.py -p $PLATFORM -r $ROOM_ID -g $ACCEPT_GIFT
