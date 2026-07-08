"""
股权资产管理查询工具 - 配置（四表联查）
集中管理接口地址、默认鉴权、查询条件、四张表的字段映射与展示列
"""

# ===== 环境配置 =====
ENVIRONMENTS = {
    "production": {
        "label": "生产环境",
        "base_url": "https://cloud.zidayun.com",
        "tenant": "e5b7a28fea70b234556fba5ba7723281",
    },
    "test": {
        "label": "测试环境",
        "base_url": "https://test-cloud.zidayun.com",
        "tenant": "e0c5a9f2393fad79dfb0e5a3915d3e7d",
    },
}

# 默认环境（可通过页面开关切换）
DEFAULT_ENV = "test"

# ===== 接口地址（根据环境动态获取）=====
API_URL = "https://cloud.zidayun.com/tojoy-form-engine/data/listPageDataManage"
APP_ID = "3ae74d7a2c3da305929fc94c984e6f16"

# ===== 登录接口 =====
LOGIN_URL = "https://cloud.zidayun.com/tojoy-uaa/oauth/token"


def get_api_url(env="production"):
    """根据环境获取数据查询接口地址"""
    base = ENVIRONMENTS.get(env, ENVIRONMENTS["production"])["base_url"]
    return f"{base}/tojoy-form-engine/data/listPageDataManage"


def get_login_url(env="production"):
    """根据环境获取登录接口地址"""
    base = ENVIRONMENTS.get(env, ENVIRONMENTS["production"])["base_url"]
    return f"{base}/tojoy-uaa/oauth/token"
LOGIN_PARAMS = {
    "nationalCode": "86",
    "mobile": "13622034186",
    "password": "daming123",
    "autoLogin": "false",
    "grant_type": "password",
    "scope": "all",
    "client_id": "tojoy",
    "client_secret": "tojoy_secret",
    "language": "zh-CN",
    "platformType": "TENANT",
    "loginPlatformType": "1",
}

# ===== 固定租户（根据环境动态获取）=====
DEFAULT_TENANT = "e5b7a28fea70b234556fba5ba7723281"


def get_tenant(env="production"):
    """根据环境获取租户ID"""
    return ENVIRONMENTS.get(env, ENVIRONMENTS["production"])["tenant"]

# ===== 三个查询条件（页面统一输入，各表映射到各自字段）=====
# key 为前端字段名；label 为中文名（用于构造接口 condition 的 name）
QUERY_LABELS = {
    "projectName": "项目名称",
    "projectNo": "项目编号",
    "tjHoldingSubject": "天九持股主体",
    "tjCreditCode": "天九持股主体统一社会信用代码",
}

# ---- 台账表 selectFields ----
_LEDGER_SELECT = [
    "serial_2f28df", "number_8e6771", "input_36c323", "input_02c3ca",
    "input_c31c2bm03734eb", "input_195656m037hs3h", "project_company_main_name",
    "select_fa5c4a", "date_0f5998", "input_eeb48c", "department_97b14a",
    "input_15fbdf", "textarea_641ec2", "textarea_d101f8", "shareholding_status",
    "select_0aeab3", "select_3760f8", "number_23536c", "number_6c376a",
    "agreement_subject_company", "ultimately_subject_company", "input_adb4f3",
    "select_55f5ca", "input_ca66f4", "corporation", "center", "contract_no",
    "create_by", "create_time", "update_by", "update_time",
    "project_company_main_code", "agreement_subject_company_code",
    "ultimately_subject_company_code", "system_type", "id",
    "input_2c2b00_uscc", "agreement_subject_company_uscc",
    "ultimately_subject_company_uscc", "project_company_main_uscc",
    "create_by_name", "update_by_name",
    # 协议内容
    "input_962d5c", "input_467cfd", "input_362c46", "input_0c698a",
    "date_3cddf3", "number_4ed0e2", "number_f2d589", "number_f2c0ad",
    "number_52c964", "number_0e966f", "number_7ba4a6",
    # 工商信息
    "number_8af4dc", "number_49b516", "number_47e399", "number_febc56",
    "number_5fff96", "number_b577e1", "number_500f42", "number_34c4e6",
    # 历史账载
    "date_07ef70", "number_25a837", "number_bfab68", "number_5dfffd",
    "number_d05245", "number_6ab9b9", "number_523233", "number_407550",
    "number_6984a3",
    # 期末
    "date_1e473f", "number_927c93", "number_b2c5ec", "number_f231c7",
    "number_d0da8e", "number_0a0717", "number_0e7eda", "number_27a451",
    "number_8c3206", "textarea_cc2a4b",
    # 其他
    "number_e7b076", "number_baf6be",
]

