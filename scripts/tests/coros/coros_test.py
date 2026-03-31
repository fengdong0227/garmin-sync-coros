from scripts.coros.coros_client import CorosClient
from scripts.utils.md5_utils import calculate_md5_file
from scripts.oss.ali_oss_client import AliOssClient
from pathlib import Path


def test():
    COROS_EMAIL = ''
    COROS_PASSWORD = ''
    corosClient = CorosClient(COROS_EMAIL, COROS_PASSWORD, 10)
    corosClient.login()
    print(corosClient.userId)
    corosClient.uploadActivity("fit_zip/58a0fa43058a4aaf84d2564ead944271.fit", calculate_md5_file("garmin-fit/58a0fa43058a4aaf84d2564ead944271.fit"), "58a0fa43058a4aaf84d2564ead944271.fit")
    client = AliOssClient()
    file_path = '../../../garmin-fit'
    last_file = get_latest_file(file_path)
    print(last_file)
    import os
    size = os.path.getsize(last_file) # 文件路径及文件名
    print(size)
    oss_obj = client.multipart_upload(last_file, f"{corosClient.userId}/{calculate_md5_file(last_file)}.zip")
    upload_result = corosClient.uploadActivity(f"fit_zip/{corosClient.userId}/{calculate_md5_file(last_file)}.zip", calculate_md5_file(last_file), "22354343348.zip", size)
    print(upload_result)


def get_latest_file(folder_path, pattern="*"):
    """使用 pathlib 获取最新的文件"""
    folder = Path(folder_path)
    files = list(folder.glob(pattern))

    if not files:
        return None

    # 按修改时间排序
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)


if __name__ == '__main__':
    test()