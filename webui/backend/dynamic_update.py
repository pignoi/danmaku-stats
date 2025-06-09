import sys
sys.path.append("../../")
import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import time

from tools.desuwa import DesuwaStats

DesuwaHistory = DesuwaStats(platform="douyu", room_id="6979222")
Desuwa1Day= DesuwaStats(platform="douyu", room_id="6979222")
Desuwa10s= DesuwaStats(platform="douyu", room_id="6979222")


if __name__ == "__main__":

    DesuwaHistory.init_update(timevalue=100000, timeunit="days")
    Desuwa1Day.init_update(timevalue=1, timeunit="days")
    Desuwa10s.init_update(timevalue=1, timeunit="hours")

    while True:
        time.sleep(10000)
