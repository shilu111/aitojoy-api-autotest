"""
合同保存/更新接口测试用例（requests + pytest + allure）
覆盖接口：POST /api/cloud-api/tojoy-contract-service/eb/contract_info/save_or_update
演示：独立 base_url + 自定义鉴权头 + JSON 大报文数据驱动 + JsonPath 断言
"""
import json
import yaml
import copy
import allure
import pytest
from pathlib import Path
from datetime import datetime

from api.contract_api import ContractApi
from common.http_client import HttpClient
from common.assertions import assert_status_code, assert_json_value, assert_contains

# 数据目录
_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 加载合同接口配置（域名、鉴权头、期望结果）
with open(_DATA_DIR / "contract_data.yaml", "r", encoding="utf-8") as f:
    CONTRACT_CFG = yaml.safe_load(f)

# 加载合同保存接口入参报文
with open(_DATA_DIR / "contract_save_payload.json", "r", encoding="utf-8") as f:
    SAVE_PAYLOAD = json.load(f)

# 加载合同直接发起接口入参报文
with open(_DATA_DIR / "contract_direct_payload.json", "r", encoding="utf-8") as f:
    DIRECT_PAYLOAD = json.load(f)


@allure.feature("合同管理")
@allure.story("合同保存/更新")
@pytest.mark.api
class TestContractApi:
    """合同保存/更新接口测试类"""

    @pytest.fixture(scope="class")
    def contract_api(self):
        """构建指向合同服务的接口客户端（独立 base_url）"""
        client = HttpClient(base_url=CONTRACT_CFG["base_url"])
        return ContractApi(client)

    @allure.title("用例1：线下合同生成成功")
    @pytest.mark.smoke
    def test_save_or_update_success(self, contract_api):
        """
        提交完整合同信息（线下发起），断言线下合同生成成功：
          1. HTTP 状态码 200
          2. 业务码 code == 200，success == true，msg == "处理成功"
          3. 返回生成的合同 id 与合同编号 contractCode（即合同已成功生成）

        说明：tj-auth token 有时效，过期会鉴权失败，需更新 data/contract_data.yaml 中的 token
        """
        expected = CONTRACT_CFG["expected"]
        headers = CONTRACT_CFG["headers"]

        # 动态合同名：登记线下合同 + 当前时间（年-月-日 时:分），避免重复数据
        contract_name = "登记线下合同" + datetime.now().strftime("%Y-%m-%d %H:%M")
        payload = copy.deepcopy(SAVE_PAYLOAD)
        payload["contractInfo"]["name"] = contract_name
        allure.attach(contract_name, name="本次合同名称", attachment_type=allure.attachment_type.TEXT)

        response = contract_api.save_or_update(payload, headers=headers)

        # 1. HTTP 状态码断言
        assert_status_code(response, expected["status_code"])
        # 2. 业务结果断言：成功码 / 成功标识 / 成功提示
        assert_json_value(response, expected["code_path"], expected["code_value"])
        assert_json_value(response, expected["success_path"], expected["success_value"])
        assert_json_value(response, expected["msg_path"], expected["msg_value"])

        # 3. 合同生成成功断言：返回合同 id 与合同编号
        result = response.json().get("data") or {}
        with allure.step("断言线下合同生成成功（返回合同 id 与合同编号）"):
            assert result.get("id"), f"【断言失败】未返回合同 id，响应：{response.text[:300]}"
            assert result.get("contractCode"), (
                f"【断言失败】未返回合同编号 contractCode，响应：{response.text[:300]}"
            )

        allure.attach(
            f"合同生成成功 | id={result.get('id')} | "
            f"合同编号={result.get('contractCode')} | "
            f"合同状态={result.get('contractStatusValue')}",
            name="线下合同生成结果",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.title("用例2：直接发起合同成功")
    @pytest.mark.smoke
    def test_direct_initiate_success(self, contract_api, contract_type_name):
        """
        提交完整合同信息（直接发起 START_TYPE_DIRECT），断言直接发起合同成功：
          1. HTTP 状态码 200
          2. 业务码 code == 200，success == true，msg == "处理成功"
          3. 返回生成的合同 id 与合同编号 contractCode
          4. 合同状态为 PROCESSING（直接发起后进入处理中，区别于线下发起的 APPROVING）

        协议类型：执行时可通过 --contract-type 传入协议类型名称（如 合作协议），
                  用例会反查对应 contractTypeValue 编码并写入请求报文；
                  未传入则使用报文中的默认 contractTypeValue。
        """
        expected = CONTRACT_CFG["expected"]
        headers = CONTRACT_CFG["headers"]
        contract_types = CONTRACT_CFG.get("contract_types", {})

        payload = copy.deepcopy(DIRECT_PAYLOAD)

        # 判断逻辑：根据输入的协议类型名称反查 contractTypeValue 编码
        if contract_type_name:
            # 名称 -> 编码 反向映射
            name_to_code = {name: code for code, name in contract_types.items()}
            type_code = name_to_code.get(contract_type_name)
            with allure.step(f"协议类型反查：{contract_type_name} -> {type_code}"):
                assert type_code, (
                    f"【断言失败】未识别的协议类型名称：{contract_type_name}，"
                    f"可选值：{list(name_to_code.keys())}"
                )
            payload["contractInfo"]["contractTypeValue"] = type_code
            type_name = contract_type_name
        else:
            # 未输入则使用报文默认编码，正向查名称
            type_code = payload["contractInfo"].get("contractTypeValue", "")
            type_name = contract_types.get(type_code, type_code)
            with allure.step(f"协议类型（报文默认）：{type_code} -> {type_name}"):
                assert type_name, f"【断言失败】未识别的协议类型编码：{type_code}"

        # 动态合同名：直接发起合同-协议类型名称-当前时间（年-月-日 时:分）
        contract_name = f"直接发起合同-{type_name}-" + datetime.now().strftime("%Y-%m-%d %H:%M")
        payload["contractInfo"]["name"] = contract_name
        allure.attach(
            f"协议类型编码={type_code} | 协议类型名称={type_name} | 合同名={contract_name}",
            name="本次合同信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        response = contract_api.save_or_update(payload, headers=headers)

        # 1. HTTP 状态码断言
        assert_status_code(response, expected["status_code"])
        # 2. 业务结果断言：成功码 / 成功标识 / 成功提示
        assert_json_value(response, expected["code_path"], expected["code_value"])
        assert_json_value(response, expected["success_path"], expected["success_value"])
        assert_json_value(response, expected["msg_path"], expected["msg_value"])

        # 3 & 4. 合同生成成功 + 状态为已发起（直接发起后状态随协议类型不同而不同：
        #         如合作协议->PROCESSING，股权转让协议->SETTING，均表示发起成功）
        result = response.json().get("data") or {}
        actual_status = result.get("contractStatusValue")
        # 直接发起成功的有效状态（非草稿）；线下发起为 APPROVING，本用例不应出现
        valid_direct_status = {"PROCESSING", "SETTING", "SIGNING"}
        with allure.step(f"断言直接发起合同成功（返回 id/编号，状态={actual_status}）"):
            assert result.get("id"), f"【断言失败】未返回合同 id，响应：{response.text[:300]}"
            assert result.get("contractCode"), (
                f"【断言失败】未返回合同编号 contractCode，响应：{response.text[:300]}"
            )
            assert actual_status in valid_direct_status, (
                f"【断言失败】直接发起合同状态期望属于 {valid_direct_status}，"
                f"实际 {actual_status}，响应：{response.text[:300]}"
            )

        allure.attach(
            f"直接发起合同成功 | id={result.get('id')} | "
            f"合同编号={result.get('contractCode')} | "
            f"合同状态={result.get('contractStatusValue')}",
            name="直接发起合同结果",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.title("用例3：缺少鉴权头时请求被拒绝")
    def test_save_or_update_without_auth(self, contract_api):
        """不带 tj-auth 鉴权头提交，断言被拦截（非 200 或业务失败）"""
        # 仅保留 Content-Type，去掉鉴权头
        headers = {"Content-Type": "application/json"}

        response = contract_api.save_or_update(SAVE_PAYLOAD, headers=headers)

        # 未鉴权时通常返回 401/403，或 200 但业务码非成功；此处断言不是成功业务码
        assert response.status_code != 200 or response.json().get("code") not in (0, 200), (
            f"【断言失败】缺少鉴权头时不应成功，实际响应：{response.text[:300]}"
        )
