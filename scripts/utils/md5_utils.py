import hashlib
import zipfile
import logging


def calculate_md5_file(file_path):
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def get_md5_of_file_in_zip(zip_path, file_name_in_zip):
    """
    计算 ZIP 包中指定文件的 MD5 值（不解压到硬盘）
    """
    md5_hash = hashlib.md5()

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 检查文件是否存在
            if file_name_in_zip not in zf.namelist():
                logging.error(f"错误: ZIP 包中找不到文件 '{file_name_in_zip}'")
                return None

            # 打开 ZIP 包内的文件
            with zf.open(file_name_in_zip) as f:
                # 分块读取并更新哈希
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)

        return md5_hash.hexdigest()

    except zipfile.BadZipFile:
        logging.error("错误: 这不是一个有效的 ZIP 文件")
        return None
    except Exception as e:
        logging.error(f"发生错误: {e}")
        return None