# ---- 台账表导入模板列映射（按导入模板顺序，用于测试环境导出） ----
# 每项: (模板列名, 台账字段名, 字段类型)
LEDGER_IMPORT_TEMPLATE_COLS = [
    ("序号(必填)", "number_8e6771", "number"),
    ("项目编号(非必填)", "input_36c323", "text"),
    ("项目归档编号", "input_02c3ca", "text"),
    ("项目名称(必填)", "input_c31c2bm03734eb", "text"),
    ("项目归档名称", "input_0c698a", "text"),
    ("项目公司主体名称编码(非必填)", "project_company_main_code", "text"),
    ("项目公司主体名称(必填)", "project_company_main_name", "text"),
    ("项目公司主体名称统一社会信用代码(非必填)", "project_company_main_uscc", "text"),
    ("主体编号(非必填)", "input_15fbdf", "text"),
    ("天九持股主体(必填)", "input_195656m037hs3h", "text"),
    ("持股主体统一社会信用代码(非必填)", "input_2c2b00_uscc", "text"),
    ("天九持股主体体系", "system_type", "label"),
    ("股权价值变动方式(必填)", "select_fa5c4a", "label"),
    ("摘要", "textarea_641ec2", "text"),
    ("差异原因", "textarea_d101f8", "text"),
    ("持股状态(必填)", "shareholding_status", "label"),
    ("持股类型", "select_0aeab3", "label"),
    ("协议股权价值变动方式", "select_3760f8", "label"),
    ("协议归档编号", "input_362c46", "text"),
    ("协议日期", "date_3cddf3", "date"),
    ("转让方/减资方公司编码", "input_467cfd", "text"),
    ("转让方/减资方", "input_962d5c", "text"),
    ("转让方/减资方公司统一社会信用代码", None, "text"),
    ("协议标的公司编码(非必填)", "agreement_subject_company_code", "text"),
    ("协议标的公司(必填)", "agreement_subject_company", "text"),
    ("协议标的公司统一社会信用代码(非必填)", "agreement_subject_company_uscc", "text"),
    ("受让方/增资方", "input_adb4f3", "text"),
    ("协议估值（万元）", "number_4ed0e2", "number"),
    ("协议签署股权比例（%）", "number_f2d589", "number"),
    ("累计协议签署股权比例（%）", "number_f2c0ad", "number"),
    ("协议金额（万元）", "number_52c964", "number"),
    ("最终标的公司编码(非必填)", "ultimately_subject_company_code", "text"),
    ("最终标的公司(必填)", "ultimately_subject_company", "text"),
    ("最终标的公司统一社会信用代码(非必填)", "ultimately_subject_company_uscc", "text"),
    ("协议标的公司持有最终标的公司股权比例（%）", "number_0e966f", "number"),
    (" 天九持有最终标的公司股权（%）", "number_7ba4a6", "number"),
    ("本地协议", None, "text"),
    ("工商变更日期", "date_0f5998", "date"),
    ("协议标的公司注册资本（万元）", "number_8af4dc", "number"),
    ("协议标的公司工商变更比例（%）", "number_49b516", "number"),
    (" 协议标的公司工商变更后比例（%）", "number_47e399", "number"),
    (" 协议标的公司工商未变更比例（%）", "number_febc56", "number"),
    ("天九认缴资金（万元）", "number_5fff96", "number"),
    ("天九实缴资金（万元）", "number_b577e1", "number"),
    (" 协议标的公司持有最终标的公司股权（%）", "number_500f42", "number"),
    (" 天九持有最终标的公司股权（%）", "number_34c4e6", "number"),
    ("历史账载日期", "date_07ef70", "date"),
    ("项目估值（元）", "number_25a837", "number"),
    (" 历史账载股权比例（%）", "number_bfab68", "number"),
    ("投资成本（元）", "number_5dfffd", "number"),
    ("公允价值变动（元）", "number_d05245", "number"),
    ("资产减值损失（元）", "number_6ab9b9", "number"),
    ("投资损益（元）", "number_523233", "number"),
    ("公允价值变动损益（元）", "number_407550", "number"),
    ("资产减值损失（损益）（元）", "number_6984a3", "number"),
    ("期末账载日期", "date_1e473f", "date"),
    ("期末账面股权比例（%）", "number_927c93", "number"),
    ("期末投资成本（元）", "number_b2c5ec", "number"),
    ("期末公允价值（元）", "number_f231c7", "number"),
    ("期末资产减值损失（元）", "number_d0da8e", "number"),
    ("期末账面价值（元）", "number_0a0717", "number"),
    ("期末累计项目投资损益（账载金额）（元）", "number_0e7eda", "number"),
    ("期末累计项目投资损益（协议金额）（元）", "number_27a451", "number"),
    ("差异（元）", "number_8c3206", "number"),
    ("原因", "textarea_cc2a4b", "text"),
    ("应收股权统计日期", None, "date"),
    ("履约完成股权比例（%）", "number_e7b076", "number"),
    ("累计履约完成股权比例（%）", "number_baf6be", "number"),
    ("导入批次号", None, "text"),
]

