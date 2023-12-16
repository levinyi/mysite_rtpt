from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler

cfg = ConfigParser()
cfg.read("setting.ini", encoding='utf-8')
path_cfg = dict(cfg.items("path"))
down_cfg = dict(cfg.items("down"))
process_cfg = dict(cfg.items("process"))
upload_cfg = dict(cfg.items("upload"))
debug_cfg = dict(cfg.items("debug"))
logging_cfg = dict(cfg.items("logging"))

DOWN_WAIT = int(down_cfg.get('down_wait'))
PROCESS_WAIT = int(process_cfg.get('process_wait'))
UPLOAD_WAIT = int(upload_cfg.get('upload_wait'))

USE_CHECK = down_cfg.get('use_check') == 'True'
TIMEDELTA_HOUR = int(down_cfg.get("check_timedelta_hour"))

COLUMNS = process_cfg.get('input_file_columns').split(',')

LOG_MAX_BYTES = int(logging_cfg.get('log_file_size')) * 1024 * 1024
UPLOAD_ONCE = int(upload_cfg.get('upload_once'))

DEBUG = debug_cfg.get('debug') == 'True'

# 配置logging

def get_logger(path):
    """获取logger对象
    在DEBUG模式下，日志输出到控制台
    在非DEBUG模式下，日志输出到文件

    :param path: 日志文件路径
    :return: logger对象
    """
    if DEBUG:
        logging.basicConfig(level=logging_cfg['log_level'], format=logging_cfg['log_format'],
                            datefmt=logging_cfg['datefmt'],encoding='utf-8')
    else:
        logging.basicConfig(level=logging_cfg['log_level'], format=logging_cfg['log_format'],
                            datefmt=logging_cfg['datefmt'], encoding='utf-8',
                            handlers=[RotatingFileHandler(
                                path, maxBytes=LOG_MAX_BYTES, backupCount=int(logging_cfg['log_file_backup']))
                            ])
    logger = logging.getLogger()
    return logger
