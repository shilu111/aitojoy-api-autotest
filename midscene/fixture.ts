import { test as base } from '@playwright/test';
import type { PlayWrightAiFixtureType } from '@midscene/web/playwright';
import { PlaywrightAiFixture } from '@midscene/web/playwright';

/**
 * 扩展 Playwright test，注入 Midscene AI 能力
 * 用例中即可使用 ai / aiQuery / aiAssert / aiTap 等自然语言 API
 */
export const test = base.extend<PlayWrightAiFixtureType>(
  PlaywrightAiFixture({
    waitForNetworkIdleTimeout: 2000,
  }),
);

export { expect } from '@playwright/test';
