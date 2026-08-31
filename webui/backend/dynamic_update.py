import logging
logging.basicConfig(level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from tools.desuwa import DesuwaStats
from tools.zywoo import ZywooStats

DesuwaHistory = DesuwaStats(platform="douyu", room_id="6979222")
Desuwa1Day= DesuwaStats(platform="douyu", room_id="6979222")
Desuwa1hours= DesuwaStats(platform="douyu", room_id="6979222")
Desuwa1min= DesuwaStats(platform="douyu", room_id="6979222")

ZywooHistory = ZywooStats(platform="douyu", room_id="6979222")
Zywoo1Day= ZywooStats(platform="douyu", room_id="6979222")
Zywoo1hours= ZywooStats(platform="douyu", room_id="6979222")
Zywoo1min= ZywooStats(platform="douyu", room_id="6979222")

if __name__ == "__main__":

    DesuwaHistory.init_dynamic_update(timevalue=100000, timeunit="days")
    Desuwa1Day.init_dynamic_update(timevalue=1, timeunit="days")
    Desuwa1hours.init_dynamic_update(timevalue=1, timeunit="hours")
    Desuwa1min.init_dynamic_update(timevalue=1, timeunit="minutes")

    ZywooHistory.init_dynamic_update(timevalue=100000, timeunit="days")
    Zywoo1Day.init_dynamic_update(timevalue=1, timeunit="days")
    Zywoo1hours.init_dynamic_update(timevalue=1, timeunit="hours")
    Zywoo1min.init_dynamic_update(timevalue=1, timeunit="minutes")

    while True:
        time.sleep(10000)
