#!/bin/bash

# 香橙派环境设置脚本
# 用于设置语音助手运行所需环境变量和权限

echo "==========================================="
echo "  ElderCare语音助手 - 环境设置脚本"
echo "==========================================="

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
  echo "请以root权限运行此脚本:"
  echo "sudo $0"
  exit 1
fi

# 设置音频权限
echo "设置音频权限..."
usermod -a -G audio $SUDO_USER

# 创建环境变量配置文件
ENV_FILE="/etc/environment"
echo "设置环境变量..."

# 检查环境变量是否已存在
if ! grep -q "ELDERCARE_HOME" $ENV_FILE; then
    echo "ELDERCARE_HOME=/opt/eldercare" >> $ENV_FILE
fi

# 创建udev规则以允许普通用户访问音频设备
echo "创建udev规则..."
cat > /etc/udev/rules.d/99-audio.rules << EOF
# Allow audio access for all users
KERNEL=="pcmC*D*", SUBSYSTEM=="sound", GROUP="audio", MODE="0666"
KERNEL=="controlC*", SUBSYSTEM=="sound", GROUP="audio", MODE="0666"
EOF

# 重新加载udev规则
echo "重新加载udev规则..."
udevadm control --reload-rules
udevadm trigger

# 设置应用目录权限
echo "设置应用目录权限..."
chown -R $SUDO_USER:audio /opt/eldercare
chmod -R 755 /opt/eldercare

# 创建日志目录
mkdir -p /var/log/eldercare
chown $SUDO_USER:audio /var/log/eldercare

echo "==========================================="
echo "环境设置完成！"
echo "请重新登录或执行以下命令加载环境变量:"
echo "source /etc/environment"
echo "==========================================="