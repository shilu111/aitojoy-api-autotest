"""
合同接口对象层（API Object）
封装合同服务相关接口，测试用例只关注业务调用，不关心 URL/请求头细节
"""
import allure
from common.http_client import HttpClient


class ContractApi:
    """合同相关接口封装"""

    # 合同新增/更新接口路径
    SAVE_OR_UPDATE_PATH = "/api/cloud-api/tojoy-contract-service/eb/contract_info/save_or_update"

    def __init__(self, client: HttpClient):
        self.client = client

    @allure.step("调用合同保存/更新接口")
    def save_or_update(self, payload: dict, headers: dict = None):
        """
        合同新增或更新接口
        :param payload: 合同入参（包含 contractInfo 等业务字段）
        :param headers: 鉴权请求头（tj-auth、tojoy-tenant 等）
        :return: Response 对象
        """
        return self.client.post(self.SAVE_OR_UPDATE_PATH, json=payload, headers=headers)
