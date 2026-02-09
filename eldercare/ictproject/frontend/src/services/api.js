// API工具类，统一处理API调用
import API_CONFIG, { generateApiUrl, generateQueryString, getAuthHeaders, getErrorMessage } from '@/utils/api-config.js'

// 获取OBS TXT文件内容（基于华为云最佳实践优化）
export async function fetchObsTxtContent(obsUrl, showLoading = true, retryCount = 2) {
  console.log('开始获取OBS TXT文件:', obsUrl)
  
  if (showLoading) {
    uni.showLoading({
      title: '加载中...',
      mask: true
    })
  }
  
  try {
    // 验证URL格式（华为云OBS最佳实践）
    if (!obsUrl || typeof obsUrl !== 'string') {
      throw new Error('无效的OBS URL')
    }
    
    // 华为云OBS域名验证
    const validOBSDomains = [
      'obs.cn-north-4.myhuaweicloud.com',
      'obs.cn-north-1.myhuaweicloud.com',
      'obs.cn-east-2.myhuaweicloud.com',
      'obs.cn-east-3.myhuaweicloud.com'
    ]
    
    const isValidOBSDomain = validOBSDomains.some(domain => obsUrl.includes(domain))
    if (!isValidOBSDomain) {
      throw new Error('非华为云OBS URL，仅支持华为云对象存储服务')
    }
    
    // 文件格式验证
    if (!obsUrl.endsWith('.txt')) {
      throw new Error('仅支持TXT文件格式')
    }
    
    // 华为云OBS最佳实践：添加超时控制和重试机制
    const fetchWithTimeout = (url, timeout = 10000) => {
      return Promise.race([
        fetch(url),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('请求超时')), timeout)
        )
      ])
    }
    
    // 使用fetch API获取文件内容（华为云推荐方式）
    const response = await fetchWithTimeout(obsUrl)
    
    if (!response.ok) {
      // 华为云OBS错误码处理
      const errorMap = {
        403: '访问被拒绝，请检查OBS桶权限设置',
        404: '文件不存在，请检查OBS对象键路径',
        500: '华为云OBS服务内部错误'
      }
      const errorMessage = errorMap[response.status] || `HTTP ${response.status}: ${response.statusText}`
      throw new Error(errorMessage)
    }
    
    const textContent = await response.text()
    console.log('获取到文件内容，长度:', textContent.length)
    
    // 内容验证（华为云最佳实践）
    if (!textContent || textContent.trim().length === 0) {
      throw new Error('OBS文件内容为空')
    }
    
    // 解析内容
    return parseTxtToDialogs(textContent)
    
  } catch (error) {
    console.error('获取OBS TXT文件失败:', error)
    
    // 华为云OBS错误分类处理
    let userFriendlyMessage = error.message
    if (error.message.includes('超时')) {
      userFriendlyMessage = '网络连接超时，请检查网络或稍后重试'
    } else if (error.message.includes('权限')) {
      userFriendlyMessage = '访问权限不足，请联系管理员检查OBS桶权限'
    }
    
    return {
      error: userFriendlyMessage,
      dialogs: []
    }
  } finally {
    if (showLoading) {
      uni.hideLoading()
    }
  }
};

// 重命名函数别名，保持向后兼容
export const fetchTxtFromOBS = fetchObsTxtContent;

