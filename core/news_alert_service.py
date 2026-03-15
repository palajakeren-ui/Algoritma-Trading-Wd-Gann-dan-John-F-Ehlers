"""
═══════════════════════════════════════════════════════════════════
 GANN QUANT AI — Real-Time News & Market Alert Service
 Multi-channel notification dispatch:
   Email (SMTP), SMS (Twilio), Telegram, Discord, Slack, Webhook
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import time
import yaml
import smtplib
import threading
import hashlib
from collections import deque
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

# Optional imports — each channel degrades gracefully
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    logger.warning("requests not installed — HTTP-based alerts (Discord/Telegram/Slack/Webhook) disabled")

try:
    from twilio.rest import Client as TwilioClient
    _HAS_TWILIO = True
except ImportError:
    _HAS_TWILIO = False

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION LOADER
# ═══════════════════════════════════════════════════════════════════

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "alerts_config.yaml")
_config: Dict[str, Any] = {}
_config_mtime: float = 0.0


def _load_config(force: bool = False) -> Dict[str, Any]:
    """Load alert config from YAML, with file-change caching."""
    global _config, _config_mtime
    path = os.path.abspath(_CONFIG_PATH)
    try:
        mt = os.path.getmtime(path)
        if not force and mt == _config_mtime and _config:
            return _config
        with open(path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
        _config_mtime = mt
        logger.info(f"Alert config loaded from {path}")
    except Exception as e:
        logger.error(f"Failed to load alert config: {e}")
        if not _config:
            _config = {"global": {"enabled": False}}
    return _config


def get_config() -> Dict[str, Any]:
    return _load_config()


def save_config(cfg: Dict[str, Any]) -> bool:
    """Save updated config back to YAML."""
    global _config, _config_mtime
    path = os.path.abspath(_CONFIG_PATH)
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        _config = cfg
        _config_mtime = os.path.getmtime(path)
        logger.info("Alert config saved")
        return True
    except Exception as e:
        logger.error(f"Failed to save alert config: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# ALERT MODEL
# ═══════════════════════════════════════════════════════════════════

_SEVERITY_PRIORITY = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4, "INFO": 5}
_SEVERITY_EMOJI = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📊", "LOW": "ℹ️", "INFO": "📌"}
_SEVERITY_COLOR = {
    "CRITICAL": "#FF0040", "HIGH": "#FF6600",
    "MEDIUM": "#FFB800", "LOW": "#00D4FF", "INFO": "#8B95A5",
}


def _make_alert(
    alert_type: str,
    title: str,
    message: str,
    severity: str = "MEDIUM",
    symbol: str = "",
    category: str = "general",
    data: Optional[Dict] = None,
    channels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a standardized alert object."""
    now = datetime.now()
    alert_id = hashlib.md5(
        f"{alert_type}:{symbol}:{title}:{now.strftime('%Y%m%d%H%M')}".encode()
    ).hexdigest()[:12]
    return {
        "id": alert_id,
        "type": alert_type,
        "category": category,
        "severity": severity,
        "priority": _SEVERITY_PRIORITY.get(severity, 3),
        "symbol": symbol,
        "title": title,
        "message": message,
        "data": data or {},
        "channels": channels,          # None = use rule defaults
        "timestamp": now.isoformat(),
        "unix_ts": time.time(),
        "dispatched": False,
        "dispatch_results": {},
        "emoji": _SEVERITY_EMOJI.get(severity, "📌"),
        "color": _SEVERITY_COLOR.get(severity, "#8B95A5"),
    }


# ═══════════════════════════════════════════════════════════════════
# RATE LIMITER & DEDUP
# ═══════════════════════════════════════════════════════════════════

class _RateLimiter:
    """Per-channel sliding-window rate limiter."""

    def __init__(self):
        self._windows: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def check(self, channel: str, max_per_minute: int = 30,
              max_per_hour: int = 300) -> bool:
        now = time.time()
        with self._lock:
            if channel not in self._windows:
                self._windows[channel] = deque()
            q = self._windows[channel]
            # Evict entries older than 1 hour
            while q and q[0] < now - 3600:
                q.popleft()
            count_hour = len(q)
            count_minute = sum(1 for t in q if t > now - 60)
            if count_minute >= max_per_minute or count_hour >= max_per_hour:
                return False
            q.append(now)
            return True

    def reset(self, channel: Optional[str] = None):
        with self._lock:
            if channel:
                self._windows.pop(channel, None)
            else:
                self._windows.clear()


_rate_limiter = _RateLimiter()
_dedup_cache: Dict[str, float] = {}
_dedup_lock = threading.Lock()


