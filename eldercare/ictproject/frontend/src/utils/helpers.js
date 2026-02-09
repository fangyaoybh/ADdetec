// 通用工具函数库

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期对象或时间戳
 * @param {string} format - 格式化模板
 * @returns {string} - 格式化后的日期字符串
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  const d = new Date(date)
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
    .replace('WW', week)
}

/**
 * 获取相对时间描述
 * @param {Date|string|number} date - 日期对象或时间戳
 * @returns {string} - 相对时间描述
 */
export function getRelativeTime(date) {
  const now = new Date()
  const target = new Date(date)
  const diff = now - target
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return formatDateTime(target, 'MM-DD HH:mm')
}

/**
 * 本地存储工具
 */
export const storage = {
  /**
   * 存储数据
   * @param {string} key - 存储键名
   * @param {any} value - 存储值
   */
  set: (key, value) => {
    try {
      const jsonValue = JSON.stringify(value)
      uni.setStorageSync(key, jsonValue)
    } catch (error) {
      console.error('存储数据失败:', error)
    }
  },
  
  /**
   * 获取数据
   * @param {string} key - 存储键名
   * @param {any} defaultValue - 默认值
   * @returns {any} - 存储的数据
   */
  get: (key, defaultValue = null) => {
    try {
      const jsonValue = uni.getStorageSync(key)
      return jsonValue ? JSON.parse(jsonValue) : defaultValue
    } catch (error) {
      console.error('读取数据失败:', error)
      return defaultValue
    }
  },
  
  /**
   * 删除数据
   * @param {string} key - 存储键名
   */
  remove: (key) => {
    try {
      uni.removeStorageSync(key)
    } catch (error) {
      console.error('删除数据失败:', error)
    }
  },
  
  /**
   * 清空所有数据
   */
  clear: () => {
    try {
      uni.clearStorageSync()
    } catch (error) {
      console.error('清空数据失败:', error)
    }
  }
}

/**
 * 获取评测结果标签类名
 * @param {string} result - 评测结果
 * @returns {string} - CSS类名
 */
export function getResultTagClass(result) {
  if (!result) return 'default'
  
  if (result.includes('中度') || result === 'AD') return 'danger'
  if (result.includes('轻度') || result === 'MCI') return 'warn'
  if (result === '健康' || result === 'HC') return 'ok'
  
  return 'default'
}

/**
 * 获取评测结果描述
 * @param {string} result - 评测结果
 * @returns {string} - 详细描述
 */
export function getResultDescription(result) {
  const descMap = {
    'HC': '健康认知状态',
    'MCI': '轻度认知障碍',
    'AD': '阿尔茨海默病',
    '健康': '认知功能正常，无明显异常',
    '轻度': '轻度认知障碍，需要定期观察',
    '中度': '中度认知障碍，建议就医治疗',
    '重度': '重度认知障碍，需要专业照护'
  }
  
  return descMap[result] || '未知状态'
}

/**
 * 防抖函数
 * @param {Function} func - 需要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} - 防抖后的函数
 */
export function debounce(func, wait = 300) {
  let timeout = null
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 节流函数
 * @param {Function} func - 需要节流的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function} - 节流后的函数
 */
export function throttle(func, limit = 300) {
  let inThrottle = false
  
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 安全的JSON解析
 * @param {string} jsonStr - JSON字符串
 * @param {any} defaultValue - 默认值
 * @returns {any} - 解析后的数据
 */
export function safeJsonParse(jsonStr, defaultValue = null) {
  try {
    return jsonStr ? JSON.parse(jsonStr) : defaultValue
  } catch (error) {
    console.error('JSON解析失败:', error)
    return defaultValue
  }
}