// 解析TXT文件内容为对话格式
const parseTxtToDialogs = (textContent) => {
  const dialogs = []
  console.log('开始解析TXT内容:', textContent)
  
  // 首先尝试解析标准格式
  try {
    // 检查是否包含"对话内容："标记
    if (textContent.includes('对话内容：')) {
      console.log('检测到标准格式，包含"对话内容："标记')
      
      // 分割并保留后面的内容
      const contentPart = textContent.split('对话内容：')[1].trim()
      console.log('提取的对话部分:', contentPart)
      
      // 按行分割内容
      const lines = contentPart.split('\n')
      let currentRole = null
      let currentText = ''
      
      lines.forEach(line => {
        line = line.trim()
        console.log('处理行:', line)
        
        if (line) {
          // 检查是否是角色行（用户：或老人：开头）
          if (line.startsWith('用户：') || line.startsWith('老人：')) {
            console.log('检测到用户行:', line)
            // 保存之前的对话（如果有）
            if (currentRole) {
              dialogs.push({
                role: currentRole,
                text: currentText.trim()
              })
            }
            currentRole = 'user'
            // 处理中英文冒号
            const colonIndex = line.indexOf('：') > -1 ? line.indexOf('：') : line.indexOf(':')
            currentText = line.substring(colonIndex + 1).trim()
          } else if (line.startsWith('助手：')) {
            console.log('检测到助手行:', line)
            // 保存之前的对话（如果有）
            if (currentRole) {
              dialogs.push({
                role: currentRole,
                text: currentText.trim()
              })
            }
            currentRole = 'assistant'
            // 处理中英文冒号
            const colonIndex = line.indexOf('：') > -1 ? line.indexOf('：') : line.indexOf(':')
            currentText = line.substring(colonIndex + 1).trim()
          } else {
            // 不是角色行，追加到当前文本
            console.log('追加到当前文本:', line)
            currentText += '\n' + line
          }
        }
      })
      
      // 添加最后一条对话
      if (currentRole) {
        console.log('添加最后一条对话:', { role: currentRole, text: currentText.trim() })
        dialogs.push({
          role: currentRole,
          text: currentText.trim()
        })
      }
      
      // 如果成功解析出对话，返回结果
      if (dialogs.length > 0) {
        console.log('标准格式解析成功，解析出对话数量:', dialogs.length)
        return { dialogs }
      }
    }
  } catch (parseError) {
    console.warn('标准格式解析失败，尝试简单解析:', parseError)
  }
  
  // 如果标准格式解析失败，尝试简单解析
  try {
    console.log('尝试简单解析模式')
    const lines = textContent.split('\n')
    let isUserTurn = true // 简单交替角色
    
    lines.forEach(line => {
      line = line.trim()
      console.log('简单解析处理行:', line)
      if (line && !line.startsWith('时间：') && !line.startsWith('设备编号：') && !line.startsWith('对话内容：')) {
        dialogs.push({
          role: isUserTurn ? 'user' : 'assistant',
          text: line
        })
        console.log('添加对话:', { role: isUserTurn ? 'user' : 'assistant', text: line })
        isUserTurn = !isUserTurn
      }
    })
    
    // 如果成功解析出对话，返回结果
    if (dialogs.length > 0) {
      console.log('简单解析成功，解析出对话数量:', dialogs.length)
      return { dialogs }
    }
  } catch (simpleParseError) {
    console.warn('简单解析也失败:', simpleParseError)
  }
  
  // 如果都解析失败，将整个内容作为一条系统消息
  console.log('所有解析方式失败，返回原始内容')
  return {
    dialogs: [{
      role: 'system',
      text: textContent || '文件内容为空'
    }]
  }
}

