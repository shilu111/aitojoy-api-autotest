import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// 加载 .env 中的大模型与地址配置
dotenv.config();

/**
 * Midscene.js + Playwright 配置
 * 仅作用于 midscene/ 目录下的 AI 视觉 UI 测试
 */
export default defineConfig({
  testDir: './midscene/tests',
  timeout: 90 * 1000,
  fullyParallel: false,
  reporter: [
    ['list'],
    ['@midscene/web/playwright-reporter', { type: 'merged' }],
  ],
  use: {
    baseURL: process.env.WEB_URL,
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
