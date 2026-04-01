import logging
import os
from enum import Enum, auto
import requests
import garth

from .garmin_url_dict import GARMIN_URL_DICT

logger = logging.getLogger(__name__)
from scripts.config import GARMIN_TOKEN_DIR

class GarminClient:
    def __init__(self, email, password, auth_domain, newest_num):
        self.auth_domain = auth_domain
        self.email = email
        self.password = password
        self.newestNum = int(newest_num)
        self.token_dir = GARMIN_TOKEN_DIR
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": GARMIN_URL_DICT.get("SSO_URL_ORIGIN"),
            "nk": "NT"
        }

        # 初始化 garth client
        self._init_garth()

    def _init_garth(self):
        """初始化 garth 客户端配置"""
        if self.auth_domain and str(self.auth_domain).upper() == "CN":
            garth.configure(domain="garmin.cn")
            logger.info("Garmin 配置为国区 (garmin.cn)")
        else:
            garth.configure(domain="garmin.com")
            logger.info("Garmin 配置为国际区 (garmin.com)")

    def login_and_save_token(self):
        """登录并保存 token 到文件"""
        try:
            logger.info("开始登录 Garmin Connect...")
            # 执行登录
            garth.login(self.email, self.password)
            # 保存 token
            if self.token_dir:
                self._save_token(self.token_dir)
                logger.info(f"Token 已保存到：{self.token_dir}")
            # 移除 User-Agent header
            del garth.client.sess.headers['User-Agent']

            logger.info(f"登录成功！用户：{garth.client.username}")
            return True

        except Exception as e:
            logger.error(f"登录失败：{str(e)}")
            return False

    def load_token(self, token_dir=None):
        """从文件加载 token"""
        try:
            if not token_dir:
                token_dir = self.token_dir

            if not token_dir or not os.path.exists(token_dir):
                logger.warning(f"Token 目录不存在：{token_dir}")
                return False

            logger.info(f"尝试从 {token_dir} 加载 Token...")

            # 使用 garth 的 resume 功能
            garth.resume(token_dir)

            # 检查 token 是否过期
            if garth.client.oauth2_token.expired:
                logger.info("Token 已过期，尝试刷新...")
                try:
                    garth.client.refresh_oauth2()
                    self._save_token(token_dir)
                    logger.info("Token 刷新成功")
                except Exception as refresh_error:
                    logger.warning(f"Token 刷新失败：{refresh_error}")
                    return False

            # 验证 token 有效性
            try:
                garth.connectapi("/userprofile-service/socialProfile")
                logger.info(f"Token 验证成功！用户：{garth.client.username}")
                return True
            except Exception as verify_error:
                logger.warning(f"Token 验证失败：{verify_error}")
                return False

        except Exception as e:
            logger.error(f"加载 Token 失败：{str(e)}")
            return False

    def authenticate(self):
        """认证：优先使用 token，失败则使用账号密码登录"""
        # 尝试加载 token
        if self.token_dir and self.load_token(self.token_dir):
            logger.info("使用 Token 认证成功")
            return True

        # Token 无效，使用账号密码登录
        logger.info("Token 无效或不存在，使用账号密码登录")
        return self.login_and_save_token()

    def _save_token(self, save_path):
        """保存 token 到文件"""
        try:
            garth.save(save_path)

            # 设置文件权限（Unix 系统）
            if os.name != 'nt':
                token_file = os.path.join(save_path, "oauth1_token.json")
                if os.path.exists(token_file):
                    os.chmod(token_file, 0o600)

        except Exception as e:
            logger.error(f"保存 Token 失败：{str(e)}")
            raise

    ## 登录装饰器
    def login(func):
        def ware(self, *args, **kwargs):
            try:
                garth.client.username
            except Exception:
                logger.warning("Garmin is not logging in or the token has expired.")
                self.authenticate()
            return func(self, *args, **kwargs)
        return ware

    @login
    def download(self, path, **kwargs):
        return garth.download(path, **kwargs)

    @login
    def connectapi(self, path, **kwargs):
        return garth.connectapi(path, **kwargs)

    ## 获取运动
    def getActivities(self, start: int, limit: int):

        params = {"start": str(start), "limit": str(limit)}
        activities = self.connectapi(path=GARMIN_URL_DICT["garmin_connect_activities"], params=params)
        return activities

    # ## 获取所有运动
    def getAllActivities(self):
        all_activities = []
        start = 0
        limit = 100
        if 0 < self.newestNum < 100:
            limit = self.newestNum

        while (True):
            activities = self.getActivities(start=start, limit=limit)
            if len(activities) > 0:
                all_activities.extend(activities)

                if 0 < self.newestNum < 100 or start > self.newestNum:
                    return all_activities
            else:
                return all_activities
            start += limit

    ## 下载原始格式的运动
    def downloadFitActivity(self, activity):
        download_fit_activity_url_prefix = GARMIN_URL_DICT["garmin_connect_fit_download"]
        download_fit_activity_url = f"{download_fit_activity_url_prefix}/{activity}"
        response = self.download(download_fit_activity_url)
        return response

    @login
    def upload_activity(self, activity_path: str):
        """Upload activity in fit format from file."""
        # This code is borrowed from python-garminconnect-enhanced ;-)
        file_base_name = os.path.basename(activity_path)
        file_extension = file_base_name.split(".")[-1]
        allowed_file_extension = (
                file_extension.upper() in ActivityUploadFormat.__members__
        )

        if allowed_file_extension:
            try:
                with open(activity_path, 'rb') as file:
                    file_data = file.read()
                    fields = {
                        'file': (file_base_name, file_data, 'text/plain')
                    }

                    url_path = GARMIN_URL_DICT["garmin_connect_upload"]
                    upload_url = f"https://connectapi.{garth.client.domain}{url_path}"
                    self.headers['Authorization'] = str(garth.client.oauth2_token)
                    response = requests.post(upload_url, headers=self.headers, files=fields)
                    res_code = response.status_code
                    result = response.json()
                    uploadId = result.get("detailedImportResult").get('uploadId')
                    isDuplicateUpload = uploadId == None or uploadId == ''
                    if res_code == 202 and not isDuplicateUpload:
                        status = "SUCCESS"
                    elif res_code == 409 and result.get("detailedImportResult").get("failures")[0].get('messages')[
                        0].get('content') == "Duplicate Activity.":
                        status = "DUPLICATE_ACTIVITY"
            except Exception as e:
                logger.error(e)
                status = "UPLOAD_EXCEPTION"
            finally:
                return status
        else:
            return "UPLOAD_EXCEPTION"


class ActivityUploadFormat(Enum):
    FIT = auto()
    GPX = auto()
    TCX = auto()


class GarminNoLoginException(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, status):
        """Initialize."""
        super(GarminNoLoginException, self).__init__(status)
        self.status = status