# ---- 天九持股主体表导入模板列映射 ----
# 模板文件：天九持股主体公司管理.xlsx
# 每项: (模板列名, 字段名, 字段类型)
HOLDING_SUBJECT_IMPORT_TEMPLATE_COLS = [
    ("天九持股主体", "input_195656", "text"),
    ("统一社会信用代码", "uscc", "text"),
    ("公司曾用名", None, "text"),
    ("曾用名详细", None, "text"),
    ("体系", "system_type", "label"),
    ("单行文本", None, "text"),
]

# ---- 股权历史表导入模板列映射 ----
# 模板文件：股权资产管理历史数据（25年之前的项目股权资产数据）.xlsx
HISTORY_IMPORT_TEMPLATE_COLS = [
    ("项目编号", "project_no", "text"),
    ("项目名称", "project_name", "text"),
    ("项目公司名称", "project_company", "text"),
    ("项目公司统一社会信用代码", "project_company_credit_code", "text"),
    ("天九持股主体", "tojoy_stock", "text"),
    ("天九持股主体统一社会信用代码", "tojoy_stock_credit_code", "text"),
    ("协议标的公司名称", "agreement_company", "text"),
    ("协议标的公司统一社会信用代码", "agreement_company_credit_code", "text"),
    ("项目公司（同时持有）", None, "text"),
    ("项目公司社会统一信用代码（同时持有）", None, "text"),
    ("统计月", "statistics_month", "text"),
    ("时点_无责股权", "time_point_non_liable", "number"),
    ("时点_对赌完成", "time_point_vam_complete", "number"),
    ("时点_现金投资", "time_point_cash_investment", "number"),
    ("时点_股权登记", "time_point_stock_register", "number"),
    ("时点_股权退回", "time_point_stock_return", "number"),
    ("时点_股权处置", "time_point_stock_disposal", "number"),
    ("时点_股权稀释", "time_point_stock_dilution", "number"),
    ("时点_未过户股权权益转让", None, "number"),
    ("时点_协议处置未变更", "time_point_xyczwbg", "number"),
    ("期末_无责股权", "end_period_non_liable", "number"),
    ("期末_对赌股权", "end_period_vam_stock", "number"),
    ("期末_现金投资", "end_period_cash_investment", "number"),
    ("期末_合计", "end_period_total", "number"),
    ("期末_股权登记", "end_period_stock_register", "number"),
    ("期末_预收股权", "end_period_advance_receipt_stock", "number"),
    ("期末_股权退回", "end_period_stock_return", "number"),
    ("期末_股权处置", "end_period_stock_disposal", "number"),
    ("期末_股权稀释", "end_period_stock_dilution", "number"),
    ("期末_工商比例", "end_period_registered_equity_ratio", "number"),
    ("期末_待过户股权", "end_period_dgh_stock", "number"),
    ("期末_协议处置未变更", "end_period_xyczwbg", "number"),
    ("期末_评估比例", "end_period_valuation_rate", "number"),
    ("期末_未过户股权权益转让", None, "number"),
]

