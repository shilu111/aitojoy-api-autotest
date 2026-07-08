"""
HTTP 接口请求封装模块
基于 requests.Session，统一管理 base_url、超时、请求头、日志与 Allure 附件
"""
import json
import allure
import requests

from config.settings import settings
from common.logger import log


class HttpClient:
    """接口请求客户端：封装常用 HTTP 方法，自动记录日志并附加到 Allure 报告"""

    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = (base_url or settings.BASE_URL).rstrip("/")
        self.timeout = timeout or settings.TIMEOUT
        self.session = requests.Session()

    def _full_url(self, path: str) -> str:
        """拼接完整 URL"""
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        统一请求入口
        :param method: 请求方法 GET/POST/PUT/DELETE
        :param path: 接口路径或完整 URL
        :param kwargs: 透传给 requests 的参数（params/json/data/headers 等）
        :return: Response 对象
        """
        url = self._full_url(path)
        kwargs.setdefault("timeout", self.timeout)

        with allure.step(f"{method.upper()} {url}"):
            log.info(f"请求: {method.upper()} {url} | 参数: {kwargs.get('json') or kwargs.get('params') or {}}")
            response = self.session.request(method, url, **kwargs)
            self._attach_to_allure(method, url, kwargs, response)
            log.info(f"响应: {response.status_code} | {response.text[:500]}")
            return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    @staticmethod
    def _attach_to_allure(method, url, kwargs, response):
        """将请求与响应详情附加到 Allure 报告"""
        detail = {
            "请求方法": method.upper(),
            "请求地址": url,
            "请求头": dict(kwargs.get("headers", {})),
            "请求体": kwargs.get("json") or kwargs.get("data"),
            "状态码": response.status_code,
        }
        allure.attach(
            json.dumps(detail, ensure_ascii=False, indent=2),
            name="接口请求详情",
            attachment_type=allure.attachment_type.JSON,
        )
        allure.attach(
            response.text,
            name="接口响应内容",
            attachment_type=allure.attachment_type.TEXT,
        )
