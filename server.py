# -*- coding: utf-8 -*-
"""
财税合规自测工具 - 后端 API 服务
功能：接收前端表单提交，推送到企业微信机器人 + QQ邮箱
"""

import os
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx

# ========== 配置 ==========
# 企业微信机器人 Webhook 地址（从群机器人复制）
WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE")

# QQ邮箱 SMTP 配置
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "20750337@qq.com")       # 你的QQ邮箱
SMTP_PASS = os.getenv("SMTP_PASS", "ecdvngknnwtccafb")    # QQ邮箱授权码
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "20750337@qq.com")  # 接收通知的邮箱

# 日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI(title="财税合规自测工具 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 数据模型 ==========
class LeadData(BaseModel):
    name: str = Field(..., min_length=1, description="姓名")
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    desc: str = Field(default="", description="需求描述")
    scenario: Optional[str] = Field(default="", description="场景类型")
    amount: Optional[float] = Field(default=0, description="测算金额（万元）")

# ========== 场景中文名映射 ==========
SCENARIO_MAP = {
    "dividend": "股东分红",
    "brokerage": "居间费/佣金",
    "labor": "劳务费",
}

# ========== 企业微信推送 ==========
async def send_wecom(lead: LeadData) -> bool:
    """推送到企业微信群机器人"""
    scenario_cn = SCENARIO_MAP.get(lead.scenario, lead.scenario or "未指定")
    amount_str = f"{lead.amount}万元" if lead.amount and lead.amount > 0 else "未填写"

    markdown = f"""## 📩 新线索提醒

> **姓名**：{lead.name}
> **手机**：{lead.phone}
> **场景**：{scenario_cn}
> **测算金额**：{amount_str}
> **需求描述**：{lead.desc or "未填写"}
> **时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

[点击拨号](tel:{lead.phone})"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                WECOM_WEBHOOK,
                json={
                    "msgtype": "markdown",
                    "markdown": {"content": markdown}
                }
            )
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info(f"企业微信推送成功: {lead.name} {lead.phone}")
                return True
            else:
                logger.error(f"企业微信推送失败: {result}")
                return False
    except Exception as e:
        logger.error(f"企业微信推送异常: {e}")
        return False

# ========== 邮件推送 ==========
async def send_email(lead: LeadData) -> bool:
    """通过QQ邮箱SMTP发送通知"""
    scenario_cn = SCENARIO_MAP.get(lead.scenario, lead.scenario or "未指定")
    amount_str = f"{lead.amount}万元" if lead.amount and lead.amount > 0 else "未填写"

    subject = f"【新线索】{lead.name} - {scenario_cn} - {amount_str}"

    html = f"""
    <div style="font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; max-width: 500px; padding: 20px;">
        <h2 style="color: #8B6914; border-bottom: 2px solid #C49A52; padding-bottom: 8px;">📩 新线索提醒</h2>
        <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
            <tr><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600; width: 80px;">姓名</td><td style="padding: 8px 12px;">{lead.name}</td></tr>
            <tr style="background: #FAF6F0;"><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600;">手机</td><td style="padding: 8px 12px;">{lead.phone}</td></tr>
            <tr><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600;">场景</td><td style="padding: 8px 12px;">{scenario_cn}</td></tr>
            <tr style="background: #FAF6F0;"><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600;">测算金额</td><td style="padding: 8px 12px;">{amount_str}</td></tr>
            <tr><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600;">需求描述</td><td style="padding: 8px 12px;">{lead.desc or "未填写"}</td></tr>
            <tr style="background: #FAF6F0;"><td style="padding: 8px 12px; color: #6B5A44; font-weight: 600;">提交时间</td><td style="padding: 8px 12px;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
        </table>
        <p style="margin-top: 16px; color: #8B7355; font-size: 12px;">线索来源：财税合规自测工具</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [NOTIFY_EMAIL], msg.as_string())
        logger.info(f"邮件推送成功: {lead.name} -> {NOTIFY_EMAIL}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("QQ邮箱SMTP认证失败，请检查授权码是否正确")
        return False
    except Exception as e:
        logger.error(f"邮件推送异常: {e}")
        return False

# ========== API 路由 ==========
import os as _os
_STATIC_DIR = _os.path.dirname(_os.path.abspath(__file__))

@app.get("/")
async def root():
    """返回前端首页"""
    return FileResponse(_os.path.join(_STATIC_DIR, "index.html"))

@app.post("/api/leads")
async def create_lead(lead: LeadData):
    """接收前端提交的线索"""
    logger.info(f"收到线索: {lead.name} {lead.phone} {lead.scenario}")

    # 并行推送
    wecom_ok = await send_wecom(lead)
    email_ok = await send_email(lead)

    return {
        "success": True,
        "message": "提交成功，顾问将在24小时内联系您",
        "channels": {
            "wecom": "已推送" if wecom_ok else "推送失败",
            "email": "已推送" if email_ok else "推送失败",
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 静态文件服务（前端 SPA）
# 挂载在根路径，API 路由优先级更高（先注册的优先）
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

# ========== 启动 ==========
if __name__ == "__main__":
    import uvicorn
    logger.info("启动财税合规自测工具 API 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
