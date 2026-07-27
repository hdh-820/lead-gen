# 一键部署指南

## 方案一：Railway（推荐，最简单）

Railway 免费额度足够用，支持 Python，自动分配独立域名。

### 步骤

1. 访问 https://railway.app → 用 GitHub 登录
2. 点击 "New Project" → "Deploy from GitHub"
3. 把本项目上传到你的 GitHub 仓库
4. Railway 自动检测 Python 项目并部署
5. 在 Railway 面板 Settings → Variables 添加环境变量：

```
SMTP_USER=20750337@qq.com
SMTP_PASS=ecdvngknnwtccafb
NOTIFY_EMAIL=20750337@qq.com
```

6. 部署完成后获得独立域名，如 `your-project.up.railway.app`

## 方案二：阿里云/腾讯云轻量服务器

适合长期使用，域名自定义，更专业。

```bash
# 1. SSH 登录服务器
# 2. 上传项目文件
# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建 systemd 服务
sudo tee /etc/systemd/system/lead-api.service <<'EOF'
[Unit]
Description=财税合规自测工具
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/lead-gen-app
Environment="SMTP_USER=20750337@qq.com"
Environment="SMTP_PASS=ecdvngknnwtccafb"
Environment="NOTIFY_EMAIL=20750337@qq.com"
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lead-api
sudo systemctl start lead-api
```

## 方案三：Vercel + 后端分离

前端部署到 Vercel（免费），后端用 Railway 或其他。

---

## 如果现在就要一个独立域名

你可以：
1. 把这个项目文件夹下载到本地
2. 上传到你的 GitHub（或我帮你创建）
3. 用 Railway 一键部署

需要我帮你做哪一步？