# ---- 对赌/历史/月度三表 共用 selectFields ----
_GHM_SELECT = [
    "statistics_month", "project_name", "project_no", "is_concurrent_holding",
    "concurrent_holding_group_no", "concurrent_holding_number", "subproject_name",
    "subproject_no", "project_company_name", "project_company_credit_code",
    "tojoy_stock", "tojoy_stock_credit_code", "agreement_company",
    "agreement_company_credit_code", "gambling_count", "gambling_content",
    "classification", "basic_stock_rate", "confirmation_stock_rate",
    "should_confirmation_stock_rate", "complete_gambling_shareholding_ratio",
    "middle_data_id", "batch_no", "create_by", "create_by_name", "create_time",
    "update_by", "update_by_name", "update_time", "id",
]

# ---- 对赌表 专属展示列（按官方 title）----
_GAMBLE_COLUMNS = [
    {"field": "statistics_month", "label": "统计月份", "type": "date", "sortable": True},
    {"field": "project_no", "label": "项目编号", "type": "text"},
    {"field": "project_name", "label": "项目名称", "type": "text"},
    {"field": "subproject_name", "label": "子项目名称", "type": "text"},
    {"field": "subproject_no", "label": "子项目编号", "type": "text"},
    {"field": "project_company_name", "label": "获取股权公司名称", "type": "text"},
    {"field": "project_company_credit_code", "label": "项目公司主体统一社会信用代码", "type": "text"},
    {"field": "tojoy_stock", "label": "天九持股主体", "type": "text"},
    {"field": "tojoy_stock_credit_code", "label": "天九持股主体统一社会信用代码", "type": "text"},
    {"field": "agreement_company", "label": "协议标的公司名称", "type": "text"},
    {"field": "agreement_company_credit_code", "label": "协议标的公司社会统一信用代码", "type": "text"},
    {"field": "is_concurrent_holding", "label": "否同时持有", "type": "label"},
    {"field": "concurrent_holding_group_no", "label": "同时持有组号", "type": "text"},
    {"field": "concurrent_holding_number", "label": "同时持有序号", "type": "text"},
    {"field": "gambling_count", "label": "对赌数量", "type": "number"},
    {"field": "gambling_content", "label": "对赌内容", "type": "text"},
    {"field": "classification", "label": "获取分类", "type": "text"},
    {"field": "basic_stock_rate", "label": "基础股权", "type": "number"},
    {"field": "confirmation_stock_rate", "label": "确认函股权", "type": "number"},
    {"field": "should_confirmation_stock_rate", "label": "应确认股权比例", "type": "number"},
    {"field": "complete_gambling_shareholding_ratio", "label": "完成对赌可获取的股权比例/股份数", "type": "number"},
    {"field": "create_by_name", "label": "创建人", "type": "text"},
    {"field": "create_time", "label": "创建时间", "type": "date"},
    {"field": "update_by_name", "label": "更新人", "type": "text"},
    {"field": "update_time", "label": "更新时间", "type": "date"},
]

# ---- 月度表展示列（按官方 title，统计月最左，只保留期末系列）----
_MONTHLY_SELECT = [
    "statistics_month", "project_no", "project_name", "project_company",
    "project_company_credit_code", "tojoy_stock", "tojoy_stock_credit_code",
    "agreement_company", "agreement_company_credit_code",
    "time_point_non_liable", "time_point_vam_complete", "time_point_cash_investment",
    "time_point_stock_register", "time_point_stock_return", "time_point_stock_disposal",
    "time_point_stock_dilution", "time_point_xyczwbg", "time_point_not_transfer_stock_right_rate",
    "end_period_non_liable", "end_period_vam_stock", "end_period_cash_investment",
    "end_period_total", "end_period_stock_register", "end_period_stock_return",
    "end_period_stock_disposal", "end_period_advance_receipt_stock",
    "end_period_stock_dilution", "end_period_registered_equity_ratio",
    "end_period_dgh_stock", "end_period_xyczwbg", "end_period_valuation_rate",
    "end_period_not_transfer_stock_right_rate",
    "create_by", "create_by_name", "create_time",
    "update_by", "update_by_name", "update_time", "id",
]

