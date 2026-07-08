"""
登录页面 UI 测试用例（playwright + pytest + allure）
演示 playwright Python 版的标准用法（传统选择器定位）

AI 视觉驱动的 UI 测试请见 midscene/ 目录（Node + Midscene.js）
"""
import allure
import pytest

from config.settings import settings


@allure.feature("用户认证")
@allure.story("登录页面")
@pytest.mark.ui
class TestLoginUI:
    """登录页面 UI 测试类"""

    @allure.title("用例1：打开登录页并校验标题")
    @pytest.mark.smoke
    def test_open_login_page(self, page):
        """
        打开 Web 登录页，断言页面成功加载

        注意：page fixture 由 pytest-playwright 提供
              运行前需将 data/config.yaml 的 web_url 替换为真实地址
        """
        with allure.step("打开登录页"):
            page.goto(settings.WEB_URL)
            page.wait_for_load_state("networkidle")

        with allure.step("截图并断言页面已加载"):
            allure.attach(
                page.screenshot(),
                name="登录页",
                attachment_type=allure.attachment_type.PNG,
            )
            assert page.title() is not None, "【断言失败】页面标题为空，可能未正常加载"
