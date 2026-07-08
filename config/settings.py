"""
全局配置加载模块
统一从 .env 环境变量 + data/config.yaml 读取配置，供全项目使用
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
# 加载 .env 环境变量
load_dotenv(ROOT_DIR / ".env")


def _load_yaml(file_name: str) -> dict:
    """读取 data 目录下的 YAML 配置文件"""
    file_path = ROOT_DIR / "data" / file_name
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings:
    """配置中心：环境变量优先，其次 config.yaml 默认值"""

    _yaml = _load_yaml("config.yaml")

    # ===== 基础地址 =====
    BASE_URL: str = os.getenv("BASE_URL", _yaml.get("base_url", ""))
    WEB_URL: str = os.getenv("WEB_URL", _yaml.get("web_url", ""))

    # ===== 测试账号 =====
    TEST_USERNAME: str = os.getenv("TEST_USERNAME", _yaml.get("username", ""))
    TEST_PASSWORD: str = os.getenv("TEST_PASSWORD", _yaml.get("password", ""))

    # ===== 超时配置（秒）=====
    TIMEOUT: int = int(_yaml.get("timeout", 30))

    # ===== 目录路径 =====
    ROOT_DIR = ROOT_DIR
    REPORT_DIR = ROOT_DIR / "reports"


settings = Settings()