_MONTHLY_COLUMNS = [
    {"field": "statistics_month", "label": "统计月", "type": "date", "sortable": True},
    {"field": "project_no", "label": "项目编号", "type": "text"},
    {"field": "project_name", "label": "项目名称", "type": "text"},
    {"field": "project_company", "label": "项目公司名称", "type": "text"},
    {"field": "project_company_credit_code", "label": "项目公司统一社会信用代码", "type": "text"},
    {"field": "tojoy_stock", "label": "天九持股主体", "type": "text"},
    {"field": "tojoy_stock_credit_code", "label": "天九持股主体统一社会信用代码", "type": "text"},
    {"field": "agreement_company", "label": "协议标的公司名称", "type": "text"},
    {"field": "agreement_company_credit_code", "label": "协议标的公司统一社会信用代码", "type": "text"},
    {"field": "time_point_non_liable", "label": "时点_无责股权", "type": "number"},
    {"field": "time_point_vam_complete", "label": "时点_对赌完成", "type": "number"},
    {"field": "time_point_cash_investment", "label": "时点_现金投资", "type": "number"},
    {"field": "time_point_stock_register", "label": "时点_股权登记", "type": "number"},
    {"field": "time_point_stock_return", "label": "时点_股权退回", "type": "number"},
    {"field": "time_point_stock_disposal", "label": "时点_股权处置", "type": "number"},
    {"field": "time_point_stock_dilution", "label": "时点_股权稀释", "type": "number"},
    {"field": "time_point_xyczwbg", "label": "时点_协议处置未变更", "type": "number"},
    {"field": "time_point_not_transfer_stock_right_rate", "label": "时点_未过户股权权益转让", "type": "number"},
    {"field": "end_period_non_liable", "label": "期末_无责股权", "type": "number"},
    {"field": "end_period_vam_stock", "label": "期末_对赌股权", "type": "number"},
    {"field": "end_period_cash_investment", "label": "期末_现金投资", "type": "number"},
    {"field": "end_period_total", "label": "期末_合计", "type": "number"},
    {"field": "end_period_stock_register", "label": "期末_股权登记", "type": "number"},
    {"field": "end_period_stock_return", "label": "期末_股权退回", "type": "number"},
    {"field": "end_period_stock_disposal", "label": "期末_股权处置", "type": "number"},
    {"field": "end_period_advance_receipt_stock", "label": "期末_预收股权", "type": "number"},
    {"field": "end_period_stock_dilution", "label": "期末_股权稀释", "type": "number"},
    {"field": "end_period_registered_equity_ratio", "label": "期末_工商比例", "type": "number"},
    {"field": "end_period_dgh_stock", "label": "期末_待过户股权", "type": "number"},
    {"field": "end_period_xyczwbg", "label": "期末_协议处置未变更", "type": "number"},
    {"field": "end_period_valuation_rate", "label": "期末_评估比例", "type": "number"},
    {"field": "end_period_not_transfer_stock_right_rate", "label": "期末_未过户股权权益转让", "type": "number"},
    {"field": "create_by_name", "label": "创建人", "type": "text"},
    {"field": "create_time", "label": "创建时间", "type": "date"},
    {"field": "update_by_name", "label": "更新人", "type": "text"},
    {"field": "update_time", "label": "更新时间", "type": "date"},
]

# ---- 股权历史表 专属 selectFields（顺序按前端实际请求）----
_HISTORY_SELECT = [
    "project_no", "project_name", "project_company", "project_company_credit_code",
    "tojoy_stock", "tojoy_stock_credit_code", "agreement_company",
    "agreement_company_credit_code", "statistics_month",
    "time_point_non_liable", "time_point_vam_complete", "time_point_cash_investment",
    "time_point_stock_register", "time_point_stock_return", "time_point_stock_disposal",
    "time_point_stock_dilution", "time_point_xyczwbg",
    "end_period_non_liable", "end_period_vam_stock", "end_period_cash_investment",
    "end_period_total", "end_period_stock_register", "end_period_advance_receipt_stock",
    "end_period_stock_return", "end_period_stock_disposal", "end_period_stock_dilution",
    "end_period_registered_equity_ratio", "end_period_dgh_stock", "end_period_xyczwbg",
    "end_period_valuation_rate",
    "create_by", "create_by_name", "create_time",
    "update_by", "update_by_name", "update_time", "id",
]

