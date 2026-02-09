// API配置文件 - 管理API地址和请求参数

// API基础配置
const API_CONFIG = {
  // API基础地址
  BASE_URL: 'http://localhost:9002',
  
  // 请求超时时间（毫秒）- 延长以适应OBS请求
  TIMEOUT: 20000,
  

  
  // 请求头配置
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  
  // API路径映射
  ENDPOINTS: {
    // 语音相关
    VOICE: {
      LIST: '/api/voice/list',
      RECENT_SUMMARY: '/api/voice/recent-summary'
    },
    
    // 对话相关
    DIALOG: {
      DETAIL: '/api/dialog/detail',
      TODAY: '/api/dialog/today',
      WEEK: '/api/dialog/week'
    },
    
    // 评测相关
    ASSESSMENT: {
      EXPECTED_RESULT: '/api/assessment/expected'
    },
    
    // 关怀提醒相关
    CARE: {
      ALERTS: '/api/care/alerts/today'
    },
    
    // 时间线相关
    TIMELINE: '/api/timeline/today',
    
    // 角色相关
    ROLE: {
      CONFIG: '/api/role/config'
    },
    
    // 患者相关
    PATIENTS: {
      LIST: '/api/patients/list'
    },
    
    // 认证相关
    AUTH: {
      LOGIN: '/api/auth/login',
      REGISTER: '/api/auth/register'
    }
  }
}

// 生成完整的API URL
export function generateApiUrl(endpoint, params = {}) {
  let url = `${API_CONFIG.BASE_URL}${endpoint}`
  
  // 替换URL中的参数占位符
  Object.keys(params).forEach(key => {
    const placeholder = `{${key}}`
    if (url.includes(placeholder)) {
      url = url.replace(placeholder, params[key])
    }
  })
  
  return url
}

// 生成查询参数字符串
export function generateQueryString(queryParams = {}) {
  if (!queryParams || Object.keys(queryParams).length === 0) {
    return ''
  }
  
  const params = new URLSearchParams()
  Object.keys(queryParams).forEach(key => {
    if (queryParams[key] !== undefined && queryParams[key] !== null) {
      params.append(key, queryParams[key])
    }
  })
  
  return `?${params.toString()}`
}

// 获取带认证信息的请求头
export function getAuthHeaders() {
  const token = uni.getStorageSync('token')
  const headers = { ...API_CONFIG.DEFAULT_HEADERS }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

// 获取错误提示信息
export function getErrorMessage(error) {
  if (!error) {
    return '未知错误'
  }
  
  // 处理HTTP错误
  if (error.code) {
    return error.message || `错误码: ${error.code}`
  }
  
  // 处理网络错误
  if (error.errMsg) {
    return error.errMsg
  }
  
  return String(error)
}

export default API_CONFIG