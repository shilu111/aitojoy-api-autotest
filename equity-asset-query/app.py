"""
股权资产管理查询工具 - Flask 后端（四表联查）
职责：
  1. 提供查询页面（深色操作面板，四张表 Tab 切换）
  2. 代理调用 zidayun 表单引擎接口（规避跨域、统一鉴权）
  3. 自动登录获取最新 Token，查询前校验有效性
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, render_template, request, jsonify

import config
from shared import (
    _current_env, _cached_tokens, _logs, _add_log,
    _get_cached_token, get_token, ensure_valid_token, friendly_error,
)

app = Flask(__name__)


def build_payload(table: dict, filters: dict, page_no: int, page_size: int, sorts: list = None) -> dict:
    """按某张表的字段映射，将页面查询条件构造为接口入参"""
    # 项目名称、天九持股主体用 LIKE 模糊匹配；项目编号用 EQ 精确匹配
    LIKE_FIELDS = {"projectName", "tjHoldingSubject"}
    conditions = []
    for key, field in table["queryFields"].items():
        value = (filters.get(key) or "").strip()
        if not value:
            continue
        condition_type = "LIKE" if key in LIKE_FIELDS else "EQ"
        conditions.append({
            "name": config.QUERY_LABELS.get(key, key),
            "field": field,
            "controlType": "TEXT",
            "preControlType": "TEXT",
            "conditionType": condition_type,
            "preLongField": field,
            "value": value,
            "isArray": "0",
            "values": [value],
        })
    fid = table["formId"]

    # 构造排序参数（注：接口可能不支持，前端也做排序兜底）
    sort_list = []
    if sorts:
        for s in sorts:
            sort_list.append({
                "field": s["field"],
                "order": s.get("order", "DESC"),
            })

    return {
        "filterRule": {
            "formId": fid,
            "selectFields": table["selectFields"],
            "conditionGroups": [{"conditionRel": "AND", "conditions": conditions}],
            "sorts": sort_list,
        },
        "formId": fid,
        "appId": config.APP_ID,
        "pageSize": page_size,
        "pageNo": page_no,
    }


def query_table(table: dict, token: str, tenant: str, filters: dict,
                page_no: int, page_size: int, sorts: list = None) -> dict:
    """查询单张表，返回标准化结果"""
    payload = build_payload(table, filters, page_no, page_size, sorts=sorts)
    headers = {"Content-Type": "application/json", "Tj-Auth": token, "Tojoy-Tenant": tenant}
    api_url = config.get_api_url(_current_env["value"])
    # 日志只显示该表实际使用的查询条件
    used_filters = {k: v for k, v in filters.items() if k in table["queryFields"] and (v or "").strip()}
    _add_log("info", f"查询[{table['name']}]",
             json.dumps({"url": api_url, "formId": table["formId"], "page": page_no, "size": page_size, "filters": used_filters}, ensure_ascii=False))
    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
        data = resp.json()
    except requests.RequestException as e:
        _add_log("error", f"查询[{table['name']}]请求失败", friendly_error(e))
        return {"ok": False, "msg": f"请求失败：{friendly_error(e)}", "total": 0, "records": [], "auth_fail": False}
    except ValueError:
        _add_log("error", f"查询[{table['name']}]", f"接口返回非JSON, status={resp.status_code}, body={resp.text[:200]}")
        return {"ok": False, "msg": "接口返回非 JSON", "total": 0, "records": [], "auth_fail": False}

    if data.get("code") != 200:
        msg = data.get("msg") or "查询失败"
        auth_fail = resp.status_code in (401, 403) or any(
            kw in msg for kw in ("token", "Token", "认证", "授权", "登录", "过期", "失效", "unauthorized")
        )
        _add_log("error", f"查询[{table['name']}]失败",
                 f"HTTP {resp.status_code}, code={data.get('code')}, msg={msg}")
        return {"ok": False, "msg": msg, "total": 0, "records": [], "auth_fail": auth_fail}

    page = data.get("data") or {}
    total = page.get("total", 0)
    records = page.get("records", [])
    _add_log("info", f"查询[{table['name']}]成功", f"total={total}, 本页返回{len(records)}条")
    return {
        "ok": True,
        "total": total,
        "pageNo": page.get("current", page_no),
        "pageSize": page.get("size", page_size),
        "records": records,
        "auth_fail": False,
    }


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查接口，用于监控服务是否正常运行"""
    return jsonify({"ok": True, "status": "running", "service": "equity-asset-query"})