# ---- 股权历史表 展示列（顺序与 selectFields 一致）----
# 注：time_point_/end_period_ 系列为业务口径，标签为最佳推断，可按实际口径修改
_HISTORY_COLUMNS = [
    {"field": "statistics_month", "label": "统计月", "type": "month"},
    {"field": "project_no", "label": "项目编号", "type": "text"},
    {"field": "project_name", "label": "项目名称", "type": "text"},
    {"field": "project_company", "label": "项目公司名称", "type": "text"},
    {"field": "project_company_credit_code", "label": "项目公司统一社会信用代码", "type": "text"},
    {"field": "tojoy_stock", "label": "天九持股主体", "type": "text"},
    {"field": "tojoy_stock_credit_code", "label": "天九持股主体统一社会信用代码", "type": "text"},
    {"field": "agreement_company", "label": "协议标的公司名称", "type": "text"},
    {"field": "agreement_company_credit_code", "label": "协议标的公司统一社会信用代码", "type": "text"},
    {"field": "end_period_non_liable", "label": "期末_无责股权", "type": "number"},
    {"field": "end_period_vam_stock", "label": "期末_对赌股权", "type": "number"},
    {"field": "end_period_cash_investment", "label": "期末_现金投资", "type": "number"},
    {"field": "end_period_total", "label": "期末_合计", "type": "number"},
    {"field": "end_period_stock_register", "label": "期末_股权登记", "type": "number"},
    {"field": "end_period_advance_receipt_stock", "label": "期末_预收股权", "type": "number"},
    {"field": "end_period_stock_return", "label": "期末_股权退回", "type": "number"},
    {"field": "end_period_stock_disposal", "label": "期末_股权处置", "type": "number"},
    {"field": "end_period_stock_dilution", "label": "期末_股权稀释", "type": "number"},
    {"field": "end_period_registered_equity_ratio", "label": "期末_工商比例", "type": "number"},
    {"field": "end_period_dgh_stock", "label": "期末_待过户股权", "type": "number"},
    {"field": "end_period_xyczwbg", "label": "期末_协议处置未变更", "type": "number"},
    {"field": "end_period_valuation_rate", "label": "期末_评估比例", "type": "number"},
    {"field": "create_by_name", "label": "创建人", "type": "text"},
    {"field": "create_time", "label": "创建时间", "type": "date"},
    {"field": "update_by_name", "label": "更新人", "type": "text"},
    {"field": "update_time", "label": "更新时间", "type": "date"},
]

