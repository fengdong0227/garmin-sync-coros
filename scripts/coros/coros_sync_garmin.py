import os
import sys
import logging

CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
config_path = CURRENT_DIR.rsplit('/', 1)[0]  # 上三级目录
sys.path.append(config_path)

from coros_client import CorosClient
from config  import DB_DIR, COROS_FIT_DIR, LOG_DIR
from coros_db import CorosDB
from garmin.garmin_client import GarminClient
from utils.md5_utils import calculate_md5_file

os.makedirs(LOG_DIR, exist_ok=True)
SYNC_CONFIG = {
    'GARMIN_AUTH_DOMAIN': '',
    'GARMIN_EMAIL': '',
    'GARMIN_PASSWORD': '',
    'GARMIN_NEWEST_NUM': 0,
    "COROS_EMAIL": '',
    "COROS_PASSWORD": '',
    "COROS_NEWEST_NUM": 0,
}

logging.basicConfig(
    filename=os.path.join(LOG_DIR,'coros_to_garmin.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def init(coros_db):
    ## 判断RQ数据库是否存在
    logging.info(f"数据库文件为:{os.path.join(DB_DIR, coros_db.db_name)}")
    if not os.path.exists(os.path.join(DB_DIR, coros_db.db_name)):
        ## 初始化建表
        coros_db.initDB()
    if not os.path.exists(COROS_FIT_DIR):
        os.mkdir(COROS_FIT_DIR)


if __name__ == "__main__":
  # 首先读取 面板变量 或者 github action 运行变量
  for k in SYNC_CONFIG:
      if os.getenv(k):
          v = os.getenv(k)
          SYNC_CONFIG[k] = v

  COROS_EMAIL = SYNC_CONFIG["COROS_EMAIL"]
  COROS_PASSWORD = SYNC_CONFIG["COROS_PASSWORD"]
  COROS_NEWEST_NUM = SYNC_CONFIG["COROS_NEWEST_NUM"]
  corosClient = CorosClient(COROS_EMAIL, COROS_PASSWORD, COROS_NEWEST_NUM)

  GARMIN_EMAIL = SYNC_CONFIG["GARMIN_EMAIL"]
  GARMIN_PASSWORD = SYNC_CONFIG["GARMIN_PASSWORD"]
  GARMIN_AUTH_DOMAIN = SYNC_CONFIG["GARMIN_AUTH_DOMAIN"]
  GARMIN_NEWEST_NUM = SYNC_CONFIG["GARMIN_NEWEST_NUM"]

  garminClient = GarminClient(GARMIN_EMAIL, GARMIN_PASSWORD, GARMIN_AUTH_DOMAIN, GARMIN_NEWEST_NUM)


  ## db 名称
  db_name = "coros.db"
  ## 建立DB链接
  coros_db = CorosDB(db_name)
  ## 初始化DB位置和下载文件位置
  init(coros_db)

  all_activities = corosClient.getAllActivities()
  if all_activities == None or len(all_activities) == 0:
      exit()
  for activity in all_activities:
      activity_id = activity["labelId"]
      sport_type = activity["sportType"]
      coros_db.saveActivity(activity_id, sport_type)


  un_sync_list = coros_db.getUnSyncActivity()
  if un_sync_list == None or len(un_sync_list) == 0:
      exit()
  for un_sync in un_sync_list:
    try:
      id = un_sync["id"]
      sport_type = un_sync["sportType"]
      logging.info(f"coros activityId:{id}, sportType:{sport_type}")
      file = corosClient.downloadActivitie(id, sport_type)
      file_path = os.path.join(COROS_FIT_DIR, f"{id}.fit")
      with open(file_path, "wb") as fb:
          fb.write(file.data)
      upload_status = garminClient.upload_activity(file_path)
      logging.info(f"{id}.fit upload status {upload_status}")
      if upload_status in ("SUCCESS", "DUPLICATE_ACTIVITY"):
        coros_db.updateSyncStatus(id, calculate_md5_file(file_path))

    except Exception as err:
      logging.error(f"同步运动数据失败.{err}")
      coros_db.updateExceptionSyncStatus(un_sync)
      exit()