"""
登录接口测试用例（requests + pytest + allure）
演示接口对象层调用、数据驱动与断言工具的标准用法
"""
import yaml
import allure
import pytest
from pathlib import Path

from api.login_api import LoginApi
from common.assertions import assert_status_code, assert_json_value

# 加载登录测试数据
_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "login_data.yaml"
with open(_DATA_FILE, "r", encoding="utf-8") as f:
    LOGIN_DATA = yaml.safe_load(f)


@allure.feature("用户认证")
@allure.story("登录接口")
@pytest.mark.api
class TestLoginApi:
    """登录接口测试类"""

    @allure.title("用例1：有效账号登录成功")
    @pytest.mark.smoke
    def test_login_success(self, http_client):
        """
        有效账号登录，断言状态码 200 且返回业务码正确

        注意：本用例为框架演示，需将 data/config.yaml 中的 base_url
              及 api/login_api.py 中的接口路径替换为真实环境后运行
        """
        data = LOGIN_DATA["valid_login"]
        login_api = LoginApi(http_client)

        response = login_api.login(data["username"], data["password"])

        assert_status_code(response, 200)
        assert_json_value(response, "$.code", data["expected_code"])

    @allure.title("用例2：错误密码登录失败")
    def test_login_wrong_password(self, http_client):
        """错误密码登录，断言返回鉴权失败状态码"""
        data = LOGIN_DATA["invalid_login"]
        login_api = LoginApi(http_client)

        response = login_api.login(data["username"], data["password"])

        assert_status_code(response, data["expected_code"])
