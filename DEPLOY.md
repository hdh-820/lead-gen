# 财税合规自测工具 - 部署指南

## 文件结构

```
lead-gen-app/
├── index.html          # 前端 SPA（自测工具 + 留资表单）
├── server.py           # 后端 API（FastAPI）
├── requirements.txt    # Python 依赖
└── DEPLOY.md           # 本文件
```

## 一、配置推送通道

编辑 `server.py` 中的环境变量（或通过系统环境变量设置）：

### 1. 企业微信机器人

```bash
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的KEY"
```

获取方式：企业微信 → 目标群 → 群设置 → 群机器人 → 添加机器人 → 复制 Webhook 地址

### 2. QQ邮箱 SMTP

```bash
export SMTP_USER="your_qq@qq.com"
export SMTP_PASS="你的QQ邮箱授权码"
export NOTIFY_EMAIL="接收通知的邮箱@qq.com"
```

获取授权码：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 生成授权码

## 二、本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量后启动
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
export SMTP_USER="your@qq.com"
export SMTP_PASS="授权码"
export NOTIFY_EMAIL="your@qq.com"

python3 server.py
```

服务运行在 http://localhost:8080

## 三、部署到服务器

### 方式1：云服务器 + Nginx 反代（推荐）

```bash
# 1. 上传文件到服务器
scp -r lead-gen-app/ user@your-server:/opt/

# 2. 安装依赖并启动
cd /opt/lead-gen-app
pip install -r requirements.txt

# 3. 使用 systemd 守护进程
sudo tee /etc/systemd/system/lead-api.service <<EOF
[Unit]
Description=财税合规自测工具 API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lead-gen-app
Environment="WECOM_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
Environment="SMTP_USER=your@qq.com"
Environment="SMTP_PASS=授权码"
Environment="NOTIFY_EMAIL=your@qq.com"
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lead-api
sudo systemctl start lead-api
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /opt/lead-gen-app;
    index index.html;

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 方式2：Vercel / Cloudflare Pages（仅前端）

前端 index.html 可直接部署到 Vercel/Cloudflare Pages。
后端 server.py 需要单独部署到云服务器或使用 Vercel Serverless Functions。

## 四、前端 API 地址配置

部署后，修改 `index.html` 中的 `API_BASE`：

```javascript
const API_BASE = 'https://your-domain.com';  // 你的后端地址
```

## 五、验证

```bash
# 健康检查
curl https://your-domain.com/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","phone":"13800138000","scenario":"dividend","amount":100}'
```

预期：
- 企业微信群收到消息
- 邮箱收到通知邮件
- API 返回 `{"success": true}`