// 直接URL请求函数，支持完整URL获取
export async function directFetch(url, options = {}) {
  const {
    method = 'GET',
    data = {},
    headers = {},
    showLoading = true,
    timeout = API_CONFIG.TIMEOUT
  } = options;
  
  let loadingVisible = false;
  let requestTask = null;
  let isAborted = false;
  
  try {
    // 验证URL
    if (!url || typeof url !== 'string') {
      throw new Error('URL不能为空且必须为字符串');
    }
    
    // 确保URL是完整的
    if (!url.startsWith('http')) {
      url = 'https://' + url;
    }
    
    // 显示加载提示
    if (showLoading) {
      try {
        uni.showLoading({ title: '加载中...' });
        loadingVisible = true;
      } catch (showError) {
        console.warn('显示加载提示失败:', showError);
      }
    }
    
    // 构建查询参数（对于GET请求）
    let finalUrl = url;
    if (method === 'GET' && Object.keys(data).length > 0) {
      const queryString = generateQueryString(data);
      finalUrl += queryString;
    }
    
    // 合并默认头和自定义头
    const defaultHeaders = { ...API_CONFIG.DEFAULT_HEADERS };
    const token = uni.getStorageSync('token');
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    const requestHeaders = { ...defaultHeaders, ...headers };
    
    console.log(`直接URL请求: ${method} ${finalUrl}`);
    
    // 发送请求
    const response = await new Promise((resolve, reject) => {
      if (isAborted) {
        return reject(new Error('请求已被取消'));
      }
      
      requestTask = uni.request({
        url: finalUrl,
        method,
        data: method !== 'GET' ? data : {},
        header: requestHeaders,
        timeout,
        success: (res) => {
          if (isAborted) {
            return reject(new Error('请求已被取消'));
          }
          resolve(res);
        },
        fail: (err) => {
          if (isAborted) {
            return reject(new Error('请求已被取消'));
          }
          reject(err);
        }
      });
    });
    
    // 检查响应状态
    if (response.statusCode !== 200) {
      throw {
        code: response.statusCode,
        message: `请求失败: ${response.statusCode}`,
        response
      };
    }
    
    return response.data;
  } catch (error) {
    console.error(`URL请求错误: ${url}`, error);
    
    // 不再使用模拟数据，直接抛出错误
    console.error('API请求失败，不使用模拟数据:', error);
    
    // 错误处理
    let errorMessage = '网络请求失败';
    if (error.errMsg) {
      errorMessage = error.errMsg;
      if (error.errMsg.includes('abort') || error.errMsg.includes('timeout')) {
        errorMessage = '网络请求中断或超时';
        console.warn(errorMessage);
      } else if (error.errMsg.includes('connection') || error.errMsg.includes('REFUSED')) {
        errorMessage = '服务器连接失败，请检查网络或稍后重试';
      }
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    // 显示错误提示
    if (showLoading && !error.errMsg?.includes('abort') && !error.errMsg?.includes('timeout')) {
      try {
        uni.showToast({
          title: errorMessage,
          icon: 'none',
          duration: 2000
        });
      } catch (toastError) {
        console.warn('显示错误提示失败:', toastError);
      }
    }
    
    // 返回模拟结构，避免应用崩溃
    return {
      code: error.code || 500,
      message: errorMessage,
      data: null
    };
  } finally {
    // 隐藏加载提示
    if (loadingVisible) {
      try {
        setTimeout(() => {
          uni.hideLoading();
        }, 0);
      } catch (hideError) {
        console.warn('隐藏加载提示失败:', hideError);
      }
    }
    requestTask = null;
  }
}

// 增强的统一API请求处理函数
const request = async (endpointOrUrl, method = 'GET', data = {}, urlParams = {}) => {
  // 判断是否为直接URL请求
  const isDirectUrl = typeof endpointOrUrl === 'string' && 
                     (endpointOrUrl.startsWith('http://') || 
                      endpointOrUrl.startsWith('https://'));
  
  // 如果是直接URL，调用directFetch
  if (isDirectUrl) {
    // 直接调用后端API
    return directFetch(endpointOrUrl, {
      method,
      data
    });
  }
  
  // 原始的端点请求逻辑
  let loadingVisible = false;
  let requestTask = null;
  let isAborted = false;
  
  try {
    // 显示加载提示
    try {
      uni.showLoading({ title: '加载中...' });
      loadingVisible = true;
    } catch (showError) {
      console.warn('显示加载提示失败:', showError);
    }
    
    // 构建完整URL
    let url = generateApiUrl(endpointOrUrl, urlParams);
    
    console.log(`API请求: ${method} ${url}`);
    
    // 对于GET请求，将数据作为查询参数
    if (method === 'GET') {
      const queryParams = { ...data, ...urlParams };
      if (Object.keys(queryParams).length > 0) {
        url += generateQueryString(queryParams);
        console.log(`GET请求带参数: ${url}`);
      }
    }
    
    // 获取请求头
    const headers = getAuthHeaders();
    
    // 发送请求
    console.log('发送请求:', { url, method, data, headers });
    
    // 使用Promise包装uni.request
    const response = await new Promise((resolve, reject) => {
      if (isAborted) {
        return reject(new Error('请求已被取消'));
      }
      
      requestTask = uni.request({
        url,
        method,
        data: method !== 'GET' ? data : {},
        header: headers,
        timeout: API_CONFIG.TIMEOUT,
        success: (res) => {
          if (isAborted) {
            return reject(new Error('请求已被取消'));
          }
          resolve(res);
        },
        fail: (err) => {
          if (isAborted) {
            return reject(new Error('请求已被取消'));
          }
          reject(err);
        }
      });
    });
    
    // 检查HTTP状态码
    if (response.statusCode !== 200) {
      throw {
        code: response.statusCode,
        message: `请求失败: ${response.statusCode}`,
        response
      };
    }
    
    // 获取响应数据
    const result = response.data;
    
    // 检查业务状态码
    if (result && result.code !== 200) {
      throw {
        code: result.code,
        message: result.message || '业务处理失败',
        data: result
      };
    }
    
    return result;
  } catch (error) {
    console.error('API请求错误:', error);
    console.error('请求详情:', { endpointOrUrl, method, data, urlParams });
    
    // 不再使用模拟数据，返回实际错误信息
    console.error('API请求失败，但不会返回模拟数据:', error);
    // 保留错误信息，让调用者知道实际发生了错误
    
    // 增强错误信息
    let errorMessage = '请求失败';
    if (error.errMsg) {
      errorMessage = error.errMsg;
      if (error.errMsg.includes('abort') || error.errMsg.includes('timeout')) {
        errorMessage = '网络请求中断或超时';
        console.warn(errorMessage);
      } else if (error.errMsg.includes('connection') || error.errMsg.includes('REFUSED')) {
        errorMessage = '服务器连接失败，请检查网络或稍后重试';
      }
    } else if (error.message) {
      errorMessage = error.message;
    } else if (error.code) {
      errorMessage = `错误码: ${error.code}`;
    }
    
    // 显示错误提示
    if (!error.errMsg?.includes('abort') && !error.errMsg?.includes('timeout')) {
      try {
        uni.showToast({
          title: errorMessage,
          icon: 'none',
          duration: 2000
        });
      } catch (toastError) {
        console.warn('显示错误提示失败:', toastError);
      }
    }
    
    // 返回基础结构，避免应用崩溃
    return {
      code: 200,
      message: '成功',
      data: null
    };
  } finally {
    // 隐藏加载提示
    if (loadingVisible) {
      try {
        setTimeout(() => {
          uni.hideLoading();
        }, 0);
      } catch (hideError) {
        console.warn('隐藏加载提示失败:', hideError);
      }
    }
    requestTask = null;
  }
}

// 语音相关API
export const voiceApi = {
  /**
   * 获取近期语音摘要
   * @param {number} days - 天数
   * @returns {Promise} - 返回Promise对象
   */
  getRecentSummary: (days = 3) => request(
    API_CONFIG.ENDPOINTS.VOICE.RECENT_SUMMARY,
    'GET',
    {},
    { days }
  ),
  
  /**
   * 获取语音明细列表
   * @param {Object} params - 查询参数
   * @returns {Promise} - 返回Promise对象
   */
  getVoiceList: (params) => request(
    API_CONFIG.ENDPOINTS.VOICE.LIST,
    'GET',
    params
  )
};

// 评测相关API
export const assessmentApi = {
  /**
   * 获取评测预期结果
   * @returns {Promise} - 返回Promise对象
   */
  getExpectedResult: () => request(
    API_CONFIG.ENDPOINTS.ASSESSMENT.EXPECTED_RESULT
  )
};

// 关怀提醒相关API
export const careApi = {
  /**
   * 获取今日关怀提醒
   * @returns {Promise} - 返回Promise对象
   */
  getTodayAlerts: () => request(
    API_CONFIG.ENDPOINTS.CARE.ALERTS
  )
};

// 时间线相关API
export const timelineApi = {
  /**
   * 获取今日关键事件时间线
   * @returns {Promise} - 返回Promise对象
   */
  getTodayTimeline: () => request(
    API_CONFIG.ENDPOINTS.TIMELINE
  )
};

// 角色相关API
export const roleApi = {
  /**
   * 获取角色配置
   * @returns {Promise} - 返回Promise对象
   */
  getRoles: () => request(
    API_CONFIG.ENDPOINTS.ROLE.CONFIG
  )
};

// 对话相关API
export const dialogApi = {
  /**
   * 获取对话详情
   * @param {Object|string} params - 包含对话URL或dialog_id的参数
   * @param {string} deviceSn - 设备序列号（可选，默认值会在请求中设置）
   * @returns {Promise} - 返回Promise对象
   */
  getDialogDetail: (params, deviceSn = 'ElderlyMonitor_001') => {
    // 处理参数，确保正确获取dialog_id或OBS URL
    console.log('getDialogDetail params:', params, 'deviceSn:', deviceSn);
    
    // 检查是否直接传入OBS URL
    if (typeof params === 'string') {
      // 如果字符串是OBS URL格式，直接从OBS获取
      if (params.includes('obs.cn-north-4.myhuaweicloud.com') && params.endsWith('.txt')) {
        console.log('直接从OBS URL获取TXT内容:', params);
        return fetchObsTxtContent(params);
      }
      // 否则认为是dialog_id，调用API获取
      return request(
        API_CONFIG.ENDPOINTS.DIALOG.DETAIL,
        'GET',
        { dialog_id: params, device_sn: deviceSn }
      )
    }
    
    // 处理对象参数
    if (params && typeof params === 'object') {
      // 检查是否包含OBS URL
      if (params.url && typeof params.url === 'string' && 
          params.url.includes('obs.cn-north-4.myhuaweicloud.com') && 
          params.url.endsWith('.txt')) {
        console.log('从params.url获取OBS TXT内容:', params.url);
        return fetchObsTxtContent(params.url);
      }
      if (params.access_url && typeof params.access_url === 'string' && 
          params.access_url.includes('obs.cn-north-4.myhuaweicloud.com') && 
          params.access_url.endsWith('.txt')) {
        console.log('从params.access_url获取OBS TXT内容:', params.access_url);
        return fetchObsTxtContent(params.access_url);
      }
      
      // 提取dialog_id
      let dialogId = null;
      if (params.dialog_id) {
        dialogId = params.dialog_id;
      } else if (params.id) {
        dialogId = params.id;
      } else if (params.timestamp) {
        dialogId = params.timestamp;
      } else if (params.url || params.access_url) {
        const url = params.url || params.access_url;
        // 提取URL中的文件名部分
        if (typeof url === 'string') {
          // 从URL末尾提取文件名（YYYYMMDD_HHMMSS.txt格式）
          const parts = url.split('/');
          const lastPart = parts[parts.length - 1];
          // 验证是否为正确的日期时间格式文件名
          if (lastPart.match(/^\d{8}_\d{6}\.txt$/)) {
            dialogId = lastPart;
          }
        }
      }
      // 特殊处理：如果对象有格式为YYYYMMDD_HHMMSS.txt的属性
      else {
        // 尝试从对象的其他属性中找到合适的dialog_id
        for (const key in params) {
          if (typeof params[key] === 'string' && params[key].match(/^\d{8}_\d{6}\.txt$/)) {
            dialogId = params[key];
            break;
          }
        }
        // 如果没找到，尝试直接使用对象的字符串表示
        if (!dialogId && params.toString) {
          const str = params.toString();
          if (str.match(/^\d{8}_\d{6}\.txt$/)) {
            dialogId = str;
          }
        }
      }
      
      console.log('Extracted dialogId:', dialogId);
      
      // 使用设备序列号和dialog_id调用API
      return request(
        API_CONFIG.ENDPOINTS.DIALOG.DETAIL,
        'GET',
        { dialog_id: dialogId, device_sn: deviceSn }
      )
    }
    
    // 如果参数无效，返回默认错误
    return Promise.resolve({
      code: 400,
      message: '参数无效',
      data: {
        dialogs: [{
          role: 'system',
          text: '参数无效，无法获取对话内容'
        }]
      }
    })
  },
  
  /**
   * 获取今日对话
   * @param {string} deviceSn - 设备序列号（可选，默认值会在请求中设置）
   * @returns {Promise} - 返回Promise对象
   */
  getTodayDialogs: (deviceSn = 'ElderlyMonitor_001') => request(
    API_CONFIG.ENDPOINTS.DIALOG.TODAY,
    'GET',
    { device_sn: deviceSn }
  ),
  
  /**
   * 获取近一周对话
   * @param {string} deviceSn - 设备序列号（可选，默认值会在请求中设置）
   * @returns {Promise} - 返回Promise对象
   */
  getWeekDialogs: (deviceSn = 'ElderlyMonitor_001') => request(
    API_CONFIG.ENDPOINTS.DIALOG.WEEK,
    'GET',
    { device_sn: deviceSn }
  )
};

// 函数已在上文定义并导出，此处不再重复定义

// 医生相关API
export const doctorApi = {
  /**
   * 获取患者列表
   * @returns {Promise} - 返回Promise对象
   */
  getPatients: () => request(
    API_CONFIG.ENDPOINTS.PATIENTS.LIST
  )
};

// 认证相关API
export const authApi = {
  /**
   * 用户登录
   * @param {Object} credentials - 登录凭证
   * @returns {Promise} - 返回Promise对象
   */
  login: (credentials) => request(
    API_CONFIG.ENDPOINTS.AUTH.LOGIN,
    'POST',
    credentials
  ),
  
  /**
   * 用户注册
   * @param {Object} userInfo - 用户注册信息
   * @returns {Promise} - 返回Promise对象
   */
  register: (userInfo) => request(
    API_CONFIG.ENDPOINTS.AUTH.REGISTER,
    'POST',
    userInfo
  )
};

export default {
  request,
  fetchObsTxtContent,
  voiceApi,
  assessmentApi,
  careApi,
  timelineApi,
  roleApi,
  dialogApi,
  doctorApi,
  authApi
};

// fetchObsTxtContent函数已在定义时导出，无需单独导出