@app.route("/api/weather", methods=["GET"])
def get_weather():
    """获取当前天气（使用 wttr.in 免费接口，北京朝阳区）"""
    try:
        resp = requests.get("https://wttr.in/Chaoyang,Beijing?format=j1&lang=zh", timeout=10)
        data = resp.json()
        current = data.get("current_condition", [{}])[0]
        temp = current.get("temp_C", "?")
        # 优先取中文描述
        lang_zh = current.get("lang_zh", [])
        if lang_zh and lang_zh[0].get("value"):
            desc = lang_zh[0]["value"].strip()
        else:
            weather_desc = current.get("weatherDesc", [{}])
            desc = weather_desc[0].get("value", "晴").strip() if weather_desc else "晴"
        code = current.get("weatherCode", "113")
        return jsonify({"ok": True, "temp": temp, "desc": desc, "code": code, "city": "北京朝阳"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@app.route("/")
def index():
    return render_template(
        "index.html",
        tables=config.TABLES,
    )


@app.route("/api/env", methods=["GET"])
def get_env():
    """获取当前环境"""
    env = _current_env["value"]
    label = config.ENVIRONMENTS[env]["label"]
    return jsonify({"ok": True, "env": env, "label": label})


@app.route("/api/env", methods=["POST"])
def switch_env():
    """切换环境（测试/生产）"""
    body = request.get_json(force=True) or {}
    env = body.get("env", "").strip()
    if env not in config.ENVIRONMENTS:
        return jsonify({"ok": False, "msg": f"无效环境：{env}"}), 400
    _current_env["value"] = env
    label = config.ENVIRONMENTS[env]["label"]
    return jsonify({"ok": True, "env": env, "label": label, "msg": f"已切换至{label}"})


@app.route("/api/login", methods=["POST"])
def login():
    """手动登录接口，支持用户使用自己的账号"""
    body = request.get_json(force=True) or {}
    mobile = (body.get("mobile") or "").strip()
    password = (body.get("password") or "").strip()
    if not mobile or not password:
        return jsonify({"ok": False, "msg": "请输入手机号和密码"}), 400

    params = dict(config.LOGIN_PARAMS)
    params["mobile"] = mobile
    params["password"] = password

    try:
        login_url = config.get_login_url(_current_env["value"])
        resp = requests.post(login_url, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        return jsonify({"ok": False, "msg": f"登录请求失败：{e}"})

    token = None
    if isinstance(data.get("data"), dict):
        token = data["data"].get("accessToken")
    if not token:
        token = data.get("access_token")

    if token:
        cached = _get_cached_token()
        cached["value"] = token
        cached["expires_at"] = time.time() + 7 * 24 * 3600 - 600
        return jsonify({"ok": True, "msg": "登录成功"})
    else:
        msg = data.get("msg") or "登录失败，请检查账号密码"
        return jsonify({"ok": False, "msg": msg})


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """检查当前环境 token 是否有效（不触发自动登录）"""
    cached = _get_cached_token()
    now = time.time()
    if cached["value"] and now < cached["expires_at"]:
        return jsonify({"ok": True, "loggedIn": True, "env": _current_env["value"]})
    return jsonify({"ok": True, "loggedIn": False, "env": _current_env["value"]})


@app.route("/api/auth/auto-login", methods=["POST"])
def auto_login():
    """自动登录：使用默认账号获取 token，返回结果"""
    token = get_token(force_refresh=False)
    if token:
        return jsonify({"ok": True, "msg": "自动登录成功"})
    # 尝试强制刷新
    token = get_token(force_refresh=True)
    if token:
        return jsonify({"ok": True, "msg": "自动登录成功"})
    return jsonify({"ok": False, "msg": "自动登录失败，请手动登录"})


@app.route("/api/query-all", methods=["POST"])
def query_all():
    """一次查询四张表（并行），用于点击查询时刷新所有 Tab"""
    body = request.get_json(force=True) or {}
    # 查询前确保 token 有效
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"}), 500
    filters = body.get("filters") or {}
    page_size = int(body.get("pageSize") or 20)
    sorts_map = body.get("sorts") or {}  # {tableKey: [{field, order}]}

    def run(t, tk):
        table_sorts = sorts_map.get(t["key"]) or []
        return t["key"], query_table(t, tk, tenant, filters, 1, page_size, sorts=table_sorts)

    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(run, t, token) for t in config.TABLES]
        for f in futures:
            key, res = f.result()
            results[key] = res

    # 如果有任何表认证失败，强制刷新 token 并重试全部
    any_auth_fail = any(results[k].get("auth_fail") for k in results)
    if any_auth_fail:
        token = get_token(force_refresh=True)
        if token:
            results = {}
            with ThreadPoolExecutor(max_workers=4) as ex:
                futures = [ex.submit(run, t, token) for t in config.TABLES]
                for f in futures:
                    key, res = f.result()
                    results[key] = res

    # 返回时去掉内部字段 auth_fail
    clean = {}
    for k, v in results.items():
        clean[k] = {kk: vv for kk, vv in v.items() if kk != "auth_fail"}
    return jsonify({"ok": True, "tables": clean})


@app.route("/api/query", methods=["POST"])
def query_single():
    """查询单张表（用于 Tab 内翻页/改每页条数）"""
    body = request.get_json(force=True) or {}
    # 查询前确保 token 有效
    token = ensure_valid_token()
    tenant = config.get_tenant(_current_env["value"])
    table_key = body.get("table")
    table = config.TABLE_MAP.get(table_key)
    if not table:
        return jsonify({"ok": False, "msg": f"未知表：{table_key}"}), 400
    if not token:
        return jsonify({"ok": False, "msg": "自动登录失败，无法获取 Token"}), 500

    filters = body.get("filters") or {}
    page_no = int(body.get("pageNo") or 1)
    page_size = int(body.get("pageSize") or 20)
    sorts = body.get("sorts") or []

    res = query_table(table, token, tenant, filters, page_no, page_size, sorts=sorts)

    # 认证失败，强制刷新 token 重试
    if res.get("auth_fail"):
        token = get_token(force_refresh=True)
        if token:
            res = query_table(table, token, tenant, filters, page_no, page_size, sorts=sorts)

    # 返回时去掉内部字段
    return jsonify({k: v for k, v in res.items() if k != "auth_fail"})


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """获取后端日志"""
    return jsonify({"ok": True, "logs": list(_logs)})


@app.route("/api/logs", methods=["DELETE"])
def clear_logs():
    """清空日志"""
    _logs.clear()
    return jsonify({"ok": True})


# ===== 注册 Blueprint =====
from routes.import_export import import_export_bp
from routes.advanced import advanced_bp

app.register_blueprint(import_export_bp)
app.register_blueprint(advanced_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
