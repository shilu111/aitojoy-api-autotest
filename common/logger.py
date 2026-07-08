"""
日志工具模块
提供统一的控制台日志输出，供接口/UI 测试调用
"""
import logging
import sys


def get_logger(name: str = "aitojoy") -> logging.Logger:
    """
    获取日志记录器
    :param name: 日志名称
    :return: Logger 实例
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # 避免重复添加 handler
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


log = get_logger()
