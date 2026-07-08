# aitojoy-api-autotest

AI 驱动的接口与 UI 自动化测试框架。

## 技术栈

| 工具 | 用途 |
|------|------|
| pytest | 测试框架核心（用例组织、fixture、参数化）|
| requests | 接口（API）测试 |
| playwright | UI 自动化（传统选择器定位，Python 版）|
| Midscene.js | AI 视觉驱动 UI 测试（自然语言操作页面，Node 版）|
| allure | 测试报告 |

> 本项目为 **Python + Node 混合框架**：Python 侧负责 pytest + requests + playwright；
> Node 侧负责 Midscene.js 的 AI 视觉 UI 测试（需多模态大模型 API Key）。

## 目录结构

```
aitojoy-api-autotest/
├── config/settings.py        # 配置加载（.env + data/config.yaml）
├── common/                   # 公共封装
│   ├── http_client.py        # requests 封装（自动 Allure 附件）
│   ├── logger.py             # 日志
│   └── assertions.py         # 断言工具（状态码/JsonPath/包含）
├── api/login_api.py          # 接口对象层（API Object）
├── data/                     # 测试数据（yaml）
├── testcases/
│   ├── api/                  # requests 接口测试用例
│   └── ui/                   # playwright UI 测试用例
├── midscene/                 # Midscene.js AI UI 测试
│   ├── fixture.ts            # 注入 AI 能力的 playwright fixture
│   ├── tests/login.spec.ts   # AI 测试用例（代码方式）
│   └── yaml/login.yaml       # AI 测试脚本（零代码 YAML 方式）
├── conftest.py               # pytest 全局 fixture
├── pytest.ini                # pytest 配置
├── requirements.txt          # Python 依赖
├── package.json              # Node / Midscene 依赖
└── playwright.config.ts      # Midscene playwright 配置
```

## 环境准备

### 1. Python 环境（接口 + playwright UI）

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 playwright 浏览器
playwright install chromium
```

### 2. Node 环境（Midscene.js AI UI）

```bash
# Node 18+ 环境
npm install
npx playwright install chromium
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入被测地址、测试账号、大模型 API Key
```

## 运行测试

### 接口 + playwright UI 测试（Python）

```bash
# 全部用例
pytest

# 仅接口用例
pytest -m api

# 仅 UI 用例
pytest -m ui

# 仅冒烟用例
pytest -m smoke
```

### AI 视觉 UI 测试（Midscene.js）

```bash
# 代码方式（playwright + Midscene）
npm run test:ai

# 零代码方式（YAML 脚本）
npx midscene ./midscene/yaml/login.yaml
```

## 测试报告（Allure）

```bash
# 生成并打开报告
allure serve reports/allure-results
```

## 说明

- 示例用例（登录接口/登录页）为框架演示，运行前请将 `data/config.yaml`、
  `api/login_api.py` 中的地址与接口路径替换为真实环境。
- Midscene.js 支持 OpenAI / 通义千问(qwen-vl) / 豆包 等多模态大模型，
  模型配置见 `.env`，详见 https://midscenejs.com 。
```
