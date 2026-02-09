# 家用机器人/信息系统 - 后端接口规范（UniApp + Vue3 前端）

本文档定义前端所需的后端接口，包含路径、方法、请求参数、响应结构、示例、错误码约定与鉴权说明。默认 JSON。时间均使用 ISO8601（UTC+8 或明确时区）。

## 0. 基础约定
- 鉴权：建议使用 Bearer Token（Authorization: Bearer <token>），如未启用可先跳过。
- 响应约定：
  - 成功：HTTP 200/201，`{ code: 0, message: 'OK', data: {...} }`
  - 失败：HTTP 4xx/5xx，`{ code: 非0, message: '错误描述', data?: any }`
- 分页（如有）：`page`, `pageSize`，返回 `total`, `list`

---

## 1. 语音数据

### 1.1 获取近期语音交流摘要
- 路径：GET `/api/voice/recent`
- 描述：返回最近 N 天的语音交流统计与摘要（前端默认近 3 天）
- 请求参数（Query）：
  - `days` 可选，number，默认 3，范围 1~30
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "count": 14,
    "keywords": ["散步", "做饭", "天气"],
    "samples": ["今早 09:12：\"记得关火\"", "昨晚 20:05：\"和邻居聊会儿\""],
    "analysis": "近期指令理解良好，语速平稳，复述能力正常。"
  }
}
```
- 字段说明：
  - `count`: 近 N 天有效语音段数量
  - `keywords`: 关键词词云Top若干
  - `samples`: 展示用的代表性片段（已脱敏）
  - `analysis`: 文本分析结论（简要）

### 1.2 获取语音明细列表（预留）
- 路径：GET `/api/voice/list`
- 参数（Query）：
  - `startTime` 必填，string，ISO8601
  - `endTime` 必填，string，ISO8601
  - `page` 可选，number，默认1
  - `pageSize` 可选，number，默认20
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "total": 56,
    "list": [
      {
        "id": "v_170000001",
        "timestamp": "2025-09-09T09:12:33+08:00",
        "text": "记得关火",
        "emotion": "positive",
        "durationSec": 3.5,
        "source": "robot"
      }
    ]
  }
}
```

---

## 2. 评测与风险

### 2.1 获取评测预期结果
- 路径：GET `/api/assessment/expected`
- 描述：返回短期（近1-2周）认知评测预期与建议
- 请求参数：无（可扩展用户ID、设备ID由鉴权侧获取）
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "mmse": "27 ± 1",
    "risk": "疑似进展：无 · 风险低",
    "next": "2 周后",
    "focus": "记忆/定向力",
    "advice": "建议每日 10 分钟回忆训练与 1 次家属视频沟通。"
  }
}
```
- 字段说明：
  - `mmse`: 预期分数或区间字符串
  - `risk`: 风险描述（含是否有进展迹象）
  - `next`: 下次评测时间建议（人类可读）
  - `focus`: 关注维度
  - `advice`: 行动建议

### 2.2 历史评测记录（预留）
- 路径：GET `/api/assessment/history`
- 参数（Query）：`page`, `pageSize`，可选 `from`, `to`
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "total": 10,
    "list": [
      {
        "id": "a_16900001",
        "date": "2025-08-15",
        "type": "MMSE",
        "score": 27,
        "note": "稳定"
      }
    ]
  }
}
```

---

## 3. 活动与提醒（前端提示条占位）

### 3.1 获取今日关怀提醒
- 路径：GET `/api/care/alerts/today`
- 描述：返回当日对家属的关怀提醒（如步数偏低、饮水不足）
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": [
    {
      "id": "alert_001",
      "level": "warn",
      "text": "今日步数偏低，建议傍晚陪同散步 15 分钟。"
    }
  ]
}
```
- 字段说明：
  - `level`: info | warn | danger
  - `text`: 展示文案

---

## 4. 今日时间线

### 4.1 获取今日关键事件时间线
- 路径：GET `/api/timeline/today`
- 描述：返回今日关键事件简表，用于“摘要/时间线”展示
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": [
    { "time": "08:10", "event": "早餐用药✓" },
    { "time": "10:20", "event": "与邻居聊天" },
    { "time": "12:30", "event": "午休" },
    { "time": "16:00", "event": "建议散步" }
  ]
}
```

---

## 5. 角色/权限（预留给“其他角色”视图）

### 5.1 获取角色配置
- 路径：GET `/api/roles`
- 描述：返回当前用户可见的角色及权限范围
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": [
    { "role": "care", "name": "护工", "scopes": ["tasks","rounds"] },
    { "role": "doctor", "name": "医生", "scopes": ["assess","prescription"] },
    { "role": "community", "name": "社区", "scopes": ["events","alerts"] },
    { "role": "family", "name": "家属", "scopes": ["summary","alerts"] }
  ]
}
```

### 5.2 护工任务看板（预留）
- 路径：GET `/api/care/tasks/today`
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "completionRate": 0.92,
    "tasks": [
      { "id": "t1", "title": "早餐后喂药", "done": true, "time": "08:10" },
      { "id": "t2", "title": "餐后散步 15 分钟", "done": false, "time": "16:30" },
      { "id": "t3", "title": "晚间巡视", "done": false, "time": "21:00" }
    ]
  }
}
```

### 5.3 医生侧评测看板（预留）
- 路径：GET `/api/doctor/assessment/overview`
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": { "mmse": 27, "moca": 25, "trend": "stable", "last": "2025-08-15" }
}
```

### 5.4 社区事件/预警（预留）
- 路径：GET `/api/community/alerts/recent`
- 响应（200）：
```json
{
  "code": 0,
  "message": "OK",
  "data": [
    { "id": "c1", "type": "access", "time": "23:40", "text": "门禁夜间出行", "level": "warn" }
  ]
}
```

---

## 6. 错误码建议
- `0`: OK
- `1001`: 未授权或 Token 失效
- `1002`: 权限不足
- `2001`: 参数错误
- `3001`: 资源不存在
- `5000`: 服务器内部错误

---

## 7. 性能与安全建议
- GET 接口尽可能开启缓存（ETag/Last-Modified）；敏感数据禁止缓存
- 返回尽量瘦身，字段语义稳定，避免频繁变更
- 对外统一网关：支持灰度、限流与熔断
- 日志与追踪：为关键接口埋点（traceId），便于问题排查

---

## 8. 前端已对接清单
- 必需：
  - GET `/api/voice/recent`
  - GET `/api/assessment/expected`
- 可选（下一步迭代）：
  - GET `/api/care/alerts/today`
  - GET `/api/timeline/today`
  - 角色扩展相关接口
