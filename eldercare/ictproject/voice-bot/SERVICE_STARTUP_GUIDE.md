# 服务启动指南

## 概述

本项目包含两个主要服务：
1. 语音助手主程序 - 处理语音识别、自然语言处理和语音合成
2. API服务 - 提供RESTful API接口，用于获取语音助手的数据和状态

## 启动方式

### 推荐方式：同时启动两个服务

```bash
python start_services.py
```

此脚本会同时启动语音助手主程序和API服务，并确保它们能够协同工作。

### 单独启动服务

#### 启动语音助手主程序
```bash
python main.py
```

#### 启动API服务
```bash
python api/api_service.py
```

默认情况下，API服务会在9002端口上运行。

## 端口配置

### API服务端口

API服务默认使用9002端口，但可以通过命令行参数指定其他端口：

```bash
python api/api_service.py 9003
```

### 端口冲突处理

start_services.py脚本具有自动端口检测功能：
- 如果默认端口(9002)被占用，它会自动尝试9003、9004等端口
- 端口检测范围：9002-9010
- 如果所有端口都被占用，会提示手动释放端口

## 验证服务状态

### 检查API服务

访问Swagger文档界面：
```
http://localhost:9002/docs
```

或者检查API根路径：
```
curl http://localhost:9002/
```

## 常见问题解决

### 权限错误

如果遇到"[Errno 13] 以一种访问权限不允许的方式做了一个访问套接字的尝试"错误：

1. 确保使用的端口号大于1024
2. 当前配置已将默认端口设置为9002，避免了常见的权限问题

### 端口占用

如果遇到端口占用问题：

1. 使用start_services.py脚本，它会自动检测并切换到可用端口
2. 或者手动指定端口号：
   ```bash
   python api/api_service.py 9003
   ```

## 服务管理

### 停止服务

当使用start_services.py启动服务时，按Ctrl+C可以同时停止两个服务。

### 查看运行中的服务

在Windows上：
```powershell
tasklist | findstr python
```

### 检查端口占用

```powershell
netstat -ano | findstr :9002
```