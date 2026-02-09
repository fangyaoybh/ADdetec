#!/bin/bash

# 香橙派部署脚本
# 用于自动部署语音助手项目到香橙派开发板

set -e  # 遇到错误时停止执行

echo "开始部署语音助手项目到香橙派..."

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
  echo "请以root权限运行此脚本: sudo $0"
  exit 1
fi

# 创建项目目录
PROJECT_DIR="/opt/eldercare"
echo "创建项目目录: $PROJECT_DIR"
mkdir -p $PROJECT_DIR

# 复制文件到目标目录
echo "复制项目文件到 $PROJECT_DIR"
cp -r ./* $PROJECT_DIR/

# 创建虚拟环境
echo "创建Python虚拟环境"
python3 -m venv $PROJECT_DIR/venv

# 激活虚拟环境
source $PROJECT_DIR/venv/bin/activate

# 安装Python依赖
echo "安装Python依赖"
pip3 install --upgrade pip
pip3 install -r $PROJECT_DIR/requirements.txt

# 创建systemd服务文件（仅用于运行主程序）
echo "创建systemd服务文件"
cat > /etc/systemd/system/eldercare.service << EOF
[Unit]
Description=ElderCare Voice Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建API服务的systemd文件
echo "创建API服务的systemd文件"
cat > /etc/systemd/system/eldercare-api.service << EOF
[Unit]
Description=ElderCare API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/api/api_service.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
echo "重新加载systemd配置"
systemctl daemon-reload

# 启用服务
echo "启用服务"
systemctl enable eldercare.service
systemctl enable eldercare-api.service

echo "部署完成！"
echo "请运行以下命令启动服务："
echo "1. 同时启动语音助手和API服务（推荐）: python3 start_services.py"
echo "2. 使用systemd启动语音助手服务: sudo systemctl start eldercare.service"
echo "3. 使用systemd启动API服务: sudo systemctl start eldercare-api.service"
echo "4. 单独启动API服务: python3 api/api_service.py"