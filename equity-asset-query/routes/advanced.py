"""
高级功能路由模块
包含股权登记比例计算、对赌判断、对赌计算等高级功能路由。
"""
import requests
from flask import Blueprint, request, jsonify

import config
from shared import _current_env, _add_log, ensure_valid_token, get_token, friendly_error
from utils import _parse_date_to_str, _safe_number

advanced_bp = Blueprint('advanced', __name__)


@advanced_bp.route("/api/advanced/equity-register", methods=["POST"])
def calc_equity_register():
    """
    高级功能：计算月度表股权登记比例
    前置条件：四要素 + 工商变更日期 -> 匹配台账 -> 匹配月度表 -> 计算
    """
    body = request.get_json(force=True) or {}
    project_no = (body.get("projectNo") or "").strip()
    project_company_uscc = (body.get("projectCompanyUscc") or "").strip()
    holding_subject_uscc = (body.get("holdingSubjectUscc") or "").strip()
    agreement_company_uscc = (body.get("agreementCompanyUscc") or "").strip()
    biz_change_date = (body.get("bizChangeDate") or "").strip()

    # 校验输入
    missing = []
    if not project_no:
        missing.append("项目编号")
    if not project_company_uscc:
        missing.append("项目公司主体统一社会信用代码")
    if not holding_subject_uscc:
        missing.append("持股主体统一社会信用代码")
    if not agreement_company_uscc:
        missing.append("协议标的公司统一社会信用代码")
    if not biz_change_date:
        missing.append("工商变更日期")
    if missing:
        return jsonify({"ok": False, "msg": f"缺少必填项：{'、'.join(missing)}"})

    # 确保 token
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"})

    headers = {"Content-Type": "application/json", "Tj-Auth": token, "Tojoy-Tenant": tenant}
    api_url = config.get_api_url(_current_env["value"])

    # ===== 第一步：查台账表，用四要素精确匹配 =====
    ledger_table = config.TABLE_MAP["ledger"]
    ledger_conditions = [
        {"name": "项目编号", "field": "input_36c323", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "input_36c323", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司主体统一社会信用代码", "field": "project_company_main_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_main_uscc", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "持股主体统一社会信用代码", "field": "input_2c2b00_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "input_2c2b00_uscc", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_subject_company_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_subject_company_uscc", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    ledger_payload = {
        "filterRule": {
            "formId": ledger_table["formId"],
            "selectFields": ledger_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": ledger_conditions}],
            "sorts": [],
        },
        "formId": ledger_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 50,
        "pageNo": 1,
    }

    _add_log("info", "高级①输入", f"项目编号={project_no}, 工商变更日期={biz_change_date}")
    try:
        resp = requests.post(api_url, json=ledger_payload, headers=headers, timeout=30)
        ledger_data = resp.json()
    except Exception as e:
        _add_log("error", "高级①失败", friendly_error(e))
        return jsonify({"ok": False, "msg": f"台账查询请求失败：{friendly_error(e)}"})

    if ledger_data.get("code") != 200:
        msg = ledger_data.get("msg") or "台账查询失败"
        return jsonify({"ok": False, "msg": f"台账查询失败：{msg}"})

    ledger_records = (ledger_data.get("data") or {}).get("records", [])
    if not ledger_records:
        _add_log("warn", "高级②台账匹配", "四要素未匹配到记录")
        return jsonify({"ok": False, "msg": "台账表中未找到满足四要素条件的记录"})

    _add_log("info", "高级②台账匹配", f"四要素匹配到{len(ledger_records)}条，匹配工商变更年月={biz_change_date[:7]}")

    # 在返回的记录中，过滤工商变更日期不为空的记录
    matched_ledger = None
    input_date_ym = biz_change_date[:7]  # 取年月 "2025-01"

    for record in ledger_records:
        # 获取工商变更日期字段
        date_val = record.get("date_0f5998")
        if not date_val:
            continue
        # 日期可能是时间戳(毫秒)或字符串
        record_date_str = _parse_date_to_str(date_val)
        if not record_date_str:
            continue
        # 比较年月
        record_ym = record_date_str[:7]
        if record_ym == input_date_ym:
            matched_ledger = record
            break

    if not matched_ledger:
        existing_dates = []
        for r in ledger_records:
            d = r.get("date_0f5998")
            if d:
                ds = _parse_date_to_str(d)
                if ds:
                    existing_dates.append(ds)
        hint = f"台账中已有工商变更日期：{', '.join(existing_dates)}" if existing_dates else "台账中无工商变更日期记录"
        _add_log("warn", "高级②日期匹配", f"未找到年月={input_date_ym}的记录。{hint}")
        return jsonify({"ok": False, "msg": f"台账表中未找到工商变更日期年月为 {input_date_ym} 的记录。{hint}"})

    # ===== 第二步：前置条件校验 =====
    # 1. 天九持股主体体系(system_type)必须为"体系内"
    system_type_raw = matched_ledger.get("system_type")
    system_type = ""
    if isinstance(system_type_raw, dict):
        system_type = system_type_raw.get("label", "")
    elif isinstance(system_type_raw, str):
        system_type = system_type_raw

    if system_type != "体系内":
        _add_log("warn", "高级③前置校验", f"体系={system_type or '空'}，非体系内，终止")
        return jsonify({
            "ok": False,
            "msg": f"不满足计算条件：天九持股主体体系为「{system_type or '空'}」，需为「体系内」"
        })

    # 2. 工商变更日期必须大于 2024-12-31
    matched_date_str = _parse_date_to_str(matched_ledger.get("date_0f5998"))
    if matched_date_str and matched_date_str <= "2024-12-31":
        _add_log("warn", "高级③前置校验", f"工商变更日期={matched_date_str}≤2024-12-31，终止")
        return jsonify({
            "ok": False,
            "msg": f"不满足计算条件：工商变更日期为 {matched_date_str}，需大于 2024-12-31"
        })

    _add_log("info", "高级③前置校验", f"通过：体系={system_type}, 工商变更日期={matched_date_str}")

    # ===== 第三步：根据变动方式判断计算类型 =====
    change_type_raw = matched_ledger.get("select_fa5c4a")
    change_type = ""
    if isinstance(change_type_raw, dict):
        change_type = change_type_raw.get("label", "")
    elif isinstance(change_type_raw, str):
        change_type = change_type_raw

    # 三种计算类型及其对应的变动方式和月度表字段
    CALC_TYPES = {
        "股权登记": {
            "valid_types": ["股权增资", "股权购买", "债转股", "内部受让", "红股入账", "股权置换"],
            "monthly_field": "time_point_stock_register",
            "monthly_label": "时点_股权登记",
        },
        "股权退回": {
            "valid_types": ["股权退回"],
            "monthly_field": "time_point_stock_return",
            "monthly_label": "时点_股权退回",
        },
        "股权处置": {
            "valid_types": ["股权退出", "内部转让"],
            "monthly_field": "time_point_stock_disposal",
            "monthly_label": "时点_股权处置",
        },
    }

    # 判断属于哪种计算类型
    calc_type = None
    calc_config = None
    for ct_name, ct_cfg in CALC_TYPES.items():
        if change_type in ct_cfg["valid_types"]:
            calc_type = ct_name
            calc_config = ct_cfg
            break

    if not calc_type:
        all_valid = []
        for cfg in CALC_TYPES.values():
            all_valid.extend(cfg["valid_types"])
        _add_log("warn", "高级④类型判断", f"变动方式={change_type or '空'}，不在有效范围内，终止")
        return jsonify({
            "ok": False,
            "msg": f"台账中股权价值变动方式为「{change_type or '空'}」，不满足计算条件（需为：{'、'.join(all_valid)} 之一）"
        })

    _add_log("info", "高级④类型判断", f"变动方式={change_type} → 计算类型={calc_type}, 对应月度字段={calc_config['monthly_field']}")

    # 获取持股类型
    holding_type_raw = matched_ledger.get("select_0aeab3")
    holding_type = ""
    if isinstance(holding_type_raw, dict):
        holding_type = holding_type_raw.get("label", "")
    elif isinstance(holding_type_raw, str):
        holding_type = holding_type_raw

    # 获取关键数值
    biz_change_ratio = _safe_number(matched_ledger.get("number_49b516"))
    agreement_hold_ultimate = _safe_number(matched_ledger.get("number_500f42"))

    # ===== 第四步：计算比例 =====
    if holding_type == "直接":
        equity_value = biz_change_ratio / 100
        calc_formula = f"直接持股：{calc_type} = 协议标的公司工商变更比例({biz_change_ratio}%) / 100 = {equity_value}"
    elif holding_type == "间接":
        if agreement_hold_ultimate is None or biz_change_ratio is None:
            _add_log("error", "高级⑤计算", f"间接持股字段为空: 持有最终标的={agreement_hold_ultimate}, 工商变更比例={biz_change_ratio}")
            return jsonify({
                "ok": False,
                "msg": f"间接持股计算所需字段为空：协议标的公司持有最终标的公司股权={agreement_hold_ultimate}，工商变更比例={biz_change_ratio}"
            })
        equity_value = (agreement_hold_ultimate / 100) * (biz_change_ratio / 100)
        calc_formula = (
            f"间接持股：{calc_type} = 协议标的公司持有最终标的公司股权({agreement_hold_ultimate}%) / 100 × "
            f"协议标的公司工商变更比例({biz_change_ratio}%) / 100 = {equity_value}"
        )
    else:
        _add_log("warn", "高级⑤计算", f"持股类型={holding_type or '空'}，无法计算")
        return jsonify({"ok": False, "msg": f"台账中持股类型为「{holding_type or '空'}」，无法计算（需为「直接」或「间接」）"})

    _add_log("info", "高级⑤计算", f"持股类型={holding_type}, {calc_formula}")

    # ===== 第五步：查月度表校验 =====
    monthly_table = config.TABLE_MAP["monthly"]
    monthly_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    monthly_payload = {
        "filterRule": {
            "formId": monthly_table["formId"],
            "selectFields": monthly_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": monthly_conditions}],
            "sorts": [],
        },
        "formId": monthly_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    _add_log("info", "高级⑥月度表查询", f"四要素匹配月度表, 目标统计月={input_date_ym}")
    try:
        resp2 = requests.post(api_url, json=monthly_payload, headers=headers, timeout=30)
        monthly_data = resp2.json()
    except Exception as e:
        _add_log("error", "高级⑥月度表查询", friendly_error(e))
        return jsonify({"ok": False, "msg": f"月度表查询失败：{friendly_error(e)}"})

    if monthly_data.get("code") != 200:
        return jsonify({"ok": False, "msg": f"月度表查询失败：{monthly_data.get('msg', '未知错误')}"})

    monthly_records = (monthly_data.get("data") or {}).get("records", [])

    # 在月度表中找统计月年月等于工商变更日期年月的记录
    matched_monthly = None
    monthly_field_value = None
    monthly_field_name = calc_config["monthly_field"]
    for mr in monthly_records:
        stat_month = mr.get("statistics_month")
        if not stat_month:
            continue
        stat_month_str = _parse_date_to_str(stat_month)
        if not stat_month_str:
            continue
        stat_ym = stat_month_str[:7]
        if stat_ym == input_date_ym:
            matched_monthly = mr
            monthly_field_value = _safe_number(mr.get(monthly_field_name))
            break

    # 构造返回结果
    result = {
        "ok": True,
        "calcType": calc_type,
        "monthlyField": monthly_field_name,
        "monthlyFieldLabel": calc_config["monthly_label"],
        "ledger": {
            "projectNo": project_no,
            "changeType": change_type,
            "holdingType": holding_type,
            "bizChangeDate": _parse_date_to_str(matched_ledger.get("date_0f5998")),
            "bizChangeRatio": biz_change_ratio,
            "agreementHoldUltimate": agreement_hold_ultimate,
        },
        "calcResult": {
            "equityValue": round(equity_value, 6) if equity_value is not None else None,
            "formula": calc_formula,
        },
        "monthly": None,
        "verification": None,
    }

    if matched_monthly:
        result["monthly"] = {
            "statisticsMonth": _parse_date_to_str(matched_monthly.get("statistics_month")),
            "currentValue": monthly_field_value,
            "recordId": matched_monthly.get("id"),
        }
        if monthly_field_value is not None and equity_value is not None:
            diff = abs(equity_value - monthly_field_value)
            if diff < 0.000001:
                result["verification"] = {"match": True, "msg": f"✅ 计算结果与月度表{calc_config['monthly_label']}值一致"}
                _add_log("info", "高级⑦校验", f"✅ 一致: 计算={equity_value}, 月度表={monthly_field_value}")
            else:
                result["verification"] = {
                    "match": False,
                    "msg": f"⚠️ 计算结果({equity_value:.6f}) 与月度表{calc_config['monthly_label']}当前值({monthly_field_value:.6f})不一致，差异={diff:.6f}"
                }
                _add_log("warn", "高级⑦校验", f"⚠️ 不一致: 计算={equity_value:.6f}, 月度表={monthly_field_value:.6f}, 差异={diff:.6f}")
        else:
            result["verification"] = {"match": None, "msg": f"月度表{calc_config['monthly_label']}值为空，无法校验"}
            _add_log("info", "高级⑦校验", f"月度表{calc_config['monthly_label']}值为空，无法校验")

        # ===== 第六步：期末计算校验 =====
        END_PERIOD_MAP = {
            "股权登记": {"end_field": "end_period_stock_register", "time_field": "time_point_stock_register", "label": "期末_股权登记"},
            "股权退回": {"end_field": "end_period_stock_return", "time_field": "time_point_stock_return", "label": "期末_股权退回"},
            "股权处置": {"end_field": "end_period_stock_disposal", "time_field": "time_point_stock_disposal", "label": "期末_股权处置"},
        }
        end_config = END_PERIOD_MAP.get(calc_type)
        if end_config:
            # 按统计月排序所有月度记录（从旧到新）
            sorted_months = []
            for mr in monthly_records:
                sm = mr.get("statistics_month")
                if sm:
                    sm_str = _parse_date_to_str(sm)
                    if sm_str:
                        sorted_months.append((sm_str[:7], mr))
            sorted_months.sort(key=lambda x: x[0])

            # 找当前月和上一个月的记录
            prev_monthly = None
            for idx_m, (ym, mr) in enumerate(sorted_months):
                if ym == input_date_ym and idx_m > 0:
                    prev_monthly = sorted_months[idx_m - 1][1]
                    break

            end_field = end_config["end_field"]
            time_field = end_config["time_field"]
            end_label = end_config["label"]

            # 当前月的期末值（月度表实际值）
            current_end_value = _safe_number(matched_monthly.get(end_field))
            # 当前月的时点值
            current_time_value = _safe_number(matched_monthly.get(time_field)) or 0

            if prev_monthly:
                prev_end_value = _safe_number(prev_monthly.get(end_field)) or 0
                # 期末计算值 = 上月期末 + 当月时点
                calc_end_value = prev_end_value + current_time_value
                calc_end_value_rounded = round(calc_end_value, 6)

                prev_stat_month = _parse_date_to_str(prev_monthly.get("statistics_month"))

                end_period_calc = {
                    "label": end_label,
                    "prevMonth": prev_stat_month[:7] if prev_stat_month else "-",
                    "prevEndValue": round(prev_end_value, 6),
                    "currentTimeValue": round(current_time_value, 6),
                    "calcEndValue": calc_end_value_rounded,
                    "actualEndValue": round(current_end_value, 6) if current_end_value is not None else None,
                    "formula": f"{end_label}(当月) = 上月{end_label}({prev_end_value:.6f}) + 当月{calc_config['monthly_label']}({current_time_value:.6f}) = {calc_end_value_rounded}",
                }

                # 校验期末计算值是否与月度表实际期末值一致
                if current_end_value is not None:
                    end_diff = abs(calc_end_value_rounded - current_end_value)
                    if end_diff < 0.000001:
                        end_period_calc["match"] = True
                        end_period_calc["msg"] = f"✅ {end_label}计算值与月度表一致"
                        _add_log("info", "高级⑧期末校验", f"✅ {end_label}一致: 计算={calc_end_value_rounded}, 实际={current_end_value}")
                    else:
                        end_period_calc["match"] = False
                        end_period_calc["msg"] = f"⚠️ {end_label}计算值({calc_end_value_rounded}) 与月度表实际值({current_end_value:.6f})不一致，差异={end_diff:.6f}"
                        _add_log("warn", "高级⑧期末校验", f"⚠️ {end_label}不一致: 计算={calc_end_value_rounded}, 实际={current_end_value:.6f}, 差异={end_diff:.6f}")
                else:
                    end_period_calc["match"] = None
                    end_period_calc["msg"] = f"月度表{end_label}值为空，无法校验"

                result["endPeriodCalc"] = end_period_calc
            else:
                # 月度表中找不到上一月，从历史表查找2024年数据作为上月期末
                _add_log("info", "高级⑧期末校验", f"月度表无上月数据(当前={input_date_ym})，尝试从历史表查找")
                prev_end_value_from_history = None
                prev_source_month = None
                try:
                    history_table = config.TABLE_MAP["history"]
                    history_conditions = [
                        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
                         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
                        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
                         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
                        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
                         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
                        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
                         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
                    ]
                    history_payload = {
                        "filterRule": {
                            "formId": history_table["formId"],
                            "selectFields": history_table["selectFields"],
                            "conditionGroups": [{"conditionRel": "AND", "conditions": history_conditions}],
                            "sorts": [],
                        },
                        "formId": history_table["formId"],
                        "appId": config.APP_ID,
                        "pageSize": 100,
                        "pageNo": 1,
                    }
                    resp_hist = requests.post(api_url, json=history_payload, headers=headers, timeout=30)
                    hist_data = resp_hist.json()
                    if hist_data.get("code") == 200:
                        hist_records = (hist_data.get("data") or {}).get("records", [])
                        # 筛选2024年的记录，取最新一条的期末值
                        hist_2024 = []
                        for hr in hist_records:
                            hsm = hr.get("statistics_month")
                            if not hsm:
                                continue
                            hsm_str = _parse_date_to_str(hsm)
                            if not hsm_str:
                                continue
                            hsm_ym = hsm_str[:7]
                            if "2024-01" <= hsm_ym <= "2024-12":
                                hist_2024.append((hsm_ym, hr))
                        if hist_2024:
                            hist_2024.sort(key=lambda x: x[0])
                            latest_hist = hist_2024[-1]
                            prev_end_value_from_history = _safe_number(latest_hist[1].get(end_field)) or 0
                            prev_source_month = latest_hist[0]
                            _add_log("info", "高级⑧期末校验", f"从历史表找到2024年数据: 统计月={prev_source_month}, {end_label}={prev_end_value_from_history}")
                        else:
                            _add_log("info", "高级⑧期末校验", f"历史表中未找到2024年数据")
                    else:
                        _add_log("warn", "高级⑧期末校验", f"历史表查询失败: {hist_data.get('msg', '')}")
                except Exception as e:
                    _add_log("error", "高级⑧期末校验", f"历史表查询异常: {friendly_error(e)}")

                if prev_end_value_from_history is not None:
                    # 用历史表数据计算期末
                    calc_end_value = prev_end_value_from_history + current_time_value
                    calc_end_value_rounded = round(calc_end_value, 6)

                    end_period_calc = {
                        "label": end_label,
                        "prevMonth": f"{prev_source_month}(历史表)",
                        "prevEndValue": round(prev_end_value_from_history, 6),
                        "currentTimeValue": round(current_time_value, 6),
                        "calcEndValue": calc_end_value_rounded,
                        "actualEndValue": round(current_end_value, 6) if current_end_value is not None else None,
                        "formula": f"{end_label}(当月) = 历史表{end_label}({prev_end_value_from_history:.6f}) + 当月{calc_config['monthly_label']}({current_time_value:.6f}) = {calc_end_value_rounded}",
                    }

                    # 校验
                    if current_end_value is not None:
                        end_diff = abs(calc_end_value_rounded - current_end_value)
                        if end_diff < 0.000001:
                            end_period_calc["match"] = True
                            end_period_calc["msg"] = f"✅ {end_label}计算值与月度表一致（上月来源：历史表{prev_source_month}）"
                            _add_log("info", "高级⑧期末校验", f"✅ {end_label}一致(历史表): 计算={calc_end_value_rounded}, 实际={current_end_value}")
                        else:
                            end_period_calc["match"] = False
                            end_period_calc["msg"] = f"⚠️ {end_label}计算值({calc_end_value_rounded}) 与月度表实际值({current_end_value:.6f})不一致，差异={end_diff:.6f}（上月来源：历史表{prev_source_month}）"
                            _add_log("warn", "高级⑧期末校验", f"⚠️ {end_label}不一致(历史表): 计算={calc_end_value_rounded}, 实际={current_end_value:.6f}, 差异={end_diff:.6f}")
                    else:
                        end_period_calc["match"] = None
                        end_period_calc["msg"] = f"月度表{end_label}值为空，无法校验（上月来源：历史表{prev_source_month}）"

                    result["endPeriodCalc"] = end_period_calc
                else:
                    result["endPeriodCalc"] = {
                        "label": end_label,
                        "msg": f"未找到{input_date_ym}的上月数据（月度表和历史表均无），无法计算{end_label}",
                        "match": None,
                    }
    else:
        existing_months = []
        for mr in monthly_records:
            sm = mr.get("statistics_month")
            if sm:
                s = _parse_date_to_str(sm)
                if s:
                    existing_months.append(s[:7])
        hint = f"（已有统计月：{', '.join(sorted(set(existing_months)))}）" if existing_months else ""
        result["monthly"] = {"msg": f"月度表中未找到统计月为 {input_date_ym} 的记录{hint}"}
        result["verification"] = {"match": None, "msg": "未匹配到月度表记录，仅返回计算结果"}
        _add_log("info", "高级⑦校验", f"月度表未找到统计月={input_date_ym}的记录{hint}")

    return jsonify(result)


@advanced_bp.route("/api/advanced/vam-check", methods=["POST"])
def check_vam():
    """
    高级功能：项目对赌计算 - 前置判断
    判断：
    1. 同月份+四要素的数据在对赌表里是否存在
    2. 满足四要素的项目在历史表里是否存在
    """
    body = request.get_json(force=True) or {}
    project_no = (body.get("projectNo") or "").strip()
    project_company_uscc = (body.get("projectCompanyUscc") or "").strip()
    holding_subject_uscc = (body.get("holdingSubjectUscc") or "").strip()
    agreement_company_uscc = (body.get("agreementCompanyUscc") or "").strip()
    statistics_month = (body.get("statisticsMonth") or "").strip()

    # 校验输入
    missing = []
    if not project_no:
        missing.append("项目编号")
    if not project_company_uscc:
        missing.append("项目公司主体统一社会信用代码")
    if not holding_subject_uscc:
        missing.append("持股主体统一社会信用代码")
    if not agreement_company_uscc:
        missing.append("协议标的公司统一社会信用代码")
    if not statistics_month:
        missing.append("统计月份")
    if missing:
        return jsonify({"ok": False, "msg": f"缺少必填项：{'、'.join(missing)}"})

    # 确保 token
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"})

    headers = {"Content-Type": "application/json", "Tj-Auth": token, "Tojoy-Tenant": tenant}
    api_url = config.get_api_url(_current_env["value"])
    stat_ym = statistics_month[:7]

    _add_log("info", "对赌判断①", f"项目编号={project_no}, 统计月={stat_ym}")

    # ===== 判断1：对赌表中是否存在同月份+四要素的数据 =====
    gamble_table = config.TABLE_MAP["gamble"]
    gamble_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司主体统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    gamble_payload = {
        "filterRule": {
            "formId": gamble_table["formId"],
            "selectFields": gamble_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": gamble_conditions}],
            "sorts": [],
        },
        "formId": gamble_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    gamble_exists = False
    gamble_month_exists = False
    gamble_months = []
    gamble_detail = ""

    try:
        resp = requests.post(api_url, json=gamble_payload, headers=headers, timeout=30)
        gamble_data = resp.json()
        if gamble_data.get("code") == 200:
            gamble_records = (gamble_data.get("data") or {}).get("records", [])
            if gamble_records:
                gamble_exists = True
                # 检查是否有同统计月的记录
                for gr in gamble_records:
                    gm = gr.get("statistics_month")
                    if gm:
                        gm_str = _parse_date_to_str(gm)
                        if gm_str:
                            gamble_months.append(gm_str[:7])
                            if gm_str[:7] == stat_ym:
                                gamble_month_exists = True
                gamble_months = sorted(set(gamble_months))
                if gamble_month_exists:
                    gamble_detail = f"对赌表中存在四要素匹配且统计月={stat_ym}的数据"
                else:
                    gamble_detail = f"对赌表中存在四要素匹配的数据，但无统计月={stat_ym}的记录（已有月份：{', '.join(gamble_months)}）"
            else:
                gamble_detail = "对赌表中未找到满足四要素条件的记录"
        else:
            gamble_detail = f"对赌表查询失败：{gamble_data.get('msg', '未知错误')}"
    except Exception as e:
        gamble_detail = f"对赌表查询异常：{friendly_error(e)}"
        _add_log("error", "对赌判断②对赌表", friendly_error(e))

    _add_log("info", "对赌判断②对赌表",
             f"四要素匹配={'是' if gamble_exists else '否'}, 同月={'是' if gamble_month_exists else '否'}")

    # ===== 判断2：历史表中是否存在满足四要素 + 统计月在2024年的数据 =====
    history_table = config.TABLE_MAP["history"]
    history_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    history_payload = {
        "filterRule": {
            "formId": history_table["formId"],
            "selectFields": history_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": history_conditions}],
            "sorts": [],
        },
        "formId": history_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    history_exists = False
    history_months = []
    history_detail = ""

    try:
        resp2 = requests.post(api_url, json=history_payload, headers=headers, timeout=30)
        history_data = resp2.json()
        if history_data.get("code") == 200:
            history_records = (history_data.get("data") or {}).get("records", [])
            matched_2024 = []
            for hr in history_records:
                hsm = hr.get("statistics_month")
                if not hsm:
                    continue
                hsm_text = str(hsm)
                if "2024" in hsm_text:
                    matched_2024.append(hsm_text)
            if matched_2024:
                history_exists = True
                history_months = matched_2024
                history_detail = f"历史表中存在四要素匹配且统计月含2024的数据（统计月：{', '.join(history_months)}）"
            else:
                history_detail = "历史表中未找到满足四要素 + 统计月含2024的记录"
        else:
            history_detail = f"历史表查询失败：{history_data.get('msg', '未知错误')}"
    except Exception as e:
        history_detail = f"历史表查询异常：{friendly_error(e)}"
        _add_log("error", "对赌判断③历史表", friendly_error(e))

    _add_log("info", "对赌判断③历史表", f"四要素+2024年匹配={'是' if history_exists else '否'}")

    # 判断是否可以计算：只要四要素在历史表有2024年数据就可以计算
    # 对赌表没数据时，期末字段默认为0
    can_calc = True  # 始终允许计算

    return jsonify({
        "ok": True,
        "canCalc": can_calc,
        "gamble": {
            "exists": gamble_exists,
            "monthExists": gamble_month_exists,
            "months": gamble_months,
            "detail": gamble_detail,
        },
        "history": {
            "exists": history_exists,
            "months": history_months,
            "detail": history_detail,
        },
    })


@advanced_bp.route("/api/advanced/vam-calc", methods=["POST"])
def calc_vam():
    """
    高级功能：项目对赌计算
    涉及表单：项目对赌表、股权月度表、股权历史表
    根据四要素匹配数据，计算月度表中的：
    - 期末_无责股权(end_period_non_liable) = 对赌表 basic_stock_rate / 100
    - 期末_对赌股权(end_period_vam_stock) = 对赌表 should_confirmation_stock_rate / 100
    - 时点_无责股权(time_point_non_liable) = 当月期末_无责股权 - 上年末期末_无责股权
    - 时点_对赌完成(time_point_vam_complete) = 当月期末_对赌股权 - 上年末期末_对赌股权
    """
    body = request.get_json(force=True) or {}
    project_no = (body.get("projectNo") or "").strip()
    project_company_uscc = (body.get("projectCompanyUscc") or "").strip()
    holding_subject_uscc = (body.get("holdingSubjectUscc") or "").strip()
    agreement_company_uscc = (body.get("agreementCompanyUscc") or "").strip()
    statistics_month = (body.get("statisticsMonth") or "").strip()

    # 校验输入
    missing = []
    if not project_no:
        missing.append("项目编号")
    if not project_company_uscc:
        missing.append("项目公司主体统一社会信用代码")
    if not holding_subject_uscc:
        missing.append("持股主体统一社会信用代码")
    if not agreement_company_uscc:
        missing.append("协议标的公司统一社会信用代码")
    if not statistics_month:
        missing.append("统计月份")
    if missing:
        return jsonify({"ok": False, "msg": f"缺少必填项：{'、'.join(missing)}"})

    # 确保 token1
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"})

    headers = {"Content-Type": "application/json", "Tj-Auth": token, "Tojoy-Tenant": tenant}
    api_url = config.get_api_url(_current_env["value"])

    # 提取统计月的年月（如 "2025-03"）
    stat_ym = statistics_month[:7]
    stat_year = int(stat_ym[:4])

    _add_log("info", "对赌计算①输入",
             f"项目编号={project_no}, 统计月={stat_ym}")

    # ===== 第一步：查对赌表，用四要素精确匹配 =====
    gamble_table = config.TABLE_MAP["gamble"]
    gamble_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司主体统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    gamble_payload = {
        "filterRule": {
            "formId": gamble_table["formId"],
            "selectFields": gamble_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": gamble_conditions}],
            "sorts": [],
        },
        "formId": gamble_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    try:
        resp = requests.post(api_url, json=gamble_payload, headers=headers, timeout=30)
        gamble_data = resp.json()
    except Exception as e:
        _add_log("error", "对赌计算②对赌表查询失败", friendly_error(e))
        return jsonify({"ok": False, "msg": f"对赌表查询请求失败：{friendly_error(e)}"})

    if gamble_data.get("code") != 200:
        msg = gamble_data.get("msg") or "对赌表查询失败"
        return jsonify({"ok": False, "msg": f"对赌表查询失败：{msg}"})

    gamble_records = (gamble_data.get("data") or {}).get("records", [])

    # 在对赌表记录中找到统计月匹配的那条
    matched_gamble = None
    if gamble_records:
        for gr in gamble_records:
            gm = gr.get("statistics_month")
            if not gm:
                continue
            gm_str = _parse_date_to_str(gm)
            if not gm_str:
                continue
            gm_ym = gm_str[:7]
            if gm_ym == stat_ym:
                matched_gamble = gr
                break

    # ===== 第二步：先查历史表获取2024年期末数据 =====
    _add_log("info", "对赌计算②查历史表", "查询历史表获取2024年期末数据")
    history_table = config.TABLE_MAP["history"]
    history_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    history_payload = {
        "filterRule": {
            "formId": history_table["formId"],
            "selectFields": history_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": history_conditions}],
            "sorts": [],
        },
        "formId": history_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    history_end_non_liable = 0
    history_end_vam_stock = 0
    history_source = "历史表(未查到)"

    try:
        resp_hist = requests.post(api_url, json=history_payload, headers=headers, timeout=30)
        hist_data = resp_hist.json()
        if hist_data.get("code") == 200:
            hist_records = (hist_data.get("data") or {}).get("records", [])
            for hr in hist_records:
                hsm = hr.get("statistics_month")
                if not hsm:
                    continue
                hsm_text = str(hsm)
                if "2024" in hsm_text:
                    history_end_non_liable = _safe_number(hr.get("end_period_non_liable")) or 0
                    history_end_vam_stock = _safe_number(hr.get("end_period_vam_stock")) or 0
                    history_source = f"历史表 {hsm_text}"
                    _add_log("info", "对赌计算②历史表数据",
                             f"{hsm_text}: 期末_无责={history_end_non_liable}, 期末_对赌={history_end_vam_stock}")
                    break
            else:
                _add_log("warn", "对赌计算②历史表数据", "未找到含2024的数据，默认为0")
        else:
            _add_log("warn", "对赌计算②历史表数据", f"查询失败: {hist_data.get('msg', '')}")
    except Exception as e:
        _add_log("error", "对赌计算②历史表数据", f"查询异常: {friendly_error(e)}")

    # ===== 第三步：根据对赌表数据确定期末值 =====
    if matched_gamble:
        _add_log("info", "对赌计算③对赌表匹配", f"找到统计月={stat_ym}的对赌记录")
        basic_stock_rate = _safe_number(matched_gamble.get("basic_stock_rate"))
        should_confirmation_stock_rate = _safe_number(matched_gamble.get("should_confirmation_stock_rate"))

        # 对赌表有数据：期末 = 对赌表值 / 100
        if basic_stock_rate is not None:
            end_period_non_liable = round(basic_stock_rate / 100, 6)
        else:
            end_period_non_liable = 0.0
        if should_confirmation_stock_rate is not None:
            end_period_vam_stock = round(should_confirmation_stock_rate / 100, 6)
        else:
            end_period_vam_stock = 0.0
    else:
        # 对赌表查不到这个项目：期末完全取历史表的期末值
        _add_log("info", "对赌计算③对赌表匹配", f"未找到对赌记录，期末取历史表值")
        basic_stock_rate = None
        should_confirmation_stock_rate = None
        end_period_non_liable = history_end_non_liable
        end_period_vam_stock = history_end_vam_stock

    _add_log("info", "对赌计算③计算期末",
             f"期末_无责股权 = {end_period_non_liable}, "
             f"期末_对赌股权 = {end_period_vam_stock}")

    # ===== 第四步：查月度表 =====
    monthly_table = config.TABLE_MAP["monthly"]
    monthly_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    monthly_payload = {
        "filterRule": {
            "formId": monthly_table["formId"],
            "selectFields": monthly_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": monthly_conditions}],
            "sorts": [],
        },
        "formId": monthly_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    try:
        resp2 = requests.post(api_url, json=monthly_payload, headers=headers, timeout=30)
        monthly_data = resp2.json()
    except Exception as e:
        _add_log("error", "对赌计算④月度表查询失败", friendly_error(e))
        return jsonify({"ok": False, "msg": f"月度表查询请求失败：{friendly_error(e)}"})

    if monthly_data.get("code") != 200:
        return jsonify({"ok": False, "msg": f"月度表查询失败：{monthly_data.get('msg', '未知错误')}"})

    monthly_records = (monthly_data.get("data") or {}).get("records", [])

    # 找到月度表中统计月匹配的记录
    matched_monthly = None
    for mr in monthly_records:
        sm = mr.get("statistics_month")
        if not sm:
            continue
        sm_str = _parse_date_to_str(sm)
        if not sm_str:
            continue
        if sm_str[:7] == stat_ym:
            matched_monthly = mr
            break

    # ===== 第五步：计算时点值 =====
    prev_year = stat_year - 1
    prev_end_non_liable = None
    prev_end_vam_stock = None
    prev_source = None

    if stat_year <= 2025:
        prev_end_non_liable = history_end_non_liable
        prev_end_vam_stock = history_end_vam_stock
        prev_source = history_source
        _add_log("info", "对赌计算⑤时点来源", f"复用历史表数据: 期末_无责={prev_end_non_liable}, 期末_对赌={prev_end_vam_stock}")
    else:
        _add_log("info", "对赌计算⑤时点来源", f"统计月年份={stat_year}，从月度表查找{prev_year}年12月数据")
        prev_dec_ym = f"{prev_year}-12"
        for mr in monthly_records:
            sm = mr.get("statistics_month")
            if not sm:
                continue
            sm_str = _parse_date_to_str(sm)
            if not sm_str:
                continue
            if sm_str[:7] == prev_dec_ym:
                prev_end_non_liable = _safe_number(mr.get("end_period_non_liable")) or 0
                prev_end_vam_stock = _safe_number(mr.get("end_period_vam_stock")) or 0
                prev_source = f"月度表 {prev_dec_ym}"
                _add_log("info", "对赌计算⑤时点来源",
                         f"月度表{prev_dec_ym}: 期末_无责={prev_end_non_liable}, 期末_对赌={prev_end_vam_stock}")
                break
        if prev_source is None:
            prev_end_non_liable = history_end_non_liable
            prev_end_vam_stock = history_end_vam_stock
            prev_source = f"{history_source}(月度表无{prev_dec_ym})"
            _add_log("warn", "对赌计算⑤时点来源", f"月度表未找到{prev_dec_ym}，回退用历史表")

    # 计算时点值
    time_point_non_liable = round(end_period_non_liable - prev_end_non_liable, 6)
    time_point_vam_complete = round(end_period_vam_stock - prev_end_vam_stock, 6)

    _add_log("info", "对赌计算⑥计算时点",
             f"时点_无责={time_point_non_liable}, 时点_对赌完成={time_point_vam_complete}")

    # ===== 与月度表实际值对比校验 =====
    verification = {}
    monthly_info = None
    if matched_monthly:
        actual_end_non_liable = _safe_number(matched_monthly.get("end_period_non_liable"))
        actual_end_vam_stock = _safe_number(matched_monthly.get("end_period_vam_stock"))
        actual_time_non_liable = _safe_number(matched_monthly.get("time_point_non_liable"))
        actual_time_vam_complete = _safe_number(matched_monthly.get("time_point_vam_complete"))

        monthly_info = {
            "statisticsMonth": _parse_date_to_str(matched_monthly.get("statistics_month")),
            "recordId": matched_monthly.get("id"),
            "actual_end_period_non_liable": actual_end_non_liable,
            "actual_end_period_vam_stock": actual_end_vam_stock,
            "actual_time_point_non_liable": actual_time_non_liable,
            "actual_time_point_vam_complete": actual_time_vam_complete,
        }

        # 逐字段校验
        fields_check = [
            ("end_period_non_liable", "期末_无责股权", end_period_non_liable, actual_end_non_liable),
            ("end_period_vam_stock", "期末_对赌股权", end_period_vam_stock, actual_end_vam_stock),
            ("time_point_non_liable", "时点_无责股权", time_point_non_liable, actual_time_non_liable),
            ("time_point_vam_complete", "时点_对赌完成", time_point_vam_complete, actual_time_vam_complete),
        ]
        all_match = True
        for field_key, field_label, calc_val, actual_val in fields_check:
            if calc_val is not None and actual_val is not None:
                diff = abs(calc_val - actual_val)
                match = diff < 0.000001
                verification[field_key] = {
                    "match": match,
                    "calcValue": calc_val,
                    "actualValue": actual_val,
                    "diff": round(diff, 6),
                    "msg": f"✅ {field_label}一致" if match else f"⚠️ {field_label}不一致: 计算={calc_val}, 实际={actual_val}, 差异={diff:.6f}",
                }
                if not match:
                    all_match = False
            elif calc_val is not None and actual_val is None:
                verification[field_key] = {
                    "match": None,
                    "calcValue": calc_val,
                    "actualValue": None,
                    "msg": f"月度表{field_label}为空，无法校验",
                }
                all_match = False
            else:
                verification[field_key] = {
                    "match": None,
                    "calcValue": calc_val,
                    "actualValue": actual_val,
                    "msg": f"计算值为空，无法校验",
                }
                all_match = False

        verification["overall"] = all_match
        _add_log("info", "对赌计算⑦校验结果", f"整体{'一致' if all_match else '存在差异'}")
    else:
        existing_months = []
        for mr in monthly_records:
            sm = mr.get("statistics_month")
            if sm:
                s = _parse_date_to_str(sm)
                if s:
                    existing_months.append(s[:7])
        hint = f"（已有统计月：{', '.join(sorted(set(existing_months)))}）" if existing_months else ""
        monthly_info = {"msg": f"月度表中未找到统计月为 {stat_ym} 的记录{hint}"}
        verification["overall"] = None
        _add_log("info", "对赌计算⑦", f"月度表未找到统计月={stat_ym}的记录{hint}")

    # 构造返回结果
    result = {
        "ok": True,
        "gamble": {
            "statisticsMonth": _parse_date_to_str(matched_gamble.get("statistics_month")) if matched_gamble else stat_ym,
            "basicStockRate": basic_stock_rate,
            "shouldConfirmationStockRate": should_confirmation_stock_rate,
            "projectName": matched_gamble.get("project_name", "") if matched_gamble else "",
            "hasData": matched_gamble is not None,
        },
        "calcResult": {
            "end_period_non_liable": end_period_non_liable,
            "end_period_vam_stock": end_period_vam_stock,
            "time_point_non_liable": time_point_non_liable,
            "time_point_vam_complete": time_point_vam_complete,
        },
        "prevSource": prev_source,
        "prevValues": {
            "end_period_non_liable": prev_end_non_liable,
            "end_period_vam_stock": prev_end_vam_stock,
        },
        "formulas": {
            "end_period_non_liable": f"期末_无责股权 = 对赌表基础股权({basic_stock_rate}%) / 100 = {end_period_non_liable}" if basic_stock_rate is not None else f"期末_无责股权 = {end_period_non_liable}（对赌表无数据，取历史表期末值）",
            "end_period_vam_stock": f"期末_对赌股权 = 对赌表应确认股权比例({should_confirmation_stock_rate}%) / 100 = {end_period_vam_stock}" if should_confirmation_stock_rate is not None else f"期末_对赌股权 = {end_period_vam_stock}（对赌表无数据，取历史表期末值）",
            "time_point_non_liable": f"时点_无责股权 = 当月期末_无责股权({end_period_non_liable}) - {prev_source}期末_无责股权({prev_end_non_liable}) = {time_point_non_liable}",
            "time_point_vam_complete": f"时点_对赌完成 = 当月期末_对赌股权({end_period_vam_stock}) - {prev_source}期末_对赌股权({prev_end_vam_stock}) = {time_point_vam_complete}",
        },
        "monthly": monthly_info,
        "verification": verification,
    }

    return jsonify(result)


@advanced_bp.route("/api/advanced/biz-ratio", methods=["POST"])
def calc_biz_ratio():
    """
    高级功能：工商比例计算
    涉及表单：台账表、股权月度表
    四要素：项目编号、项目公司主体统一社会信用代码、持股主体统一社会信用代码、协议标的公司统一社会信用代码
    逻辑：
    1. 用月度表的项目编号+统计月 定位月度表记录
    2. 用四要素匹配台账表，找工商变更日期<=统计月 且 序号最大的一条
    3. 计算期末工商比例：
       - 直接持股：期末工商比例 = 协议标的公司工商变更后比例(number_e7b076)
       - 间接持股：期末工商比例 = 协议标的公司持有最终标的公司股权(%)(number_500f42) * 协议标的公司工商变更后比例(%)(number_47e399)
    4. 与月度表的期末_工商比例(end_period_registered_equity_ratio)对比
    """
    body = request.get_json(force=True) or {}
    project_no = (body.get("projectNo") or "").strip()
    project_company_uscc = (body.get("projectCompanyUscc") or "").strip()
    holding_subject_uscc = (body.get("holdingSubjectUscc") or "").strip()
    agreement_company_uscc = (body.get("agreementCompanyUscc") or "").strip()
    statistics_month = (body.get("statisticsMonth") or "").strip()  # 格式: "2025-01" 或 "2025-01-xx"

    # 校验输入
    missing = []
    if not project_no:
        missing.append("项目编号")
    if not project_company_uscc:
        missing.append("项目公司主体统一社会信用代码")
    if not holding_subject_uscc:
        missing.append("持股主体统一社会信用代码")
    if not agreement_company_uscc:
        missing.append("协议标的公司统一社会信用代码")
    if not statistics_month:
        missing.append("统计月")
    if missing:
        return jsonify({"ok": False, "msg": f"缺少必填项：{'、'.join(missing)}"})

    # 确保 token
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"})

    headers = {"Content-Type": "application/json", "Tj-Auth": token, "Tojoy-Tenant": tenant}
    api_url = config.get_api_url(_current_env["value"])

    # 提取统计月的年月（如 "2025-01"）
    stat_ym = statistics_month[:7]

    _add_log("info", "工商比例①输入", f"项目编号={project_no}, 统计月={stat_ym}")

    # ===== 第一步：查台账表，用四要素精确匹配（获取所有记录） =====
    ledger_table = config.TABLE_MAP["ledger"]
    ledger_conditions = [
        {"name": "项目编号", "field": "input_36c323", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "input_36c323", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司主体统一社会信用代码", "field": "project_company_main_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_main_uscc", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "持股主体统一社会信用代码", "field": "input_2c2b00_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "input_2c2b00_uscc", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_subject_company_uscc", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_subject_company_uscc", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    ledger_payload = {
        "filterRule": {
            "formId": ledger_table["formId"],
            "selectFields": ledger_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": ledger_conditions}],
            "sorts": [],
        },
        "formId": ledger_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 200,
        "pageNo": 1,
    }

    try:
        resp = requests.post(api_url, json=ledger_payload, headers=headers, timeout=30)
        ledger_data = resp.json()
    except Exception as e:
        _add_log("error", "工商比例②台账查询失败", friendly_error(e))
        return jsonify({"ok": False, "msg": f"台账查询请求失败：{friendly_error(e)}"})

    if ledger_data.get("code") != 200:
        msg = ledger_data.get("msg") or "台账查询失败"
        return jsonify({"ok": False, "msg": f"台账查询失败：{msg}"})

    ledger_records = (ledger_data.get("data") or {}).get("records", [])
    if not ledger_records:
        _add_log("warn", "工商比例②台账匹配", "四要素未匹配到记录")
        return jsonify({"ok": False, "msg": "台账表中未找到满足四要素条件的记录"})

    _add_log("info", "工商比例②台账匹配", f"四要素匹配到{len(ledger_records)}条")

    # ===== 第二步：筛选工商变更日期 <= 统计月 的记录，取序号最大的一条 =====
    # 统计月是年月格式（如 "2025-01"），台账工商变更日期是年月日
    # 规则：2025-01-01 ~ 2025-01-31 都算 <= 2025-01
    # 即：工商变更日期的年月 <= 统计月年月
    candidates = []
    for record in ledger_records:
        date_val = record.get("date_0f5998")
        if not date_val:
            continue
        record_date_str = _parse_date_to_str(date_val)
        if not record_date_str:
            continue
        # 比较年月：记录的年月 <= 统计月年月
        record_ym = record_date_str[:7]
        if record_ym <= stat_ym:
            seq_num = _safe_number(record.get("number_8e6771"))
            candidates.append({
                "record": record,
                "date_str": record_date_str,
                "seq_num": seq_num if seq_num is not None else -1,
            })

    if not candidates:
        # 列出已有的工商变更日期供参考
        existing_dates = []
        for r in ledger_records:
            d = r.get("date_0f5998")
            if d:
                ds = _parse_date_to_str(d)
                if ds:
                    existing_dates.append(ds)
        hint = f"台账中已有工商变更日期：{', '.join(sorted(existing_dates))}" if existing_dates else "台账中无工商变更日期记录"
        _add_log("warn", "工商比例③筛选", f"无工商变更日期<={stat_ym}的记录。{hint}")
        return jsonify({"ok": False, "msg": f"台账表中未找到工商变更日期≤{stat_ym}的记录。{hint}"})

    # 取序号最大的一条
    candidates.sort(key=lambda x: x["seq_num"], reverse=True)
    matched = candidates[0]
    matched_ledger = matched["record"]
    matched_date_str = matched["date_str"]
    matched_seq = matched["seq_num"]

    _add_log("info", "工商比例③筛选",
             f"工商变更日期<={stat_ym}的记录有{len(candidates)}条，取序号最大={matched_seq}, 工商变更日期={matched_date_str}")

    # ===== 第三步：根据持股类型计算期末工商比例 =====
    holding_type_raw = matched_ledger.get("select_0aeab3")
    holding_type = ""
    if isinstance(holding_type_raw, dict):
        holding_type = holding_type_raw.get("label", "")
    elif isinstance(holding_type_raw, str):
        holding_type = holding_type_raw

    # 获取计算所需的字段值
    # number_e7b076: 履约完成股权比例（%）—— 用户指定直接持股用此字段作为协议标的公司工商变更后比例
    biz_ratio_direct = _safe_number(matched_ledger.get("number_e7b076"))
    # number_500f42: 协议标的公司持有最终标的公司股权（%）
    agreement_hold_ultimate = _safe_number(matched_ledger.get("number_500f42"))
    # number_47e399: 协议标的公司工商变更后比例（%）
    biz_change_after_ratio = _safe_number(matched_ledger.get("number_47e399"))

    calc_result = None
    calc_formula = ""

    if holding_type == "直接" or holding_type == "直接持股":
        if biz_ratio_direct is None:
            _add_log("error", "工商比例④计算", f"直接持股，但number_e7b076字段为空")
            return jsonify({"ok": False, "msg": "直接持股计算所需字段为空：协议标的公司工商变更后比例(number_e7b076)为空"})
        calc_result = biz_ratio_direct / 100
        calc_formula = f"直接持股：期末工商比例 = 协议标的公司工商变更后比例({biz_ratio_direct}%) / 100 = {calc_result}"
    elif holding_type == "间接" or holding_type == "间接持股":
        if agreement_hold_ultimate is None or biz_change_after_ratio is None:
            _add_log("error", "工商比例④计算",
                     f"间接持股字段为空: 持有最终标的={agreement_hold_ultimate}, 工商变更后比例={biz_change_after_ratio}")
            return jsonify({
                "ok": False,
                "msg": f"间接持股计算所需字段为空：协议标的公司持有最终标的公司股权(%)={agreement_hold_ultimate}，协议标的公司工商变更后比例(%)={biz_change_after_ratio}"
            })
        calc_result = (agreement_hold_ultimate / 100) * (biz_change_after_ratio / 100)
        calc_formula = (
            f"间接持股：期末工商比例 = 协议标的公司持有最终标的公司股权({agreement_hold_ultimate}%) / 100 × "
            f"协议标的公司工商变更后比例({biz_change_after_ratio}%) / 100 = {calc_result}"
        )
    else:
        _add_log("warn", "工商比例④计算", f"持股类型={holding_type or '空'}，无法计算")
        return jsonify({"ok": False, "msg": f"台账中持股类型为「{holding_type or '空'}」，无法计算（需为「直接」或「间接」）"})

    calc_result_rounded = round(calc_result, 6)
    _add_log("info", "工商比例④计算", f"持股类型={holding_type}, {calc_formula}")

    # ===== 第四步：查月度表，校验期末_工商比例 =====
    monthly_table = config.TABLE_MAP["monthly"]
    monthly_conditions = [
        {"name": "项目编号", "field": "project_no", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_no", "value": project_no, "isArray": "0", "values": [project_no]},
        {"name": "项目公司统一社会信用代码", "field": "project_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "project_company_credit_code", "value": project_company_uscc, "isArray": "0", "values": [project_company_uscc]},
        {"name": "天九持股主体统一社会信用代码", "field": "tojoy_stock_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "tojoy_stock_credit_code", "value": holding_subject_uscc, "isArray": "0", "values": [holding_subject_uscc]},
        {"name": "协议标的公司统一社会信用代码", "field": "agreement_company_credit_code", "controlType": "TEXT", "preControlType": "TEXT",
         "conditionType": "EQ", "preLongField": "agreement_company_credit_code", "value": agreement_company_uscc, "isArray": "0", "values": [agreement_company_uscc]},
    ]
    monthly_payload = {
        "filterRule": {
            "formId": monthly_table["formId"],
            "selectFields": monthly_table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": monthly_conditions}],
            "sorts": [],
        },
        "formId": monthly_table["formId"],
        "appId": config.APP_ID,
        "pageSize": 100,
        "pageNo": 1,
    }

    _add_log("info", "工商比例⑤月度表查询", f"四要素匹配月度表, 目标统计月={stat_ym}")
    try:
        resp2 = requests.post(api_url, json=monthly_payload, headers=headers, timeout=30)
        monthly_data = resp2.json()
    except Exception as e:
        _add_log("error", "工商比例⑤月度表查询失败", friendly_error(e))
        return jsonify({"ok": False, "msg": f"月度表查询失败：{friendly_error(e)}"})

    if monthly_data.get("code") != 200:
        return jsonify({"ok": False, "msg": f"月度表查询失败：{monthly_data.get('msg', '未知错误')}"})

    monthly_records = (monthly_data.get("data") or {}).get("records", [])

    # 找到月度表中统计月匹配的记录
    matched_monthly = None
    monthly_biz_ratio = None
    for mr in monthly_records:
        sm = mr.get("statistics_month")
        if not sm:
            continue
        sm_str = _parse_date_to_str(sm)
        if not sm_str:
            continue
        if sm_str[:7] == stat_ym:
            matched_monthly = mr
            monthly_biz_ratio = _safe_number(mr.get("end_period_registered_equity_ratio"))
            break

    # ===== 第五步：构造返回结果 =====
    result = {
        "ok": True,
        "ledger": {
            "projectNo": project_no,
            "seq": matched_seq,
            "holdingType": holding_type,
            "bizChangeDate": matched_date_str,
            "bizRatioDirect": biz_ratio_direct,
            "agreementHoldUltimate": agreement_hold_ultimate,
            "bizChangeAfterRatio": biz_change_after_ratio,
        },
        "calcResult": {
            "value": calc_result_rounded,
            "formula": calc_formula,
        },
        "monthly": None,
        "verification": None,
    }

    if matched_monthly:
        result["monthly"] = {
            "statisticsMonth": _parse_date_to_str(matched_monthly.get("statistics_month")),
            "currentValue": monthly_biz_ratio,
            "recordId": matched_monthly.get("id"),
        }
        if monthly_biz_ratio is not None and calc_result_rounded is not None:
            diff = abs(calc_result_rounded - monthly_biz_ratio)
            if diff < 0.000001:
                result["verification"] = {"match": True, "msg": f"✅ 计算结果与月度表期末_工商比例一致"}
                _add_log("info", "工商比例⑥校验", f"✅ 一致: 计算={calc_result_rounded}, 月度表={monthly_biz_ratio}")
            else:
                result["verification"] = {
                    "match": False,
                    "msg": f"⚠️ 计算结果({calc_result_rounded:.6f}) 与月度表期末_工商比例({monthly_biz_ratio:.6f})不一致，差异={diff:.6f}"
                }
                _add_log("warn", "工商比例⑥校验",
                         f"⚠️ 不一致: 计算={calc_result_rounded:.6f}, 月度表={monthly_biz_ratio:.6f}, 差异={diff:.6f}")
        else:
            result["verification"] = {"match": None, "msg": "月度表期末_工商比例值为空，无法校验"}
            _add_log("info", "工商比例⑥校验", "月度表期末_工商比例值为空，无法校验")
    else:
        existing_months = []
        for mr in monthly_records:
            sm = mr.get("statistics_month")
            if sm:
                s = _parse_date_to_str(sm)
                if s:
                    existing_months.append(s[:7])
        hint = f"（已有统计月：{', '.join(sorted(set(existing_months)))}）" if existing_months else ""
        result["monthly"] = {"msg": f"月度表中未找到统计月为 {stat_ym} 的记录{hint}"}
        result["verification"] = {"match": None, "msg": "未匹配到月度表记录，仅返回计算结果"}
        _add_log("info", "工商比例⑥校验", f"月度表未找到统计月={stat_ym}的记录{hint}")

    return jsonify(result)
