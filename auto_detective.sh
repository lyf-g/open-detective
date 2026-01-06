#!/bin/bash

# Open-Detective 自动化维护脚本
# 执行内容：提交代码 -> 强制构建 -> 重启服务

echo "🕵️‍♂️ Starting Open-Detective Maintenance..."

# 1. 提交代码记录
echo "📦 Staging and Committing changes..."
git add .
git commit -m "feat: total professional evolution - UI upgrade, sanitization, and interpretation logic"

# 2. 强制重新构建并重启
echo "🚀 Rebuilding and Restarting containers..."
docker-compose down
docker-compose up -d --build

echo "✅ Investigation system is now UP and CLEAN!"
echo "Visit http://localhost:8082 to start your mission."
