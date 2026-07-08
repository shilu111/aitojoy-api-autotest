import { test } from '../fixture';

/**
 * AI 视觉驱动的登录 UI 测试（Midscene.js）
 * 用自然语言描述操作步骤，由多模态大模型识别页面元素并执行
 *
 * 运行前请在 .env 配置 WEB_URL / 测试账号 / 大模型 API Key
 * 执行命令：npm run test:ai
 */
test.beforeEach(async ({ page }) => {
  await page.goto(process.env.WEB_URL || '/');
  await page.waitForLoadState('networkidle');
});

test('AI 登录流程校验', async ({
  page,
  ai,
  aiInput,
  aiTap,
  aiAssert,
}) => {
  // 用自然语言定位并输入用户名、密码
  await aiInput(process.env.TEST_USERNAME || '', '用户名输入框');
  await aiInput(process.env.TEST_PASSWORD || '', '密码输入框');

  // 点击登录按钮
  await aiTap('登录按钮');

  // AI 断言登录成功（页面进入首页/出现用户信息）
  await aiAssert('页面已登录成功，显示了首页或用户信息');
});
