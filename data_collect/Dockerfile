FROM python:3.10

RUN apt update \
    && DEBIAN_FRONTEND=noninteractive apt install -y tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV DB_PATH=/app/dbs
ENV USERINFO=/app/userinfo.json
ENV TZ=Asia/Shanghai

ADD . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt


ENV PLATFORM="bilibili"
ENV ROOM_ID=3044248

CMD python3 data_collector.py -p $PLATFORM -r $ROOM_ID