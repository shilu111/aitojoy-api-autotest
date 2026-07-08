"""
conftest.py - pytest 全局 fixture 配置
提供：接口客户端、playwright 页面、Allure 环境信息、失败截图
"""
import os
import pytest
import allure

from config.settings import settings
from common.http_client import HttpClient


def pytest_configure(config):
    """写入 Allure 环境信息"""
    allure_dir = config.getoption("--alluredir", default="reports/allure-results")
    if allure_dir:
        os.makedirs(allure_dir, exist_ok=True)
        with open(os.path.join(allure_dir, "environment.properties"), "w", encoding="utf-8") as f:
            f.write(f"BaseURL={settings.BASE_URL}\n")
            f.write(f"WebURL={settings.WEB_URL}\n")
            f.write("Project=aitojoy-api-autotest\n")
            f.write("Framework=pytest+requests+playwright+Midscene.js+allure\n")


def pytest_addoption(parser):
    """注册自定义命令行参数：执行时输入协议类型名称"""
    parser.addoption(
        "--contract-type",
        action="store",
        default=None,
        help="协议类型名称（如 合作协议/服务协议），用例将反查对应 contractTypeValue 编码后调用",
    )


@pytest.fixture(scope="session")
def contract_type_name(request):
    """获取命令行传入的协议类型名称（未传则为 None，用例使用报文默认值）"""
    return request.config.getoption("--contract-type")


# ==================== 接口测试 fixture ====================

@pytest.fixture(scope="session")
def http_client():
    """会话级接口客户端，全用例复用同一 Session"""
    return HttpClient()


# ==================== UI 测试 fixture (playwright) ====================

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """统一浏览器上下文配置（视口大小、忽略 HTTPS 错误）"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """UI 用例失败时自动截图并附加到 Allure"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(
                page.screenshot(),
                name=f"失败截图-{item.name}",
                attachment_type=allure.attachment_type.PNG,
            )
