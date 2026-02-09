# 香橙派部署指南 - ElderCare语音助手

## 目录
1. [简介](#简介)
2. [硬件准备](#硬件准备)
3. [系统准备](#系统准备)
4. [部署步骤](#部署步骤)
5. [服务管理](#服务管理)
6. [故障排除](#故障排除)
7. [更新维护](#更新维护)

## 简介

本文档详细介绍了如何将ElderCare语音助手部署到香橙派开发板上。该部署方案适用于Orange Pi系列开发板，包括Orange Pi 4、Orange Pi PC Plus等型号。

## 硬件准备

### 必需硬件
- Orange Pi开发板（推荐Orange Pi 4 LTS）
- 电源适配器（5V/3A）
- microSD卡（至少16GB Class 10）
- USB麦克风
- 音响或耳机

### 可选硬件
- 散热片或风扇
- 外壳保护套
- HDMI显示器（调试用）

## 系统准备

### 烧录系统镜像
1. 下载适用于Orange Pi的Ubuntu/Debian镜像
2. 使用BalenaEtcher或类似工具将镜像烧录到microSD卡
3. 插入microSD卡并启动香橙派

### 系统初始配置
1. 首次启动后，使用默认用户名密码登录（通常是orangepi/orangepi）
2. 运行`sudo apt update && sudo apt upgrade`更新系统
3. 配置网络连接（WiFi或有线）
4. 启用SSH（如果需要远程访问）：
   ```bash
   sudo apt install openssh-server
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

## 部署步骤

### 1. 传输项目文件
将本地项目文件传输到香橙派：
```bash
# 在本地计算机上执行
scp -r ./voice-bot orangepi@<IP地址>:/home/orangepi/
```

或者通过Git克隆：
```bash
git clone <项目仓库地址>
```

### 2. 安装依赖
```bash
# 进入项目目录
cd voice-bot

# 给脚本添加执行权限
chmod +x deploy_orangepi.sh setup_env.sh

# 运行部署脚本（需要root权限）
sudo ./deploy_orangepi.sh
```

### 3. 环境配置
```bash
# 运行环境设置脚本
sudo ./setup_env.sh
```

### 4. 配置文件调整
根据实际环境修改配置文件：
```bash
# 编辑配置文件
sudo nano /opt/eldercare/config.py
```

确保以下配置项正确：
- 科大讯飞API密钥
- 华为云OBS配置（如需要）
- 音频设备参数

### 5. 验证部署
检查服务状态：
```bash
# 检查systemd服务状态
systemctl status eldercare.service

# 检查进程是否正常运行
ps aux | grep -E "(main\.py|api_service\.py)"
```

查看实时日志：
```bash
# 查看systemd服务日志
journalctl -u eldercare.service -f

# 如果使用同时启动脚本，查看控制台输出
```

## 服务管理

### 启动服务
```bash
# 方式1: 同时启动语音助手和API服务（推荐）
python3 start_services.py

# 方式2: 使用systemd服务启动语音助手
sudo systemctl start eldercare.service

# 方式3: 单独启动API服务
python3 api/api_service.py
```

### 停止服务
```bash
# 方式1: 停止同时运行的语音助手和API服务
# 按 Ctrl+C 组合键

# 方式2: 停止systemd服务
sudo systemctl stop eldercare.service

# 方式3: 停止单独运行的API服务
# 按 Ctrl+C 组合键
```

### 重启服务
```bash
# 方式1: 重启同时运行的语音助手和API服务
# 按 Ctrl+C 组合键停止，然后重新运行启动命令

# 方式2: 重启systemd服务
sudo systemctl restart eldercare.service
```

### 查看服务状态
```bash
# 查看systemd服务状态
sudo systemctl status eldercare.service

# 查看进程状态
ps aux | grep -E "(main\.py|api_service\.py)"
```

### 查看日志
```bash
# 实时日志
journalctl -u eldercare.service -f

# 最近的日志
journalctl -u eldercare.service --since "1 hour ago"

# 详细日志
journalctl -u eldercare.service -o verbose

# API服务日志（如果单独运行）
# 日志输出到控制台，可通过重定向保存到文件
```

## 故障排除

### 常见问题及解决方案

#### 1. 音频设备无法访问
**问题现象**: 程序无法访问麦克风或音响
**解决方案**:
```bash
# 检查音频设备
arecord -l  # 查看录音设备
aplay -l    # 查看播放设备

# 检查用户组权限
groups $USER

# 添加用户到audio组
sudo usermod -a -G audio $USER
```

#### 2. 依赖安装失败
**问题现象**: pip安装依赖时报错
**解决方案**:
```bash
# 更新pip
sudo pip3 install --upgrade pip

# 安装特定版本依赖
pip3 install -r requirements.txt --force-reinstall
```

#### 3. 服务启动失败
**问题现象**: systemctl显示服务启动失败
**解决方案**:
```bash
# 检查详细错误信息
journalctl -u eldercare.service --no-pager

# 手动运行程序查看错误
cd /opt/eldercare
python3 main.py
```

#### 4. 网络连接问题
**问题现象**: 无法连接科大讯飞API或华为云OBS
**解决方案**:
```bash
# 检查网络连接
ping baidu.com

# 检查DNS设置
cat /etc/resolv.conf

# 测试API连接
curl -I https://www.xfyun.cn/
```

### 日志分析
主要日志位置：
- systemd日志: `/var/log/journal/`
- 应用日志: `/var/log/eldercare/`（如果配置）

## 更新维护

### 更新代码
```bash
# 停止服务
sudo systemctl stop eldercare.service

# 备份当前版本
sudo cp -r /opt/eldercare /opt/eldercare.backup.$(date +%Y%m%d)

# 更新代码
cd /opt/eldercare
git pull origin main

# 重新安装依赖（如有变化）
pip3 install -r requirements.txt

# 重启服务
sudo systemctl start eldercare.service
```

### 备份配置
```bash
# 备份配置文件
sudo cp /opt/eldercare/config.py /opt/eldercare/config.py.backup.$(date +%Y%m%d)
```

### 系统维护
```bash
# 清理系统缓存
sudo apt autoremove
sudo apt autoclean

# 检查磁盘空间
df -h

# 检查系统负载
top
```

## 性能优化建议

1. **内存管理**: 监控内存使用情况，必要时增加swap空间
2. **CPU优化**: 避免同时运行多个高负载任务
3. **存储优化**: 定期清理日志文件，避免占用过多存储空间
4. **网络优化**: 使用有线连接获得更稳定的网络性能

## 安全建议

1. 修改默认用户名密码
2. 禁用不必要的服务和端口
3. 定期更新系统和软件包
4. 配置防火墙规则
5. 使用SSH密钥认证而非密码认证

## 技术支持

如有任何问题，请联系技术支持团队：
- 邮箱: support@example.com
- 电话: 400-xxx-xxxx

---
© 2025 ElderCare项目团队