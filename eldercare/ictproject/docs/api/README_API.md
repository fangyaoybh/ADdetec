# 老年痴呆监测系统 - 前后端对接说明

## 项目概述

本文档描述了老年痴呆监测系统的前后端对接方案，包括API接口调用方式、数据格式、错误处理和跨域解决方案。

## 后端API服务

### 启动方式

1. 确保已安装Python环境
2. 运行以下命令启动API服务器：

```bash
# Windows系统
start_api_server.bat

# 或直接运行
python api_service.py
```

服务器将在 `http://localhost:9002` 启动

### 主要API接口

| 模块 | 接口 | 方法 | 功能描述 |
|------|------|------|----------|
| 语音 | /api/voice/recent-summary/{days} | GET | 获取近期语音摘要 |
| 语音 | /api/voice/list | GET | 获取语音明细列表 |
| 评估 | /api/assessment/expected-result | GET | 获取评测预期结果 |
| 关怀 | /api/care/alerts | GET | 获取关怀提醒 |
| 对话 | /api/dialog/detail | GET | 获取对话详情 |
| 对话 | /api/dialog/today | GET | 获取今日对话 |
| 对话 | /api/dialog/week | GET | 获取一周对话 |
| 时间线 | /api/timeline | GET | 获取时间线 |
| 角色 | /api/role/config | GET | 获取角色配置 |
| 患者 | /api/patients/list | GET | 获取患者列表 |
| 认证 | /api/auth/login | POST | 用户登录 |

## 前端API对接

### API工具类使用方法

```javascript
// 导入API模块
import { voiceApi, assessmentApi, dialogApi } from '../../utils/api.js'

// 使用示例
async function fetchData() {
  try {
    // 获取语音摘要
    const summary = await voiceApi.getRecentSummary(3)
    
    // 获取评测结果
    const result = await assessmentApi.getExpectedResult()
    
    // 获取今日对话
    const dialogs = await dialogApi.getTodayDialogs()
    
    // 获取对话详情
    const dialogDetail = await dialogApi.getDialogDetail('dialog_2025-09-28_01')
  } catch (error) {
    // 错误处理已在API工具类中统一处理
  }
}
```

### 新增页面

- **对话查看页面**：`src/pages/dialog-view/dialog-view.vue`
  - 实现了与后端API的完整对接
  - 支持查看今日和一周对话列表
  - 提供对话详情查看功能
  - 显示语音摘要和关怀提醒

## 配置说明

### API配置

API基础配置位于 `src/utils/api-config.js`，可以修改以下配置：

- `BASE_URL`: API基础地址
- `TIMEOUT`: 请求超时时间
- `MOCK_MODE`: 模拟数据模式
- `DEFAULT_HEADERS`: 默认请求头

### 跨域配置

后端API服务已配置CORS中间件，允许所有来源的请求访问。生产环境中应设置具体的前端域名。

## 数据格式

### 响应格式

所有API响应统一采用以下格式：

```json
{
  "code": 200,          // 状态码，200表示成功
  "message": "success", // 状态描述
  "data": {}            // 业务数据
}
```

### 错误处理

- HTTP状态码：用于表示网络请求状态
- 业务状态码：在响应体中，用于表示业务处理状态
- 统一的错误提示已在API工具类中实现

## 功能验证

1. **启动后端服务**：运行 `start_api_server.bat`
2. **运行前端项目**：使用HBuilderX或其他工具运行前端项目
3. **访问新增页面**：导航到 `/pages/dialog-view/dialog-view`
4. **测试功能**：
   - 点击刷新数据按钮获取最新数据
   - 展开各卡片查看详细信息
   - 点击"查看详情"按钮查看对话内容

## 安全性考虑

- API请求使用Bearer Token进行认证
- 实现了基本的输入验证和错误处理
- 生产环境中应进一步加强安全措施

## 性能优化

- 使用并行请求优化数据加载速度
- 实现了加载提示和错误反馈
- 建议在实际部署时启用数据缓存机制