# ===== 四张表定义 =====
TABLES = [
    {
        "key": "ledger",
        "name": "台账表",
        "formId": "5fe04116f79b468a87edc1e5e6ae5797",
        "freeze": 0,
        "queryFields": {
            "projectName": "input_c31c2bm03734eb",
            "projectNo": "input_36c323",
            "tjHoldingSubject": "input_195656m037hs3h",
            "tjCreditCode": "input_2c2b00_uscc",
        },
        "selectFields": _LEDGER_SELECT,
        "columns": [
            # --- 1. 项目基本信息 ---
            {"field": "number_8e6771", "label": "序号", "type": "number", "group": "项目基本信息"},
            {"field": "input_36c323", "label": "项目编号", "type": "text", "group": "项目基本信息"},
            {"field": "input_c31c2bm03734eb", "label": "项目名称", "type": "text", "group": "项目基本信息"},
            {"field": "project_company_main_code", "label": "项目公司主体编码", "type": "text", "group": "项目基本信息", "hidden": True},
            {"field": "project_company_main_name", "label": "项目公司主体名称", "type": "text", "group": "项目基本信息"},
            {"field": "project_company_main_uscc", "label": "项目公司主体统一社会信用代码", "type": "text", "group": "项目基本信息"},
            {"field": "input_15fbdf", "label": "主体编号", "type": "text", "group": "项目基本信息", "hidden": True},
            {"field": "input_195656m037hs3h", "label": "天九持股主体", "type": "text", "group": "项目基本信息"},
            {"field": "input_2c2b00_uscc", "label": "持股主体统一社会信用代码", "type": "text", "group": "项目基本信息"},
            {"field": "system_type", "label": "天九持股主体体系", "type": "label", "group": "项目基本信息"},
            {"field": "textarea_641ec2", "label": "摘要", "type": "text", "group": "项目基本信息", "hidden": True},
            # --- 2. 协议内容 ---
            {"field": "shareholding_status", "label": "持股状态", "type": "label", "group": "协议内容"},
            {"field": "select_0aeab3", "label": "持股类型", "type": "label", "group": "协议内容"},
            {"field": "select_3760f8", "label": "协议股权价值变动方式", "type": "label", "group": "协议内容"},
            {"field": "input_362c46", "label": "协议归档编号", "type": "text", "group": "协议内容", "hidden": True},
            {"field": "date_3cddf3", "label": "协议日期", "type": "date", "group": "协议内容"},
            {"field": "number_4ed0e2", "label": "协议估值（万元）", "type": "number", "group": "协议内容"},
            {"field": "input_962d5c", "label": "转让方/减资方", "type": "text", "group": "协议内容"},
            {"field": "agreement_subject_company_code", "label": "协议标的公司编码", "type": "text", "group": "协议内容", "hidden": True},
            {"field": "agreement_subject_company", "label": "协议标的公司", "type": "text", "group": "协议内容"},
            {"field": "agreement_subject_company_uscc", "label": "协议标的公司统一社会信用代码", "type": "text", "group": "协议内容"},
            {"field": "ultimately_subject_company_code", "label": "最终标的公司编码", "type": "text", "group": "协议内容", "hidden": True},
            {"field": "ultimately_subject_company", "label": "最终标的公司", "type": "text", "group": "协议内容"},
            {"field": "ultimately_subject_company_uscc", "label": "最终标的公司统一社会信用代码", "type": "text", "group": "协议内容"},
            {"field": "input_adb4f3", "label": "受让方/增资方", "type": "text", "group": "协议内容"},
            {"field": "number_f2d589", "label": "协议签署股权比例（%）", "type": "number", "group": "协议内容"},
            {"field": "number_f2c0ad", "label": "累计协议签署股权比例（%）", "type": "number", "group": "协议内容"},
            {"field": "number_52c964", "label": "协议金额（万元）", "type": "number", "group": "协议内容"},
            {"field": "number_0e966f", "label": "协议标的公司持有最终标的公司股权比例（%）", "type": "number", "group": "协议内容"},
            {"field": "number_7ba4a6", "label": "天九持有最终标的公司股权（%）", "type": "number", "group": "协议内容"},
            {"field": "childForm_078dc9", "label": "合同明细", "type": "text", "group": "协议内容", "hidden": True},
            {"field": "childForm_4bd511", "label": "本地协议", "type": "text", "group": "协议内容", "hidden": True},
            # --- 3. 项目主体工商信息 ---
            {"field": "date_0f5998", "label": "工商变更日期", "type": "date", "group": "项目主体工商信息"},
            {"field": "number_8af4dc", "label": "注册资本（万元）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_49b516", "label": "协议标的公司工商变更比例（%）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_47e399", "label": "协议标的公司工商变更后比例（%）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_febc56", "label": "协议标的公司工商未变更比例（%）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_5fff96", "label": "天九认缴资金（万元）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_b577e1", "label": "天九实缴资金（万元）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_500f42", "label": "协议标的公司持有最终标的公司股权（%）", "type": "number", "group": "项目主体工商信息"},
            {"field": "number_34c4e6", "label": "工商登记的天九持有最终标的公司股权（%）", "type": "number", "group": "项目主体工商信息"},
            # --- 4. 历史账载信息 ---
            {"field": "date_07ef70", "label": "历史账载日期", "type": "date", "group": "历史账载信息"},
            {"field": "number_25a837", "label": "项目估值（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_bfab68", "label": "历史账载股权比例（%）", "type": "number", "group": "历史账载信息"},
            {"field": "number_5dfffd", "label": "投资成本（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_d05245", "label": "公允价值变动（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_6ab9b9", "label": "资产减值损失（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_523233", "label": "投资损益（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_407550", "label": "公允价值变动损益（元）", "type": "number", "group": "历史账载信息"},
            {"field": "number_6984a3", "label": "资产减值损失（损益）（元）", "type": "number", "group": "历史账载信息"},
            # --- 5. 期末账面价值 ---
            {"field": "date_1e473f", "label": "期末账载日期", "type": "date", "group": "期末账面价值"},
            {"field": "number_927c93", "label": "期末账面股权比例（%）", "type": "number", "group": "期末账面价值"},
            {"field": "number_b2c5ec", "label": "期末投资成本（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_f231c7", "label": "期末公允价值（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_0a0717", "label": "期末账面价值（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_d0da8e", "label": "期末资产减值损失（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_0e7eda", "label": "期末累计项目投资损益（账载金额）（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_27a451", "label": "期末累计项目投资损益（协议金额）（元）", "type": "number", "group": "期末账面价值"},
            {"field": "number_8c3206", "label": "差异（元）", "type": "number", "group": "期末账面价值"},
            {"field": "textarea_cc2a4b", "label": "原因", "type": "text", "group": "期末账面价值"},
            # --- 6. 系统信息 ---
            {"field": "create_by_name", "label": "创建人", "type": "text", "group": "系统信息"},
            {"field": "create_time", "label": "创建时间", "type": "date", "group": "系统信息"},
            {"field": "update_by_name", "label": "更新人", "type": "text", "group": "系统信息"},
            {"field": "update_time", "label": "更新时间", "type": "date", "group": "系统信息"},
        ],
    },
    {
        "key": "gamble",
        "name": "项目对赌表",
        "formId": "1eeeca3286ad445f98a60e571b09958a",
        "freeze": 3,
        "queryFields": {
            "projectName": "project_name",
            "projectNo": "project_no",
            "tjHoldingSubject": "tojoy_stock",
            "tjCreditCode": "tojoy_stock_credit_code",
        },
        "selectFields": _GHM_SELECT,
        "columns": _GAMBLE_COLUMNS,
    },
    {
        "key": "history",
        "name": "股权历史表",
        "formId": "433011f3e6454bbf9735bb39f643b6c1",
        "freeze": 3,
        "queryFields": {
            "projectName": "project_name",
            "projectNo": "project_no",
            "tjHoldingSubject": "tojoy_stock",
            "tjCreditCode": "tojoy_stock_credit_code",
        },
        "selectFields": _HISTORY_SELECT,
        "columns": _HISTORY_COLUMNS,
    },
    {
        "key": "monthly",
        "name": "股权月度表",
        "formId": "d9568ac212c945959937386d9a9f0b41",
        "freeze": 3,
        "queryFields": {
            "projectName": "project_name",
            "projectNo": "project_no",
            "tjHoldingSubject": "tojoy_stock",
            "tjCreditCode": "tojoy_stock_credit_code",
        },
        "selectFields": _MONTHLY_SELECT,
        "columns": _MONTHLY_COLUMNS,
    },
    {
        "key": "holding_subject",
        "name": "天九持股主体",
        "formId": "56eb6fb198bf4a4a9882262749409c43",
        "freeze": 0,
        "mini": True,
        "queryFields": {
            "tjHoldingSubject": "input_195656",
            "tjCreditCode": "uscc",
        },
        "selectFields": [
            "serial_a0d3e1", "input_195656", "uscc", "system_type",
            "create_by", "create_by_name", "create_time",
            "update_by", "update_by_name", "update_time", "id",
        ],
        "columns": [
            {"field": "serial_a0d3e1", "label": "编号", "type": "text"},
            {"field": "input_195656", "label": "天九持股主体", "type": "text"},
            {"field": "uscc", "label": "统一社会信用代码", "type": "text"},
            {"field": "system_type", "label": "体系类型", "type": "label"},
            {"field": "create_by_name", "label": "创建人", "type": "text"},
            {"field": "create_time", "label": "创建时间", "type": "date"},
            {"field": "update_by_name", "label": "更新人", "type": "text"},
            {"field": "update_time", "label": "更新时间", "type": "date"},
        ],
    },
    {
        "key": "project_company",
        "name": "项目所属公司管理",
        "formId": "d33f5c831bf34c5c9a1f2059e91c3ca7",
        "freeze": 0,
        "mini": True,
        "queryFields": {},
        "selectFields": [
            "code", "subject_company_name", "uscc", "is_overseas", "input_bb024d",
            "create_by", "create_by_name", "create_time",
            "update_by", "update_by_name", "update_time", "id",
        ],
        "columns": [
            {"field": "code", "label": "编号", "type": "text"},
            {"field": "subject_company_name", "label": "项目所属公司名称", "type": "text"},
            {"field": "uscc", "label": "统一社会信用代码", "type": "text"},
            {"field": "is_overseas", "label": "是否境外", "type": "label"},
            {"field": "create_by_name", "label": "创建人", "type": "text"},
            {"field": "create_time", "label": "创建时间", "type": "date"},
            {"field": "update_by_name", "label": "更新人", "type": "text"},
            {"field": "update_time", "label": "更新时间", "type": "date"},
        ],
    },
]

TABLE_MAP = {t["key"]: t for t in TABLES}
