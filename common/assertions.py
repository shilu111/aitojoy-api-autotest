"""
断言工具模块
提供接口测试常用的断言方法，断言信息自动写入 Allure 步骤
"""
import allure
from jsonpath_ng import parse


def assert_status_code(response, expected: int = 200):
    """断言响应状态码"""
    with allure.step(f"断言状态码 == {expected}"):
        actual = response.status_code
        assert actual == expected, f"【断言失败】状态码期望 {expected}，实际 {actual}"


def assert_json_value(response, json_path: str, expected):
    """
    断言 JSON 响应中指定路径的值
    :param json_path: JsonPath 表达式，如 '$.data.code'
    :param expected: 期望值
    """
    with allure.step(f"断言 {json_path} == {expected}"):
        matches = [m.value for m in parse(json_path).find(response.json())]
        assert matches, f"【断言失败】响应中未找到路径: {json_path}"
        assert matches[0] == expected, (
            f"【断言失败】{json_path} 期望 {expected}，实际 {matches[0]}"
        )


def assert_contains(response, keyword: str):
    """断言响应文本包含关键字"""
    with allure.step(f"断言响应包含 '{keyword}'"):
        assert keyword in response.text, f"【断言失败】响应中不包含: {keyword}"
