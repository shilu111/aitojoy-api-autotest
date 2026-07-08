"""
共享状态模块
存放跨模块共享的变量和函数，避免循环导入。
"""
import json
import time
from collections import deque
from datetime import datetime

import requests

import config

# 当前环境（默认测试）
_current_env = {"value": config.DEFAULT_ENV}

# 缓存 token 及过期时间（按环境区分）
_cached_tokens = {
    "production": {"value": None, "expires_at": 0},
    "test": {"value": None, "expires_at": 0},
}

# ===== 日志队列（最多保留200条）=====
_logs = deque(maxlen=200)


def _add_log(level, action, detail):
    """添加一条日志记录"""
    _logs.append({
        "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,  # info / error / warn
        "action": action,
        "detail": detail,
    })


def _get_cached_token():
    """获取当前环境的 token 缓存"""
    return _cached_tokens[_current_env["value"]]


def get_token(force_refresh=False):
    """调用登录接口获取最新 token，带过期时间管理"""
    now = time.time()
    cached = _get_cached_token()
    # 未过期且非强制刷新，直接返回缓存
    if cached["value"] and not force_refresh and now < cached["expires_at"]:
        return cached["value"]
    try:
        login_url = config.get_login_url(_current_env["value"])
        _add_log("info", "登录", f"POST {login_url} (环境: {_current_env['value']})")
        resp = requests.post(login_url, params=config.LOGIN_PARAMS, timeout=15)
        data = resp.json()
        _add_log("info", "登录响应", f"status={resp.status_code}, code={data.get('code')}")
        # 接口返回格式: {"code": 200, "data": {"accessToken": "..."}}
        token = None
        if isinstance(data.get("data"), dict):
            token = data["data"].get("accessToken")
        if not token:
            token = data.get("access_token")
        if token:
            # 默认 token 有效期 7 天，提前 10 分钟刷新
            cached["value"] = token
            cached["expires_at"] = now + 7 * 24 * 3600 - 600
            _add_log("info", "登录成功", f"token={token[:20]}...")
            return token
        else:
            _add_log("error", "登录失败", f"未获取到token, 响应: {json.dumps(data, ensure_ascii=False)[:200]}")
            return None
    except Exception as e:
        _add_log("error", "登录异常", str(e))
        return None


def ensure_valid_token():
    """确保拿到有效 token：先检查缓存是否过期，过期则强制刷新"""
    now = time.time()
    cached = _get_cached_token()
    env = _current_env["value"]
    if cached["value"] and now < cached["expires_at"]:
        _add_log("info", "Token检查", f"使用缓存token (环境: {env}, token={cached['value'][:20]}...)")
        return cached["value"]
    # 缓存无效，强制重新登录
    _add_log("warn", "Token检查", f"缓存无效，重新登录 (环境: {env})")
    return get_token(force_refresh=True)


def friendly_error(e):
    """将网络异常转为简洁的中文错误提示"""
    msg = str(e)
    # DNS 解析失败
    if "nodename nor servname" in msg or "Name or service not known" in msg or "getaddrinfo failed" in msg:
        # 提取主机名
        host = ""
        if "host='" in msg:
            host = msg.split("host='")[1].split("'")[0]
        return f"DNS解析失败：无法访问 {host or '目标服务器'}，请检查网络或VPN连接"
    # 连接超时
    if "timed out" in msg or "TimeoutError" in msg:
        return "请求超时：服务器无响应，请检查网络连接"
    # 连接被拒绝
    if "Connection refused" in msg:
        return "连接被拒绝：目标服务器未启动或端口不通"
    # 连接重置
    if "Connection reset" in msg or "ConnectionReset" in msg:
        return "连接被重置：网络不稳定或服务器异常"
    # SSL 错误
    if "SSL" in msg or "certificate" in msg.lower():
        return "SSL证书错误：请检查网络环境（是否有代理拦截）"
    # 通用网络错误（截短显示）
    if "Max retries exceeded" in msg:
        # 提取核心原因
        if "Caused by" in msg:
            cause = msg.split("Caused by")[-1].strip().rstrip(")")
            # 再精简一次
            if "NewConnectionError" in cause:
                return f"网络连接失败：无法连接目标服务器，请检查网络或VPN"
            return f"网络连接失败：{cause[:80]}"
        return "网络连接失败：多次重试后仍无法连接，请检查网络"
    # 其他异常，截短到100字符
    if len(msg) > 100:
        return msg[:100] + "…"
    return msg
