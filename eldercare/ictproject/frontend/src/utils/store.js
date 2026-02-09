// 全局状态管理 - 使用响应式API实现简单的状态管理
import { reactive } from 'vue'
import { storage } from './helpers.js'

/**
 * 全局状态对象
 */
const store = reactive({
  // 用户信息
  user: {
    isLoggedIn: false,
    token: '',
    role: 'child', // 'child' 或 'doctor'
    info: {}
  },
  
  // 应用配置
  app: {
    theme: 'default',
    language: 'zh-CN',
    notifications: true,
    loading: false,
    lastError: null
  },
  
  // 缓存数据
  cache: {
    recentSummary: null,
    todayDialogs: null,
    weekDialogs: null,
    cacheTime: null
  }
})

/**
 * 状态管理方法
 */
const storeActions = {
  /**
   * 初始化状态 - 从本地存储加载
   */
  initialize() {
    const savedToken = uni.getStorageSync('token')
    const savedRole = uni.getStorageSync('role')
    const savedUserInfo = storage.get('userInfo', {})
    
    if (savedToken) {
      store.user.isLoggedIn = true
      store.user.token = savedToken
      store.user.role = savedRole || 'child'
      store.user.info = savedUserInfo
    }
  },
  
  /**
   * 用户登录
   * @param {Object} userData - 用户数据
   */
  login(userData) {
    store.user.isLoggedIn = true
    store.user.token = userData.token || ''
    store.user.role = userData.role || 'child'
    store.user.info = userData.userInfo || {}
    
    // 保存到本地存储
    uni.setStorageSync('token', store.user.token)
    uni.setStorageSync('role', store.user.role)
    storage.set('userInfo', store.user.info)
  },
  
  /**
   * 用户登出
   */
  logout() {
    // 清除状态
    store.user.isLoggedIn = false
    store.user.token = ''
    store.user.role = 'child'
    store.user.info = {}
    
    // 清除本地存储
    uni.removeStorageSync('token')
    uni.removeStorageSync('role')
    storage.remove('userInfo')
    
    // 清除缓存数据
    this.clearCache()
  },
  
  /**
   * 更新用户信息
   * @param {Object} userInfo - 用户信息
   */
  updateUserInfo(userInfo) {
    store.user.info = { ...store.user.info, ...userInfo }
    storage.set('userInfo', store.user.info)
  },
  
  /**
   * 设置加载状态
   * @param {boolean} isLoading - 是否加载中
   */
  setLoading(isLoading) {
    store.app.loading = isLoading
  },
  
  /**
   * 设置错误信息
   * @param {Error|string} error - 错误信息
   */
  setError(error) {
    store.app.lastError = error
    console.error('应用错误:', error)
  },
  
  /**
   * 清除错误信息
   */
  clearError() {
    store.app.lastError = null
  },
  
  /**
   * 缓存数据
   * @param {string} key - 缓存键名
   * @param {any} data - 缓存数据
   */
  setCache(key, data) {
    if (store.cache.hasOwnProperty(key)) {
      store.cache[key] = data
      store.cache.cacheTime = new Date().getTime()
    }
  },
  
  /**
   * 获取缓存数据
   * @param {string} key - 缓存键名
   * @param {number} maxAge - 最大缓存时间（毫秒）
   * @returns {any|null} - 缓存数据或null
   */
  getCache(key, maxAge = 5 * 60 * 1000) { // 默认5分钟
    if (!store.cache.hasOwnProperty(key) || !store.cache[key]) {
      return null
    }
    
    // 检查缓存是否过期
    if (maxAge && store.cache.cacheTime) {
      const now = new Date().getTime()
      if (now - store.cache.cacheTime > maxAge) {
        return null
      }
    }
    
    return store.cache[key]
  },
  
  /**
   * 清除缓存数据
   */
  clearCache() {
    store.cache = {
      recentSummary: null,
      todayDialogs: null,
      weekDialogs: null,
      cacheTime: null
    }
  },
  
  /**
   * 更新应用配置
   * @param {Object} config - 配置对象
   */
  updateConfig(config) {
    store.app = { ...store.app, ...config }
  }
}

/**
 * 导出状态和方法
 */
const appStore = {
  state: store,
  actions: storeActions
}

export default appStore