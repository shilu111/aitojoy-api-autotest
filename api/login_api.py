"""
登录接口对象层（API Object）
将接口请求按业务封装，测试用例只关注业务调用，不关心 URL/参数细节
"""
import allure
from common.http_client import HttpClient


class LoginApi:
    """登录相关接口封装"""

    # 接口路径（按实际后端调整）
    LOGIN_PATH = "/api/auth/login"

    def __init__(self, client: HttpClient):
        self.client = client

    @allure.step("调用登录接口")
    def login(self, username: str, password: str):
        """
        登录接口
        :param username: 用户名
        :param password: 密码
        :return: Response 对象
        """
        payload = {"username": username, "password": password}
        return self.client.post(self.LOGIN_PATH, json=payload)
