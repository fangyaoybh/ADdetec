// 路由配置文件 - 提供页面路由信息

const ROUTER_CONFIG = {
  // 页面路由映射
  PAGES: {
    INDEX: '/pages/index/index',
    DIALOG_VIEW: '/pages/dialog-view/dialog-view',
    DOCTOR: '/pages/doctor/index',
    LOGIN: '/pages/auth/login'
  },
  
  // 页面标题配置
  TITLES: {
    INDEX: '语音助手监控',
    DIALOG_VIEW: '对话内容查看',
    DOCTOR: '机构/医生',
    LOGIN: '登录 / 注册'
  },
  
  /**
   * 页面跳转方法
   * @param {string} pagePath - 页面路径
   * @param {Object} params - 页面参数
   * @param {Object} options - 跳转选项
   */
  navigateTo: (pagePath, params = {}, options = {}) => {
    let url = pagePath;
    
    // 添加查询参数
    const queryParams = Object.keys(params)
      .map(key => `${key}=${encodeURIComponent(params[key])}`)
      .join('&');
    
    if (queryParams) {
      url += `?${queryParams}`;
    }
    
    uni.navigateTo({
      url,
      ...options
    });
  },
  
  /**
   * 重定向到指定页面
   * @param {string} pagePath - 页面路径
   */
  redirectTo: (pagePath) => {
    uni.redirectTo({ url: pagePath });
  },
  
  /**
   * 返回上一页
   */
  navigateBack: () => {
    uni.navigateBack();
  }
};

export default ROUTER_CONFIG;