def _is_duplicate(alert: Dict) -> bool:
    """Check if alert is duplicate within dedup window."""
    cfg = _load_config()
    window = cfg.get("global", {}).get("dedup_window_minutes", 5) * 60
    key = f"{alert['type']}:{alert['symbol']}:{alert['title']}"
    now = time.time()
    with _dedup_lock:
        # Clean old entries
        expired = [k for k, v in _dedup_cache.items() if now - v > window]
        for k in expired:
            del _dedup_cache[k]
        if key in _dedup_cache:
            return True
        _dedup_cache[key] = now
        return False


# ═══════════════════════════════════════════════════════════════════
# CHANNEL DISPATCHERS
# ═══════════════════════════════════════════════════════════════════

def _send_email(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via SMTP email."""
    try:
        host = ch_cfg.get("smtp_host", "smtp.gmail.com")
        port = ch_cfg.get("smtp_port", 587)
        user = ch_cfg.get("username", "")
        pwd = ch_cfg.get("password", "")
        from_addr = ch_cfg.get("from_address", user)
        recipients = ch_cfg.get("recipients", [])
        prefix = ch_cfg.get("subject_prefix", "[GANN ALERT]")

        if not user or not pwd or not recipients:
            return False, "Email credentials or recipients not configured"

        recipients = [r for r in recipients if r]
        if not recipients:
            return False, "No valid email recipients"

        subject = f"{prefix} {alert['emoji']} {alert['severity']}: {alert['title']}"

        # Build HTML email
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e17;color:#fff;border-radius:8px;overflow:hidden;border:1px solid #1a2a3a">
            <div style="background:{alert['color']};padding:12px 20px;text-align:center">
                <h2 style="margin:0;font-size:16px;color:#fff">{alert['emoji']} {alert['title']}</h2>
            </div>
            <div style="padding:20px">
                <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
                    <tr><td style="color:#8B95A5;padding:4px 8px;width:100px">Severity</td>
                        <td style="color:{alert['color']};font-weight:bold;padding:4px 8px">{alert['severity']}</td></tr>
                    <tr><td style="color:#8B95A5;padding:4px 8px">Symbol</td>
                        <td style="color:#FFB800;font-weight:bold;padding:4px 8px">{alert.get('symbol','—')}</td></tr>
                    <tr><td style="color:#8B95A5;padding:4px 8px">Category</td>
                        <td style="color:#00D4FF;padding:4px 8px">{alert.get('category','general')}</td></tr>
                    <tr><td style="color:#8B95A5;padding:4px 8px">Time</td>
                        <td style="color:#fff;padding:4px 8px">{alert['timestamp']}</td></tr>
                </table>
                <div style="background:#111827;border:1px solid #1a2a3a;padding:12px;border-radius:4px;margin-bottom:16px">
                    <p style="margin:0;color:#e5e7eb;font-size:14px;line-height:1.6">{alert['message']}</p>
                </div>
                {"<div style='background:#111827;border:1px solid #1a2a3a;padding:12px;border-radius:4px'><pre style='margin:0;color:#8B95A5;font-size:11px'>" + json.dumps(alert.get('data',{}), indent=2) + "</pre></div>" if alert.get('data') else ""}
            </div>
            <div style="background:#060a10;padding:10px 20px;text-align:center;border-top:1px solid #1a2a3a">
                <span style="color:#8B95A5;font-size:11px">Gann Quant AI • Automated Trading Alert System</span>
            </div>
        </div>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)

        text_part = MIMEText(
            f"{alert['emoji']} {alert['severity']}: {alert['title']}\n\n"
            f"Symbol: {alert.get('symbol','—')}\n"
            f"Message: {alert['message']}\n"
            f"Time: {alert['timestamp']}\n",
            "plain"
        )
        html_part = MIMEText(html, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(host, port) as server:
            if ch_cfg.get("smtp_tls", True):
                server.starttls()
            server.login(user, pwd)
            server.sendmail(from_addr, recipients, msg.as_string())

        logger.info(f"📧 Email sent: {alert['title']} → {len(recipients)} recipients")
        return True, f"Sent to {len(recipients)} recipients"

    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False, str(e)


def _send_sms(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via Twilio SMS."""
    if not _HAS_TWILIO:
        return False, "Twilio library not installed (pip install twilio)"
    try:
        sid = ch_cfg.get("account_sid", "")
        token = ch_cfg.get("auth_token", "")
        from_num = ch_cfg.get("from_number", "")
        recipients = [r for r in ch_cfg.get("recipients", []) if r]

        if not sid or not token or not from_num or not recipients:
            return False, "Twilio credentials not configured"

        client = TwilioClient(sid, token)
        body = (
            f"{alert['emoji']} {alert['severity']}: {alert['title']}\n"
            f"Symbol: {alert.get('symbol','—')}\n"
            f"{alert['message'][:300]}"
        )

        sent = 0
        for num in recipients:
            try:
                client.messages.create(body=body, from_=from_num, to=num)
                sent += 1
            except Exception as e2:
                logger.warning(f"SMS to {num} failed: {e2}")

        logger.info(f"📱 SMS sent: {alert['title']} → {sent}/{len(recipients)}")
        return sent > 0, f"Sent to {sent}/{len(recipients)} numbers"

    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return False, str(e)


def _send_telegram(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via Telegram Bot API."""
    if not _HAS_REQUESTS:
        return False, "requests library not installed"
    try:
        token = ch_cfg.get("bot_token", "")
        chat_ids = [c for c in ch_cfg.get("chat_ids", []) if c]
        parse_mode = ch_cfg.get("parse_mode", "HTML")

        if not token or not chat_ids:
            return False, "Telegram bot_token or chat_ids not configured"

        # Build Telegram message
        if parse_mode == "HTML":
            text = (
                f"{alert['emoji']} <b>{alert['severity']}: {alert['title']}</b>\n\n"
                f"{'<b>📌 ' + alert['symbol'] + '</b>  •  ' if alert.get('symbol') else ''}"
                f"<i>{alert.get('category','general')}</i>\n\n"
                f"{alert['message']}\n\n"
                f"🕐 {alert['timestamp']}\n"
                f"<code>Gann Quant AI Alert System</code>"
            )
        else:
            text = (
                f"{alert['emoji']} *{alert['severity']}: {alert['title']}*\n\n"
                f"{'📌 *' + alert['symbol'] + '*  •  ' if alert.get('symbol') else ''}"
                f"_{alert.get('category','general')}_\n\n"
                f"{alert['message']}\n\n"
                f"🕐 {alert['timestamp']}\n"
                f"`Gann Quant AI Alert System`"
            )

        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        sent = 0
        for cid in chat_ids:
            try:
                resp = _requests.post(api_url, json={
                    "chat_id": cid,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": ch_cfg.get("disable_web_preview", False),
                }, timeout=10)
                if resp.status_code == 200:
                    sent += 1
                else:
                    logger.warning(f"Telegram send failed for {cid}: {resp.text}")
            except Exception as e2:
                logger.warning(f"Telegram API error for {cid}: {e2}")

        logger.info(f"✈️ Telegram sent: {alert['title']} → {sent}/{len(chat_ids)} chats")
        return sent > 0, f"Sent to {sent}/{len(chat_ids)} chats"

    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False, str(e)


def _send_discord(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via Discord Webhook."""
    if not _HAS_REQUESTS:
        return False, "requests library not installed"
    try:
        webhook_url = ch_cfg.get("webhook_url", "")
        if not webhook_url:
            return False, "Discord webhook_url not configured"

        # Parse hex color to int
        color_hex = alert.get("color", "#FFB800").lstrip("#")
        color_int = int(color_hex, 16)

        embed = {
            "title": f"{alert['emoji']} {alert['title']}",
            "description": alert["message"],
            "color": color_int,
            "fields": [
                {"name": "Severity", "value": alert["severity"], "inline": True},
                {"name": "Symbol", "value": alert.get("symbol", "—"), "inline": True},
                {"name": "Category", "value": alert.get("category", "general"), "inline": True},
            ],
            "footer": {"text": "Gann Quant AI Alert System"},
            "timestamp": alert["timestamp"],
        }

        # Add data fields
        data = alert.get("data", {})
        for key, val in list(data.items())[:6]:
            embed["fields"].append({
                "name": str(key).replace("_", " ").title(),
                "value": str(val),
                "inline": True,
            })

        payload: Dict[str, Any] = {"embeds": [embed]}
        if ch_cfg.get("username"):
            payload["username"] = ch_cfg["username"]
        if ch_cfg.get("avatar_url"):
            payload["avatar_url"] = ch_cfg["avatar_url"]

        # Mention role for critical alerts
        mention_role = ch_cfg.get("mention_role_id", "")
        if mention_role and alert["severity"] == "CRITICAL":
            payload["content"] = f"<@&{mention_role}> 🚨 CRITICAL ALERT"

        resp = _requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            logger.info(f"💬 Discord sent: {alert['title']}")
            return True, "Sent successfully"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    except Exception as e:
        logger.error(f"Discord send error: {e}")
        return False, str(e)


def _send_slack(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via Slack Incoming Webhook."""
    if not _HAS_REQUESTS:
        return False, "requests library not installed"
    try:
        webhook_url = ch_cfg.get("webhook_url", "")
        if not webhook_url:
            return False, "Slack webhook_url not configured"

        color_map = {"CRITICAL": "danger", "HIGH": "warning", "MEDIUM": "#FFB800",
                     "LOW": "#00D4FF", "INFO": "#8B95A5"}

        payload = {
            "username": ch_cfg.get("username", "Gann Quant AI"),
            "icon_emoji": ch_cfg.get("icon_emoji", ":chart_with_upwards_trend:"),
            "attachments": [{
                "color": color_map.get(alert["severity"], "#FFB800"),
                "title": f"{alert['emoji']} {alert['title']}",
                "text": alert["message"],
                "fields": [
                    {"title": "Severity", "value": alert["severity"], "short": True},
                    {"title": "Symbol", "value": alert.get("symbol", "—"), "short": True},
                    {"title": "Category", "value": alert.get("category", "general"), "short": True},
                    {"title": "Time", "value": alert["timestamp"], "short": True},
                ],
                "footer": "Gann Quant AI Alert System",
            }],
        }

        if ch_cfg.get("channel"):
            payload["channel"] = ch_cfg["channel"]

        resp = _requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"📢 Slack sent: {alert['title']}")
            return True, "Sent successfully"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    except Exception as e:
        logger.error(f"Slack send error: {e}")
        return False, str(e)


def _send_webhook(alert: Dict, ch_cfg: Dict) -> Tuple[bool, str]:
    """Send alert via custom REST webhook."""
    if not _HAS_REQUESTS:
        return False, "requests library not installed"
    try:
        endpoints = ch_cfg.get("endpoints", [])
        if not endpoints:
            return False, "No webhook endpoints configured"

        sent = 0
        errors = []
        for ep in endpoints:
            url = ep.get("url", "")
            if not url:
                continue
            method = ep.get("method", "POST").upper()
            headers = ep.get("headers", {})
            timeout = ep.get("timeout_seconds", 10)
            payload = {
                "alert_id": alert["id"],
                "type": alert["type"],
                "severity": alert["severity"],
                "symbol": alert.get("symbol", ""),
                "title": alert["title"],
                "message": alert["message"],
                "category": alert.get("category", "general"),
                "data": alert.get("data", {}),
                "timestamp": alert["timestamp"],
                "source": "gann_quant_ai",
            }
            try:
                if method == "POST":
                    resp = _requests.post(url, json=payload, headers=headers, timeout=timeout)
                elif method == "PUT":
                    resp = _requests.put(url, json=payload, headers=headers, timeout=timeout)
                else:
                    resp = _requests.post(url, json=payload, headers=headers, timeout=timeout)
                if resp.status_code < 400:
                    sent += 1
                else:
                    errors.append(f"{url}: HTTP {resp.status_code}")
            except Exception as e2:
                errors.append(f"{url}: {e2}")

        if sent > 0:
            logger.info(f"🔗 Webhook sent: {alert['title']} → {sent}/{len(endpoints)}")
            return True, f"Sent to {sent}/{len(endpoints)} endpoints"
        return False, "; ".join(errors)

    except Exception as e:
        logger.error(f"Webhook send error: {e}")
        return False, str(e)


# Channel dispatcher map
_DISPATCHERS = {
    "email": _send_email,
    "sms": _send_sms,
    "telegram": _send_telegram,
    "discord": _send_discord,
    "slack": _send_slack,
    "webhook": _send_webhook,
}


# ═══════════════════════════════════════════════════════════════════
# ALERT HISTORY & STATE
# ═══════════════════════════════════════════════════════════════════

_alert_history: deque = deque(maxlen=500)
_alert_lock = threading.Lock()
_custom_price_alerts: Dict[str, List[Dict]] = {}  # symbol → list of price targets


def get_alert_history(limit: int = 50, severity: str = "",
                      category: str = "", symbol: str = "") -> List[Dict]:
    """Get recent alert history with optional filters."""
    with _alert_lock:
        alerts = list(_alert_history)
    # Apply filters
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.upper()]
    if category:
        alerts = [a for a in alerts if a["category"] == category]
    if symbol:
        alerts = [a for a in alerts if a.get("symbol", "").upper() == symbol.upper()]
    return alerts[-limit:]


def get_alert_stats() -> Dict[str, Any]:
    """Get alert statistics."""
    with _alert_lock:
        history = list(_alert_history)
    now = time.time()
    last_hour = [a for a in history if now - a.get("unix_ts", 0) < 3600]
    last_24h = [a for a in history if now - a.get("unix_ts", 0) < 86400]
    by_severity = {}
    for a in last_24h:
        s = a["severity"]
        by_severity[s] = by_severity.get(s, 0) + 1
    by_category = {}
    for a in last_24h:
        c = a.get("category", "general")
        by_category[c] = by_category.get(c, 0) + 1

    return {
        "total": len(history),
        "last_hour": len(last_hour),
        "last_24h": len(last_24h),
        "by_severity": by_severity,
        "by_category": by_category,
        "last_alert": history[-1] if history else None,
    }


def clear_history():
    """Clear alert history."""
    with _alert_lock:
        _alert_history.clear()
    logger.info("Alert history cleared")


# ═══════════════════════════════════════════════════════════════════
# PRICE ALERT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def add_price_alert(symbol: str, target_price: float,
                    direction: str = "above",
                    channels: Optional[List[str]] = None,
                    note: str = "") -> Dict:
    """Add a custom price alert."""
    alert_def = {
        "id": hashlib.md5(f"{symbol}:{target_price}:{direction}:{time.time()}".encode()).hexdigest()[:10],
        "symbol": symbol.upper(),
        "target_price": target_price,
        "direction": direction,  # "above" or "below"
        "channels": channels or ["telegram", "discord", "email", "desktop_push"],
        "note": note,
        "created_at": datetime.now().isoformat(),
        "triggered": False,
        "triggered_at": None,
    }
    sym = symbol.upper()
    if sym not in _custom_price_alerts:
        _custom_price_alerts[sym] = []
    _custom_price_alerts[sym].append(alert_def)
    logger.info(f"Price alert added: {sym} {direction} {target_price}")
    return alert_def


def remove_price_alert(alert_id: str) -> bool:
    """Remove a custom price alert by ID."""
    for sym, alerts in _custom_price_alerts.items():
        for i, a in enumerate(alerts):
            if a["id"] == alert_id:
                alerts.pop(i)
                logger.info(f"Price alert removed: {alert_id}")
                return True
    return False


def get_price_alerts(symbol: str = "") -> List[Dict]:
    """Get all price alerts, optionally filtered by symbol."""
    if symbol:
        return _custom_price_alerts.get(symbol.upper(), [])
    all_alerts = []
    for sym, alerts in _custom_price_alerts.items():
        all_alerts.extend(alerts)
    return all_alerts


def check_price_alerts(symbol: str, current_price: float) -> List[Dict]:
    """Check if any price alerts should trigger for given price."""
    sym = symbol.upper()
    triggered = []
    alerts = _custom_price_alerts.get(sym, [])
    for a in alerts:
        if a["triggered"]:
            continue
        should_trigger = False
        if a["direction"] == "above" and current_price >= a["target_price"]:
            should_trigger = True
        elif a["direction"] == "below" and current_price <= a["target_price"]:
            should_trigger = True
        if should_trigger:
            a["triggered"] = True
            a["triggered_at"] = datetime.now().isoformat()
            triggered.append(a)
            # Dispatch alert
            dispatch_alert(
                alert_type="price_target",
                title=f"Price Alert: {sym} {'↑' if a['direction'] == 'above' else '↓'} ${current_price:,.2f}",
                message=(
                    f"{sym} has {'risen above' if a['direction'] == 'above' else 'dropped below'} "
                    f"your target of ${a['target_price']:,.2f}.\n"
                    f"Current price: ${current_price:,.2f}"
                    f"{(' — ' + a['note']) if a.get('note') else ''}"
                ),
                severity="HIGH",
                symbol=sym,
                category="price_alerts",
                data={"target": a["target_price"], "actual": current_price, "direction": a["direction"]},
                channels=a.get("channels"),
            )
    return triggered


# ═══════════════════════════════════════════════════════════════════
# CORE DISPATCH ENGINE
# ═══════════════════════════════════════════════════════════════════

def dispatch_alert(
    alert_type: str,
    title: str,
    message: str,
    severity: str = "MEDIUM",
    symbol: str = "",
    category: str = "general",
    data: Optional[Dict] = None,
    channels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create and dispatch an alert to configured channels.
    Returns the alert object with dispatch results.
    """
    cfg = _load_config()

    # Check global enabled
    if not cfg.get("global", {}).get("enabled", True):
        return {"dispatched": False, "reason": "Alerts globally disabled"}

    # Create alert
    alert = _make_alert(alert_type, title, message, severity,
                        symbol, category, data, channels)

    # Dedup check
    if _is_duplicate(alert):
        logger.debug(f"Duplicate alert suppressed: {title}")
        return {"dispatched": False, "reason": "Duplicate suppressed"}

    # Determine channels
    ch_cfg_all = cfg.get("channels", {})
    target_channels = channels
    if not target_channels:
        # Look up default channels from alert rules
        rules = cfg.get("alert_rules", {})
        rule = rules.get(category, {})
        target_channels = rule.get("channels", ["desktop_push"])

    # CRITICAL severity → all enabled channels
    sev_conf = cfg.get("severity_config", {}).get(severity, {})
    if sev_conf.get("channels") == "all":
        target_channels = list(ch_cfg_all.keys())

    # Dispatch to each channel
    results = {}
    for ch_name in target_channels:
        ch_cfg = ch_cfg_all.get(ch_name, {})
        if not ch_cfg.get("enabled", False) and ch_name != "desktop_push":
            results[ch_name] = {"success": False, "reason": "Channel disabled"}
            continue

        # Rate limit check
        rl = ch_cfg.get("rate_limit", {})
        max_min = rl.get("max_per_minute", 30)
        max_hr = rl.get("max_per_hour", 300)
        if not _rate_limiter.check(ch_name, max_min, max_hr):
            results[ch_name] = {"success": False, "reason": "Rate limited"}
            continue

        # Dispatch
        dispatcher = _DISPATCHERS.get(ch_name)
        if dispatcher:
            try:
                success, msg = dispatcher(alert, ch_cfg)
                results[ch_name] = {"success": success, "message": msg}
            except Exception as e:
                results[ch_name] = {"success": False, "message": str(e)}
        elif ch_name == "desktop_push":
            # Desktop push — just logged, frontend handles via WebSocket
            results[ch_name] = {"success": True, "message": "Queued for desktop push"}
        else:
            results[ch_name] = {"success": False, "reason": f"Unknown channel: {ch_name}"}

    alert["dispatched"] = True
    alert["dispatch_results"] = results

    # Store in history
    with _alert_lock:
        _alert_history.append(alert)

    logger.info(
        f"Alert dispatched: [{alert['severity']}] {alert['title']} → "
        f"{sum(1 for r in results.values() if r.get('success'))}/{len(results)} channels"
    )
    return alert


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE ALERT GENERATORS
# ═══════════════════════════════════════════════════════════════════

def alert_breaking_news(title: str, body: str, symbol: str = "",
                        source: str = "", **kw) -> Dict:
    """Dispatch a breaking news alert."""
    return dispatch_alert(
        alert_type="breaking_news",
        title=f"BREAKING: {title}",
        message=f"{body}\n\nSource: {source}" if source else body,
        severity="CRITICAL",
        symbol=symbol,
        category="news_alerts",
        data={"source": source, **kw},
    )


def alert_price_spike(symbol: str, change_pct: float,
                       price: float, timeframe: str = "15m", **kw) -> Dict:
    """Dispatch a price spike/crash alert."""
    direction = "SPIKE" if change_pct > 0 else "CRASH"
    return dispatch_alert(
        alert_type=f"price_{'spike' if change_pct > 0 else 'crash'}",
        title=f"{symbol} Price {direction}: {change_pct:+.1f}%",
        message=(
            f"{symbol} has moved {change_pct:+.1f}% in the last {timeframe}.\n"
            f"Current price: ${price:,.2f}"
        ),
        severity="CRITICAL" if abs(change_pct) > 10 else "HIGH",
        symbol=symbol,
        category="price_alerts",
        data={"change_pct": change_pct, "price": price, "timeframe": timeframe, **kw},
    )


def alert_volume_spike(symbol: str, volume: float,
                        avg_volume: float, multiplier: float, **kw) -> Dict:
    """Dispatch a volume spike alert."""
    return dispatch_alert(
        alert_type="volume_spike",
        title=f"{symbol} Volume Spike: {multiplier:.1f}x Average",
        message=(
            f"Unusual volume detected for {symbol}.\n"
            f"Current: {volume:,.0f} | Average: {avg_volume:,.0f} | Ratio: {multiplier:.1f}x"
        ),
        severity="CRITICAL" if multiplier > 5 else "HIGH",
        symbol=symbol,
        category="volume_alerts",
        data={"volume": volume, "avg_volume": avg_volume, "multiplier": multiplier, **kw},
    )


def alert_technical_signal(symbol: str, signal: str,
                            details: str = "", **kw) -> Dict:
    """Dispatch a technical analysis signal alert."""
    sev_map = {"golden_cross": "HIGH", "death_cross": "CRITICAL",
               "macd_crossover": "MEDIUM", "rsi_overbought": "MEDIUM",
               "rsi_oversold": "MEDIUM", "gann_signal": "HIGH"}
    return dispatch_alert(
        alert_type=signal,
        title=f"{symbol} Technical Signal: {signal.replace('_', ' ').title()}",
        message=details or f"Technical signal detected: {signal.replace('_', ' ').title()} on {symbol}",
        severity=sev_map.get(signal, "MEDIUM"),
        symbol=symbol,
        category="technical_alerts",
        data={"signal": signal, **kw},
    )


def alert_risk_warning(symbol: str, risk_type: str,
                        details: str, **kw) -> Dict:
    """Dispatch a risk management alert."""
    sev = "CRITICAL" if risk_type in ("margin_call", "position_liquidation") else "HIGH"
    return dispatch_alert(
        alert_type=risk_type,
        title=f"⚠ RISK: {risk_type.replace('_', ' ').title()} — {symbol}",
        message=details,
        severity=sev,
        symbol=symbol,
        category="risk_alerts",
        data={"risk_type": risk_type, **kw},
    )


def alert_whale_activity(symbol: str, tx_type: str,
                          value_usd: float, details: str = "", **kw) -> Dict:
    """Dispatch a whale/large transaction alert."""
    return dispatch_alert(
        alert_type=tx_type,
        title=f"🐋 {symbol} Whale: {tx_type.replace('_', ' ').title()} — ${value_usd:,.0f}",
        message=details or f"Large {tx_type.replace('_', ' ')} detected for {symbol}: ${value_usd:,.0f}",
        severity="CRITICAL" if value_usd > 10_000_000 else "HIGH",
        symbol=symbol,
        category="whale_alerts",
        data={"tx_type": tx_type, "value_usd": value_usd, **kw},
    )


def alert_economic_event(event_name: str, impact: str = "HIGH",
                          actual: str = "", forecast: str = "",
                          previous: str = "", **kw) -> Dict:
    """Dispatch an economic calendar event alert."""
    return dispatch_alert(
        alert_type="economic_event",
        title=f"📅 Economic Event: {event_name}",
        message=(
            f"Event: {event_name}\n"
            f"Impact: {impact}\n"
            f"Actual: {actual or '—'} | Forecast: {forecast or '—'} | Previous: {previous or '—'}"
        ),
        severity="HIGH" if impact == "HIGH" else "MEDIUM",
        symbol="",
        category="news_alerts",
        data={"event": event_name, "impact": impact, "actual": actual,
              "forecast": forecast, "previous": previous, **kw},
    )


# ═══════════════════════════════════════════════════════════════════
# CHANNEL TEST & STATUS
# ═══════════════════════════════════════════════════════════════════

def test_channel(channel_name: str) -> Dict[str, Any]:
    """Send a test alert to a specific channel."""
    cfg = _load_config()
    ch_cfg = cfg.get("channels", {}).get(channel_name, {})

    if not ch_cfg:
        return {"success": False, "error": f"Channel '{channel_name}' not found in config"}
    if not ch_cfg.get("enabled", False) and channel_name != "desktop_push":
        return {"success": False, "error": f"Channel '{channel_name}' is disabled"}

    test_alert = _make_alert(
        alert_type="test",
        title="Test Alert — Gann Quant AI",
        message=(
            "This is a test notification from Gann Quant AI Alert System.\n"
            "If you received this message, the channel is configured correctly! ✅"
        ),
        severity="INFO",
        symbol="TEST",
        category="test",
    )

    dispatcher = _DISPATCHERS.get(channel_name)
    if dispatcher:
        success, msg = dispatcher(test_alert, ch_cfg)
        return {"success": success, "message": msg, "channel": channel_name}
    elif channel_name == "desktop_push":
        return {"success": True, "message": "Desktop push test queued", "channel": channel_name}
    return {"success": False, "error": f"No dispatcher for '{channel_name}'"}


def get_channels_status() -> Dict[str, Any]:
    """Get status of all notification channels."""
    cfg = _load_config()
    channels_cfg = cfg.get("channels", {})
    status = {}
    for name, ch_cfg in channels_cfg.items():
        enabled = ch_cfg.get("enabled", False)
        configured = False
        detail = ""

        if name == "email":
            configured = bool(ch_cfg.get("username")) and bool(ch_cfg.get("password"))
            detail = f"SMTP: {ch_cfg.get('smtp_host', '—')}"
        elif name == "sms":
            configured = bool(ch_cfg.get("account_sid")) and bool(ch_cfg.get("auth_token"))
            detail = f"Twilio {'✓' if _HAS_TWILIO else '✗ (pip install twilio)'}"
        elif name == "telegram":
            configured = bool(ch_cfg.get("bot_token")) and bool([c for c in ch_cfg.get("chat_ids", []) if c])
            detail = f"{len([c for c in ch_cfg.get('chat_ids',[]) if c])} chat(s)"
        elif name == "discord":
            configured = bool(ch_cfg.get("webhook_url"))
            detail = "Webhook configured" if configured else "No webhook URL"
        elif name == "slack":
            configured = bool(ch_cfg.get("webhook_url"))
            ch = ch_cfg.get("channel", "—")
            detail = f"Channel: {ch}"
        elif name == "webhook":
            eps = ch_cfg.get("endpoints", [])
            configured = any(ep.get("url") for ep in eps)
            detail = f"{len(eps)} endpoint(s)"
        elif name == "desktop_push":
            configured = True
            enabled = True
            detail = "Browser notifications"

        status[name] = {
            "enabled": enabled,
            "configured": configured,
            "ready": enabled and configured,
            "detail": detail,
            "has_library": True,
        }

        # Library dependency check
        if name in ("telegram", "discord", "slack", "webhook"):
            status[name]["has_library"] = _HAS_REQUESTS
        elif name == "sms":
            status[name]["has_library"] = _HAS_TWILIO

    return status


def get_alert_rules() -> Dict[str, Any]:
    """Get configured alert rules."""
    cfg = _load_config()
    return cfg.get("alert_rules", {})


def update_channel_config(channel_name: str, updates: Dict) -> bool:
    """Update a specific channel's configuration."""
    cfg = _load_config(force=True)
    if "channels" not in cfg:
        cfg["channels"] = {}
    if channel_name not in cfg["channels"]:
        cfg["channels"][channel_name] = {}
    cfg["channels"][channel_name].update(updates)
    return save_config(cfg)


def update_alert_rule(rule_name: str, updates: Dict) -> bool:
    """Update a specific alert rule."""
    cfg = _load_config(force=True)
    if "alert_rules" not in cfg:
        cfg["alert_rules"] = {}
    if rule_name not in cfg["alert_rules"]:
        cfg["alert_rules"][rule_name] = {}
    cfg["alert_rules"][rule_name].update(updates)
    return save_config(cfg)


# ═══════════════════════════════════════════════════════════════════
# SIMULATED NEWS FEED (for demo / testing)
# ═══════════════════════════════════════════════════════════════════

_SIMULATED_NEWS = [
    {"title": "Fed Signals Potential Rate Cut in Q2 2026", "source": "Reuters", "impact": "HIGH",
     "body": "Federal Reserve Chair Jerome Powell hinted that rate cuts could begin as early as Q2 2026, citing improving inflation data.",
     "keywords": ["Fed", "rate", "inflation"], "symbols": ["SPX", "US10Y", "EURUSD"]},
    {"title": "Bitcoin ETF Inflows Hit $2.1B Weekly Record", "source": "Bloomberg", "impact": "HIGH",
     "body": "BlackRock and Fidelity spot Bitcoin ETFs attract record inflows, signaling strong institutional demand.",
     "keywords": ["ETF", "BTC"], "symbols": ["BTCUSDT"]},
    {"title": "SEC Approves Ethereum Spot ETF Applications", "source": "CoinDesk", "impact": "CRITICAL",
     "body": "SEC grants approval for multiple Ethereum spot ETF applications. Markets surge on the news.",
     "keywords": ["SEC", "ETF", "approval"], "symbols": ["ETHUSDT"]},
    {"title": "NVIDIA Reports Record Q4 Earnings, AI Revenue Jumps 200%", "source": "CNBC", "impact": "HIGH",
     "body": "NVIDIA beats estimates with $40B quarterly revenue driven by massive AI chip demand.",
     "keywords": ["earnings"], "symbols": ["NVDA"]},
    {"title": "Gold Breaks $2,500 as Safe-Haven Demand Surges", "source": "Financial Times", "impact": "HIGH",
     "body": "Geopolitical tensions and inflation concerns drive gold to a new all-time high above $2,500/oz.",
     "keywords": ["rally"], "symbols": ["XAUUSD"]},
    {"title": "US CPI Data Shows Inflation Cooling to 2.1%", "source": "DoL", "impact": "HIGH",
     "body": "October CPI report shows inflation falling to 2.1% year-over-year, below expectations of 2.3%.",
     "keywords": ["CPI", "inflation"], "symbols": ["SPX", "US10Y"]},
    {"title": "Major DeFi Protocol Exploit: $180M Drained", "source": "The Block", "impact": "CRITICAL",
     "body": "A smart contract vulnerability leads to $180M being drained from a major DeFi lending protocol.",
     "keywords": ["hack", "exploit"], "symbols": ["ETHUSDT"]},
    {"title": "Oil Prices Surge 8% on OPEC+ Emergency Cuts", "source": "Reuters", "impact": "HIGH",
     "body": "OPEC+ announces surprise production cuts of 2M bbl/day effective immediately.",
     "keywords": ["rally"], "symbols": ["WTIUSD"]},
    {"title": "Bank of Japan Ends Negative Interest Rate Policy", "source": "Nikkei", "impact": "CRITICAL",
     "body": "BOJ raises rates for the first time in 17 years, sending USDJPY sharply lower.",
     "keywords": ["rate"], "symbols": ["USDJPY"]},
    {"title": "Tesla Unveils Autonomous Ride-Hail Network Launch", "source": "Bloomberg", "impact": "HIGH",
     "body": "Tesla announces FSD-powered robotaxi service launching in 10 US cities.",
     "keywords": ["rally"], "symbols": ["TSLA"]},
]


def get_simulated_news_feed(limit: int = 10) -> List[Dict]:
    """Get simulated news feed for testing."""
    import random
    now = datetime.now()
    feed = []
    for i, n in enumerate(_SIMULATED_NEWS[:limit]):
        ts = now - timedelta(minutes=random.randint(5, 300))
        feed.append({
            "id": f"news_{i:04d}",
            "title": n["title"],
            "body": n["body"],
            "source": n["source"],
            "impact": n["impact"],
            "keywords": n["keywords"],
            "symbols": n["symbols"],
            "timestamp": ts.isoformat(),
            "unix_ts": ts.timestamp(),
        })
    feed.sort(key=lambda x: x["unix_ts"], reverse=True)
    return feed


# Initialize config on import
_load_config()
logger.info(f"News Alert Service initialized — channels status: {get_channels_status()}")
