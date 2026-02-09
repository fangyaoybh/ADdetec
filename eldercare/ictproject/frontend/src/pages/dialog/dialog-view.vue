<template>
  <view class="page">
    <!-- 顶部品牌与时间 -->
    <view class="header">
      <view class="brand">
        <view class="brand-badge">
          <text class="brand-star">★</text>
        </view>
        <text class="brand-text">关爱·守护</text>
        <text class="role-tag">子女</text>
      </view>
      <text class="header-time">{{ timeText }}</text>
    </view>

    <scroll-view class="content" :scroll-y="true">
      <view class="toolbar">
        <button class="btn" @tap="refreshAll" :disabled="loading">{{ loading ? '刷新中…' : '刷新数据' }}</button>
        <text class="muted">上次更新：{{ lastUpdate || '—' }}</text>
      </view>

      <view class="grid">
        <!-- 1. 今日语音摘要 -->
        <view class="card" @tap="toggleAcc('voiceSummary')">
          <text class="trend up"></text>
          <text class="card-title">今日语音摘要</text>
          <text class="desc">查看语音交流统计</text>
          <view class="accordion" v-show="acc.voiceSummary">
            <view class="summary-stats">
              <view class="stat-item">
                <text class="stat-value">{{ todayVoiceStats.count }}</text>
                <text class="stat-label">今日对话次数</text>
              </view>
              <view class="stat-item">
                <text class="stat-value">{{ todayVoiceStats.duration }}</text>
                <text class="stat-label">今日对话时长</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 2. 今日老年痴呆预测结果 -->
        <view class="card" @tap="toggleAcc('todayAssessments')">
          <text class="trend up"></text>
          <text class="card-title">今日老年痴呆预测结果</text>
          <text class="desc">共{{ todayAssessments.length }}次评测</text>
          <view class="accordion" v-show="acc.todayAssessments">
            <view class="assessment-list">
              <view class="assessment-item" v-for="(item, index) in todayAssessments" :key="index">
                <text class="assessment-time">{{ item.time }}</text>
                <text class="assessment-result" :class="getResultClass(item.result)">{{ item.result }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 3. 老年痴呆七日综合预测结果 -->
        <view class="card" @tap="toggleAcc('weeklyStats')">
          <text class="trend up"></text>
          <text class="card-title">老年痴呆七日综合预测结果</text>
          <text class="desc">点击查看详细统计</text>
          <view class="accordion" v-show="acc.weeklyStats">
          <view class="chart-header">
            <text class="chart-title">近七日预测统计</text>
            <text class="chart-subtitle">不同健康状态的出现频率</text>
          </view>
          <view class="chart-container">
            <view class="chart-bars">
              <view
                v-for="stat in weeklyStats"
                :key="stat.type"
                class="chart-bar"
                :class="`bar-${stat.type}`"
                :style="{ height: stat.height + '%', '--target-height': stat.height + '%' }"
              >
                <view class="bar-count">{{ stat.count }}</view>
              </view>
            </view>
            <view class="chart-labels">
              <view v-for="stat in weeklyStats" :key="stat.type" class="chart-label">
                {{ getStatusLabel(stat.type) }}
              </view>
            </view>
          </view>
        </view>
        </view>

        <!-- 4. 今日关怀提醒 -->
        <view class="card" @tap="toggleAcc('todayAlerts')">
          <text class="trend" :class="getAlertTrendClass()"></text>
          <text class="card-title">今日关怀提醒</text>
          <text class="desc">{{ todayAlerts.length }}条提醒{{ getWarningCountText() }}</text>
          <view class="accordion" v-show="acc.todayAlerts">
            <view v-if="todayAlerts.length > 0">
              <!-- 先显示警告级别提醒 -->
              <view 
                v-for="(alert, index) in todayAlerts.filter(a => a.level === 'warn')" 
                :key="alert.id || index"
                class="alert-item warn"
              >
                <view class="alert-icon">⚠️</view>
                <text class="alert-content">{{ alert.text }}</text>
              </view>
              <!-- 再显示普通信息提醒 -->
              <view 
                v-for="(alert, index) in todayAlerts.filter(a => a.level !== 'warn')" 
                :key="alert.id || index"
                class="alert-item"
                :class="alert.level"
              >
                <view class="alert-icon">ℹ️</view>
                <text class="alert-content">{{ alert.text }}</text>
              </view>
            </view>
            <view v-else class="no-data">暂无提醒</view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 对话详情弹窗 -->
    <view class="dialog-detail-modal" v-if="showDialogDetail">
      <view class="dialog-detail-content">
        <view class="dialog-detail-header">
          <text class="dialog-detail-title">对话详情</text>
          <text class="dialog-detail-close" @tap="closeDialogDetail">✕</text>
        </view>
        <scroll-view class="dialog-detail-body" :scroll-y="true">
          <view v-if="currentDialog && currentDialog.dialogs && currentDialog.dialogs.length > 0">
            <view class="dialog-message" v-for="(msg, index) in currentDialog.dialogs" :key="index">
              <view class="dialog-speaker">{{ msg.role === 'user' ? '老人' : '助手' }}</view>
              <view class="dialog-text">{{ msg.text }}</view>
            </view>
          </view>
          <view v-else class="no-dialog-data">加载对话内容中...</view>
        </scroll-view>
      </view>
    </view>
    
    <!-- 退出/切换账号组件 -->
    <AccountManager />
  </view>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { voiceApi, assessmentApi, careApi, dialogApi, fetchObsTxtContent } from '../../services/api.js'
import AccountManager from '../../components/AccountManager.vue'

const loading = ref(false)
const lastUpdate = ref('')

const timeText = ref('')
function updateTime() {
  const d = new Date()
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const y = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  timeText.value = `${y}-${month}-${day} ${week[d.getDay()]} ${h}:${m}`
}

const acc = reactive({
  voiceSummary: false,
  todayAssessments: false,
  weeklyStats: false,
  todayAlerts: false
})

function toggleAcc(key) {
  acc[key] = !acc[key]
}

// 今日语音摘要数据（模拟数据）
const todayVoiceStats = reactive({
  count: '8次',
  duration: '15分钟'
})

// 今日老年痴呆预测结果（模拟数据，4-6小时一次评测）
const todayAssessments = reactive([
  { time: '2025/11/24 6.32', result: '健康' },
  { time: '2025/11/24 10.45', result: '轻微认知障碍' },
  { time: '2025/11/24 15.20', result: '健康' },
  { time: '2025/11/24 20.10', result: '健康' }
])

// 老年痴呆七日综合预测结果（使用原生实现）
const weeklyStats = reactive([
  // 修改为更合理的数据展示，确保比例合适且数字不会超出范围
  { type: 'healthy', count: 12, height: 100 },  // 保持100%高度作为基准
  { type: 'mild', count: 5, height: 50 },      // 50%高度，与基准形成明显对比
  { type: 'dementia', count: 2, height: 20 }   // 20%高度，确保可见性
]);

// 设备序列号配置
const deviceSn = ref('ElderlyMonitor_001') // 默认设备序列号

// 对话相关数据
const todayDialogs = ref([])
const weekDialogs = ref([])
const todayDialogCount = ref(0)
const weekDialogCount = ref(0)
const voiceSummary = ref({
  count: 0,
  keywords: [],
  analysis: ''
})

// 关怀提醒
const todayAlerts = ref([])

// 对话详情弹窗
const showDialogDetail = ref(false)
const currentDialog = ref(null)

// 获取评测结果对应的样式类
function getResultClass(result) {
  switch(result) {
    case '健康': return 'healthy'
    case '轻微认知障碍': return 'mild'
    case '轻度认知障碍': return 'mild'
    case '老年痴呆': return 'dementia'
    default: return 'healthy'
  }
}

function setLastUpdate() {
  const d = new Date()
  lastUpdate.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 导入直接URL获取函数和API配置
import { directFetch } from '@/services/api';
import API_CONFIG from '@/utils/api-config';

// 获取近期语音摘要 (已注释API调用，直接使用模拟数据)
async function fetchVoiceSummary() {
  try {
    // 注释掉API调用
    /*
    const result = await directFetch(
      `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.VOICE.RECENT_SUMMARY}/3`,
      {
        method: 'GET',
        mockData: {
          code: 200,
          message: 'success',
          data: {
            count: 12,
            keywords: ['散步', '天气', '吃饭'],
            analysis: '近期交流正常，老人情绪稳定。'
          }
        }
      }
    );
    */
    
    // 直接使用模拟数据
    console.log('使用模拟数据作为语音摘要');
    voiceSummary.value = {
      count: 12,
      keywords: ['散步', '天气', '吃饭'],
      analysis: '近期交流正常，老人情绪稳定。'
    };
  } catch (error) {
    console.error('获取语音摘要失败:', error);
    // 失败时使用模拟数据
    voiceSummary.value = {
      count: 12,
      keywords: ['散步', '天气', '吃饭'],
      analysis: '近期交流正常，老人情绪稳定。'
    };
  }
}

// 获取评测结果 (已注释API调用)
async function fetchAssessmentResults() {
  try {
    // 注释掉API调用
    // const result = await assessmentApi.getExpectedResult()
    // if (result && result.data) {
    //   todayResult.value = 'HC'
    //   totalResult.value = 'HC'
    // }
    
    // 直接使用模拟数据
    console.log('使用模拟数据作为评测结果');
  } catch (error) {
    console.error('获取评测结果失败:', error)
  }
}

// 获取关怀提醒 (已注释API调用，直接使用模拟数据)
async function fetchTodayAlerts() {
  try {
    // 注释掉API调用
    // const result = await careApi.getTodayAlerts()
    // if (result && result.data && result.data.alerts) {
    //   todayAlerts.value = result.data.alerts
    // }
    
    // 直接使用模拟数据
    console.log('使用模拟数据作为关怀提醒');
    todayAlerts.value = [{
      id: 'alert_mock_001',
      level: 'info',
      text: '当前是适合户外活动的时间，可建议老人进行适当散步。'
    }]
  } catch (error) {
    console.error('获取关怀提醒失败:', error)
    // 失败时使用模拟数据
    todayAlerts.value = [{
      id: 'alert_mock_001',
      level: 'info',
      text: '当前是适合户外活动的时间，可建议老人进行适当散步。'
    }]
  }
}

// 根据提醒级别获取趋势图标样式
function getAlertTrendClass() {
  const warnCount = todayAlerts.value.filter(a => a.level === 'warn').length
  if (warnCount > 0) {
    return 'warn'
  } else if (todayAlerts.value.length > 0) {
    return 'info'
  }
  return 'up'
}

// 获取警告数量文本
function getWarningCountText() {
  const warnCount = todayAlerts.value.filter(a => a.level === 'warn').length
  if (warnCount > 0) {
    return `，其中${warnCount}条需要关注`
  }
  return ''
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 获取对话数据 (已注释API调用，直接使用模拟数据)
async function fetchDialogData() {
  try {
    // 注释掉API调用
    // const todayResult = await dialogApi.getTodayDialogs(deviceSn.value)
    // if (todayResult && todayResult.data && todayResult.data.dialogs) {
    //   todayDialogs.value = todayResult.data.dialogs
    //   todayDialogCount.value = todayResult.data.dialogs.length
    // }
    // 
    // const weekResult = await dialogApi.getWeekDialogs(deviceSn.value)
    // if (weekResult && weekResult.data && weekResult.data.dialogs) {
    //   weekDialogs.value = weekResult.data.dialogs
    //   weekDialogCount.value = weekResult.data.dialogs.length
    // }
    
    // 直接使用模拟数据
    console.log('使用模拟数据作为对话数据');
    todayDialogs.value = [
      {
        dialog_time: '2025-09-28 08:30:45',
        access_url: 'http://example.com/dialog1',
        preview: '老人询问天气情况...',
        file_size: 2048
      },
      {
        dialog_time: '2025-09-28 12:15:30',
        access_url: 'http://example.com/dialog2',
        preview: '老人询问午餐建议...',
        file_size: 3072
      }
    ]
    todayDialogCount.value = todayDialogs.value.length
    
    weekDialogs.value = [
      ...todayDialogs.value,
      {
        dialog_time: '2025-09-27 15:45:20',
        access_url: 'http://example.com/dialog3',
        preview: '老人询问时间...',
        file_size: 1536
      },
      {
        dialog_time: '2025-09-26 10:20:15',
        access_url: 'http://example.com/dialog4',
        preview: '老人要求播放音乐...',
        file_size: 4096
      }
    ]
    weekDialogCount.value = weekDialogs.value.length
  } catch (error) {
    console.error('获取对话数据失败:', error)
    // 失败时使用模拟数据
    todayDialogs.value = [
      {
        dialog_time: '2025-09-28 08:30:45',
        access_url: 'http://example.com/dialog1',
        preview: '老人询问天气情况...',
        file_size: 2048
      }
    ]
    todayDialogCount.value = todayDialogs.value.length
    weekDialogs.value = todayDialogs.value
    weekDialogCount.value = weekDialogs.value.length
  }
}

// 查看对话详情 - 增强版
async function viewDialogDetail(dialog) {
  
  console.log('================================================================');
  console.log('===================== 进入viewDialogDetail函数 =====================');
  console.log('接收到的dialog参数:', JSON.stringify(dialog));
  console.log('dialog参数类型:', typeof dialog);
  
  // 防止在请求中再次点击
  if (dialogLoading.value) {
    console.log('函数提前返回：dialogLoading.value为true');
    return;
  }
  
  try {
    // 显示加载状态
    dialogLoading.value = true;
    console.log('设置dialogLoading为true，开始处理');
    
    // 先显示对话框和加载状态
    showDialogDetail.value = true;
    currentDialog.value = null;
    console.log('显示对话框，清空当前对话数据');
    
    // 详细记录dialog对象结构
    console.log('传递给API的dialog对象:', JSON.stringify(dialog));
    
    // 处理多种可能的参数来源
    let idToUse = dialog;
    let obsUrl = null;
    
    if (typeof dialog === 'object' && dialog !== null) {
      console.log('Dialog object structure:', Object.keys(dialog));
      
      // 检查是否有直接的OBS URL
      if (dialog.access_url && dialog.access_url.includes('obs.cn-north-4.myhuaweicloud.com') && dialog.access_url.endsWith('.txt')) {
        obsUrl = dialog.access_url;
        console.log('直接使用OBS URL:', obsUrl);
      } else {
        // 增强的dialog_id提取逻辑
        // 优先使用明确的dialog_id或文件名
        if (dialog.dialog_id) {
          idToUse = dialog.dialog_id;
          console.log('Using dialog.dialog_id:', idToUse);
        } else if (dialog.fileName || dialog.filename) {
          idToUse = dialog.fileName || dialog.filename;
          console.log('Using fileName/filename:', idToUse);
        } else if (dialog.id) {
          idToUse = dialog.id;
          console.log('Using dialog.id:', idToUse);
        } else if (dialog.access_url) {
          // 从URL中提取文件名，并去除URL参数
          const urlParts = dialog.access_url.split('/');
          let lastPart = urlParts[urlParts.length - 1];
          // 去除可能的URL参数部分（?及之后的内容）
          const questionMarkIndex = lastPart.indexOf('?');
          if (questionMarkIndex !== -1) {
            lastPart = lastPart.substring(0, questionMarkIndex);
          }
          // 检查是否是类似20251026_131011.txt的格式
          if (lastPart.match(/^\d{8}_\d{6}\.txt$/)) {
            idToUse = lastPart;
            console.log('Extracted filename from access_url:', idToUse);
          } else {
            idToUse = lastPart;
            console.log('Using access_url last part:', idToUse);
          }
        } else if (dialog.timestamp) {
          idToUse = dialog.timestamp;
          console.log('Using dialog.timestamp:', idToUse);
        } else if (dialog.dialog_time) {
          // 处理dialog_time字段，尝试转换为文件名格式
          // 假设格式为: 2025-10-31 08:47:20
          const timeStr = dialog.dialog_time.replace(/[-:]/g, '').replace(/\s/g, '_');
          if (timeStr) {
            idToUse = timeStr + '.txt';
            console.log('Constructed filename from dialog_time:', idToUse);
          }
        } else if (dialog.time) {
          // 如果只有时间，尝试构造文件名格式
          const timeStr = dialog.time.replace(/[-:]/g, '').replace(/\s/g, '_');
          if (timeStr) {
            idToUse = timeStr + '.txt';
            console.log('Constructed filename from time:', idToUse);
          }
        } else {
          // 遍历对象，查找符合YYYYMMDD_HHMMSS.txt格式的属性值
          for (const key in dialog) {
            const value = dialog[key];
            if (typeof value === 'string' && value.match(/^\d{8}_\d{6}\.txt$/)) {
              idToUse = value;
              console.log('Found matching filename format in key:', key, 'value:', idToUse);
              break;
            }
          }
        }
      }
    }
    
    // 额外的验证和修复逻辑
    if (typeof idToUse === 'string' && !idToUse.endsWith('.txt')) {
      // 检查是否是类似20251031_084720的格式但缺少.txt后缀
      if (idToUse.match(/^\d{8}_\d{6}$/)) {
        idToUse += '.txt';
        console.log('Added .txt suffix:', idToUse);
      }
    }
    
    // 确定最终的请求ID
    if (obsUrl) {
      // 使用OBS URL作为请求标识
      idToUse = obsUrl;
    } else {
      // 确保idToUse是字符串且有效
      if (idToUse === undefined || idToUse === null || String(idToUse).trim() === '') {
        throw new Error('对话ID不能为空');
      }
      idToUse = String(idToUse).trim();
    }
    
    console.log('正在获取对话详情，ID:', idToUse);
    
    // 添加防抖逻辑，避免短时间内多次请求同一对话
    if (lastDialogIdRequested.value === idToUse && 
        Date.now() - lastDialogRequestTime.value < 1000) {
      console.warn('对话详情请求过于频繁，跳过');
      return;
    }
    
    // 更新最后请求信息
    lastDialogIdRequested.value = idToUse;
    lastDialogRequestTime.value = Date.now();
    
    let result;
    
    // 根据是否有OBS URL决定调用方式
    if (obsUrl) {
      // 直接调用增强版的fetchObsTxtContent函数
      console.log('直接从OBS获取内容，URL:', obsUrl);
      result = await timeoutPromise(
        fetchObsTxtContent(obsUrl, false), // 不显示额外的loading，因为我们自己管理
        30000 // 对OBS直接请求使用更长的超时时间
      );
    } else {
      // 调用API获取对话详情，传入设备序列号
      console.log('===== 开始调用对话详情API =====');
      console.log('调用API获取对话详情，dialog_id:', idToUse, 'device_sn:', deviceSn.value);
      console.log('API路径: /dialog/detail');
      
      // 构建完整的URL进行调试
      const fullApiUrl = `http://localhost:9002/api/dialog/detail?dialog_id=${encodeURIComponent(idToUse)}&device_sn=${encodeURIComponent(deviceSn.value)}`;
      console.log('完整API URL:', fullApiUrl);
      
      // 使用最简化的fetch API调用方式
      try {
        console.log('开始使用fetch API调用/detail接口');
        
        // 使用从dialog参数中提取的实际idToUse
        const actualApiUrl = `http://localhost:9002/api/dialog/detail?dialog_id=${encodeURIComponent(idToUse)}&device_sn=${encodeURIComponent(deviceSn.value)}`;
        
        console.log('使用实际ID调用API，URL:', actualApiUrl);
        
        // 直接使用fetch API
        const fetchResponse = await fetch(actualApiUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 15000
        });
        
        console.log('fetch请求完成，状态码:', fetchResponse.status);
        
        if (fetchResponse.ok) {
          result = await fetchResponse.json();
          console.log('API调用成功，返回数据:', JSON.stringify(result));
          console.log('返回对话数量:', result.data.dialogs.length);
        } else {
          console.error('API请求失败:', fetchResponse.status);
          result = { code: fetchResponse.status, message: '请求失败', data: null };
          console.error('API请求失败，状态码:', fetchResponse.status);
        }
      } catch (apiError) {
        console.error('API调用发生异常:', apiError);
        const errorMessage = 'API调用异常: ' + apiError.message;
        console.error(errorMessage);
        // 即使出错也返回一个结构，避免应用崩溃
        result = { 
          code: 500, 
          message: errorMessage, 
          data: {
            dialogs: [
              { role: 'system', text: errorMessage + '\n请检查网络连接和服务状态。' }
            ]
          }
        };
      }
      
      console.log('API调用结果:', JSON.stringify(result, null, 2));
      console.log('===== 对话详情API调用结束 =====');
    }
    
    console.log('对话详情获取结果:', result);
    
    // 检查结果并更新UI
    if (result) {
      // 添加防抖检查，确保只显示最新请求的结果
      if (lastDialogIdRequested.value === idToUse) {
        // 增强的数据结构处理逻辑
        let dialogData = [];
        
        // 处理多种可能的数据结构
        if (result.data && result.data.dialogs) {
          dialogData = result.data.dialogs;
          console.log('从result.data.dialogs提取对话数据');
        } else if (result.dialogs) {
          dialogData = result.dialogs;
          console.log('从result.dialogs提取对话数据');
        } else if (Array.isArray(result)) {
          dialogData = result;
          console.log('结果本身是数组，直接使用');
        } else if (typeof result === 'string') {
          // 如果返回的是字符串，尝试解析为JSON
          try {
            const parsed = JSON.parse(result);
            dialogData = parsed.dialogs || parsed.data?.dialogs || [];
            console.log('解析字符串结果:', dialogData);
          } catch (e) {
            // 如果解析失败，将整个字符串作为一条对话
            dialogData = [{ role: 'system', text: result }];
            console.log('字符串解析失败，作为系统消息处理');
          }
        }
        
        console.log('最终提取的对话数据:', dialogData);
        console.log('对话数据长度:', dialogData.length);
        
        // 检查是否为空数据，如果是空数据则使用模拟数据
        if (!dialogData || dialogData.length === 0 || !Array.isArray(dialogData)) {
          console.log('API返回空数据或无效数据，使用模拟数据');
          currentDialog.value = {
            dialogs: [
              { role: 'user', text: '我想知道什么时候适合去散步？' },
              { role: 'assistant', text: '当然可以，建议您在上午10点到下午4点之间散步，注意防晒和补充水分。' },
              { role: 'user', text: '今天的天气怎么样？' },
              { role: 'assistant', text: '今天天气晴朗，温度适宜，适合外出活动。' }
            ]
          };
        } else {
          // 验证对话数据的格式
          const validDialogs = dialogData.filter(d => d && typeof d === 'object' && (d.role || d.text));
          console.log('有效对话数量:', validDialogs.length);
          
          if (validDialogs.length > 0) {
            console.log('使用API返回的有效对话数据');
            currentDialog.value = {
              dialogs: validDialogs
            };
          } else {
            console.log('对话数据格式无效，使用模拟数据');
            currentDialog.value = {
              dialogs: [
                { role: 'user', text: '我想知道什么时候适合去散步？' },
                { role: 'assistant', text: '当然可以，建议您在上午10点到下午4点之间散步，注意防晒和补充水分。' }
              ]
            };
          }
        }
      }
    }
  } catch (error) {
    console.error('获取对话详情失败:', error);
    // 使用setTimeout在下一个事件循环中更新UI，避免阻塞
    setTimeout(() => {
      // 如果获取失败，使用模拟数据
      currentDialog.value = {
        dialogs: [
          { role: 'user', text: '我想知道什么时候适合去散步？' },
          { role: 'assistant', text: '当然可以，建议您在上午10点到下午4点之间散步，注意防晒和补充水分。' }
        ]
      };
    }, 0);
  } finally {
    // 确保总是关闭加载状态
    setTimeout(() => {
      dialogLoading.value = false;
    }, 0);
  }
}

// 关闭对话详情弹窗
function closeDialogDetail() {
  showDialogDetail.value = false
  currentDialog.value = null
}

// 移除了测试API调用的相关代码

// 超时Promise封装，处理异步操作超时
function timeoutPromise(promise, ms) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      console.error(`操作超时（${ms}ms）`);
      reject(new Error(`操作超时（${ms}ms）`));
    }, ms);
    promise.then(
      (res) => {
        clearTimeout(timeoutId);
        resolve(res);
      },
      (err) => {
        clearTimeout(timeoutId);
        console.error('Promise执行失败:', err);
        reject(err);
      }
    );
  });
}

// 优化的数据刷新方法 - 只使用模拟数据
async function refreshAll() {
  // 添加loading状态管理
  if (loading.value) return; // 防止重复调用
  loading.value = true;
  
  try {
    // 注释掉API调用，直接使用模拟数据
    // await timeoutPromise(fetchVoiceSummary(), 20000);
    // await timeoutPromise(fetchAssessmentResults(), 20000);
    // await timeoutPromise(fetchTodayAlerts(), 20000);
    // await timeoutPromise(fetchDialogData(), 20000);
    
    // 直接使用模拟数据
    ensureMockData();
  } catch (error) {
    console.error('刷新数据失败:', error);
    // 确保即使有错误，也会使用模拟数据
    ensureMockData();
  } finally {
    setLastUpdate();
    loading.value = false;
  }
}

// 确保有模拟数据显示
function ensureMockData() {
  // 确保有对话数据
  if (todayDialogs.value.length === 0) {
    todayDialogs.value = [
      {
        dialog_time: new Date().toLocaleString('zh-CN'),
        access_url: 'mock-dialog',
        preview: '老人询问天气情况...'
      }
    ]
    todayDialogCount.value = todayDialogs.value.length
    weekDialogs.value = todayDialogs.value
    weekDialogCount.value = weekDialogCount.value || todayDialogCount.value
  }
  
  // 确保有语音摘要
  if (!voiceSummary.value.count) {
    voiceSummary.value = {
      count: 12,
      keywords: ['散步', '天气', '吃饭'],
      analysis: '近期交流正常，老人情绪稳定。'
    }
  }
  
  // 确保有关怀提醒
  if (todayAlerts.value.length === 0) {
    todayAlerts.value = [{
      id: 'alert_001',
      level: 'info',
      text: '今日交流正常，老人情绪稳定。'
    }]
  }
}

// 添加对话加载状态和防抖相关变量
const dialogLoading = ref(false);
const lastDialogIdRequested = ref('');
const lastDialogRequestTime = ref(0);

// 添加定时刷新功能
let refreshTimer = null;

// 组件生命周期管理
onMounted(() => {
  updateTime();
  setInterval(updateTime, 15000);
  
  // 使用nextTick确保DOM渲染完成后再请求数据
  nextTick(() => {
    // 添加延迟执行，避免页面刚加载就发起大量请求
    setTimeout(() => {
      refreshAll();
    }, 300);
  });
  
  // 设置定时刷新，每30秒刷新一次数据
  refreshTimer = setInterval(() => {
    if (!loading.value) { // 确保不在刷新中再刷新
      refreshAll();
    }
  }, 30000);
});

// 组件卸载时清理定时器和资源
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});

// 获取状态标签文字
function getStatusLabel(type) {
  switch(type) {
    case 'healthy': return '健康';
    case 'mild': return '轻度认知障碍';
    case 'dementia': return '老年痴呆';
    default: return '';
  }
}
</script>

<style>
/* 全局字体设置 */
.page {
  min-height: 100vh;
  background: linear-gradient(180deg,#f9f7f4,#ffffff);
  color: #4a4036;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 头部样式 - 温暖简洁 */
.header {
  padding: 24rpx;
  display:flex;
  align-items:center;
  justify-content:space-between;
  background: #ffffff;
  box-shadow: 0 2rpx 16rpx rgba(158, 142, 126, 0.1);
}

.brand {
  display:flex;
  align-items:center;
  gap: 14rpx;
}

.brand-badge {
  width: 52rpx;
  height: 52rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg,#f89b6b,#fcb677);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 18rpx rgba(248, 155, 107, 0.2);
}

.brand-star {
  color: #ffffff;
  font-weight: 800;
  font-size: 28rpx;
}

.brand-text {
  font-weight: bold;
  font-size: 32rpx;
  color: #4a4036;
}

.role-tag {
  margin-left: 12rpx;
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  color: #ffffff;
  background: linear-gradient(135deg,#f89b6b,#fcb677);
  box-shadow: 0 2rpx 8rpx rgba(248, 155, 107, 0.2);
}

.header-time {
  color:#9e8e7e;
  font-size:22rpx;
}

/* 内容区域 */
.content {
  height: calc(100vh - 120rpx);
  padding: 20rpx 20rpx 20rpx;
}

/* 工具栏 - 温暖舒适 */
.toolbar {
    margin: 40rpx 0 8rpx;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding: 16rpx 20rpx;
    background: #ffffff;
    border-radius: 20rpx;
    box-shadow: 0 4rpx 12rpx rgba(158, 142, 126, 0.05);
  }

.btn {
  border-radius: 12rpx;
  padding: 20rpx 0;
  font-weight: 500;
  font-size: 28rpx;
  transition: all 0.3s ease;
  color: #ffffff;
  background: linear-gradient(135deg, #f89b6b, #fcb677);
  box-shadow: 0 4rpx 16rpx rgba(248, 155, 107, 0.25);
  width: 100%;
  text-align: center;
}

.btn:active {
  transform: scale(0.98);
}

.muted {
  color:#9e8e7e;
}

/* 网格布局 */
.grid {
    display:flex;
    flex-direction:column;
    gap: 12rpx;
    padding-top: 8rpx;
  }

/* 淡雅风格设计 - 四个核心部分的卡片样式 */
.card {
  background: rgba(255, 255, 255, 0.95);
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  border-radius: 24rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(158, 142, 126, 0.05);
  transition: all 0.3s ease;
}

.card:active {
  background: #ffffff;
  box-shadow: 0 6rpx 20rpx rgba(158, 142, 126, 0.1);
}

/* 趋势指示 */
.trend {
  font-size: 20rpx;
  margin-bottom: 8rpx;
  display:block;
}

.trend.up {
  color: #6bb588;
}

.trend.warn {
  color: #e97865;
}

.trend.info {
  color: #6bb588;
}

/* 提醒样式 - 温暖色调提醒 */
.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 20rpx;
  margin-bottom: 16rpx;
  background: rgba(107, 181, 136, 0.15);
  border-radius: 18rpx;
  border-left: 4rpx solid #6bb588;
  transition: all 0.2s ease;
  box-shadow: 0 2rpx 8rpx rgba(158, 142, 126, 0.05);
}

.alert-item.warn {
  background: rgba(233, 120, 101, 0.15);
  border-left: 4rpx solid #e97865;
  box-shadow: 0 2rpx 8rpx rgba(233, 120, 101, 0.1);
}

.alert-item.danger {
  background: rgba(233, 120, 101, 0.2);
  border-left: 4rpx solid #e97865;
  box-shadow: 0 2rpx 8rpx rgba(233, 120, 101, 0.15);
}

.alert-item.info {
  background: rgba(107, 181, 136, 0.15);
  border-left: 4rpx solid #6bb588;
}

.alert-item:active {
  transform: scale(0.99);
}

.alert-icon {
  margin-right: 14rpx;
  font-size: 30rpx;
  margin-top: 2rpx;
  color: #6bb588;
  width: 36rpx;
  text-align: center;
}

.alert-item.warn .alert-icon,
.alert-item.danger .alert-icon {
  color: #e97865;
}

.alert-content {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.6;
  color: #4a4036;
  font-weight: 500;
}

.alert-item.warn .alert-content,
.alert-item.danger .alert-content {
  color: #e97865;
  font-weight: 600;
}

/* 卡片标题和描述 */
.card-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #4a4036;
  margin-bottom: 10rpx;
  letter-spacing: 1rpx;
}

.desc {
  color: #9e8e7e;
  font-size: 22rpx;
  margin-bottom: 12rpx;
  line-height: 1.5;
}

/* 今日语音摘要统计样式 */
.summary-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}

.stat-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 12px;
  margin: 0 8px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #495057;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #6c757d;
}

/* 今日老年痴呆预测结果样式 */
.assessment-list {
  margin-top: 16px;
}

.assessment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;
}

/* 确保预测结果在右侧显示 */


.assessment-time {
  font-size: 14px;
  color: #495057;
}

.assessment-result {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
}

.assessment-result.healthy {
  background: #d4edda;
  color: #155724;
}

.assessment-result.mild {
  background: #fff3cd;
  color: #856404;
}

.assessment-result.dementia {
  background: #f8d7da;
  color: #721c24;
}

/* 图表标题样式 */
.chart-header {
  text-align: center;
  margin-bottom: 15px;
}

.chart-title {
  font-size: 20px;
  font-weight: 700;
  color: #4a4036;
  display: block;
  margin-bottom: 5px;
}

.chart-subtitle {
  font-size: 14px;
  color: #9e8e7e;
  display: block;
}

/* 老年痴呆七日综合预测结果柱状图样式 - 美化版 */
.chart-container {
  width: 100%;
  height: 380px;
  background: linear-gradient(145deg, #ffffff, #f5f0e6);
  padding: 60px 25px 25px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  position: relative;
  border: 1px solid #e8e0d4;
  margin-top: 25px;
  box-sizing: border-box;
  overflow: visible;
  box-shadow: 0 8px 24px rgba(158, 142, 126, 0.15);
}

.chart-bars {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  height: 75%;
  width: 100%;
  margin-bottom: 25px;
  position: relative;
  z-index: 2;
}

.chart-bar {
  width: 75px;
  margin: 0 20px;
  border-radius: 8px 8px 0 0;
  position: relative;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  min-height: 25px;
  z-index: 3;
  background-image: linear-gradient(to top, rgba(255, 255, 255, 0.3), transparent);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(2px);
}

.chart-bar:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
}

/* 美化后的颜色方案 */
.bar-healthy {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  height: 100% !important;
}

.bar-mild {
  background: linear-gradient(135deg, #ffc53d 0%, #fa8c16 100%);
  height: 50% !important;
}

.bar-dementia {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  height: 15% !important;
}

.bar-count {
  position: absolute;
  top: -35px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 18px;
  font-weight: 800;
  color: #2c251e;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 6px 12px;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
  text-align: center;
  white-space: nowrap;
  min-width: 45px;
  line-height: 1;
  border: 2px solid #f0e8dc;
}

.chart-labels {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 10px;
  z-index: 1;
}

.chart-label {
  width: 75px;
  margin: 0 20px;
  text-align: center;
  font-size: 15px;
  color: #4a4036;
  font-weight: 600;
  word-wrap: break-word;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

/* 添加Y轴刻度线以增强视觉对比 */
/* 移除所有背景参考线 */

/* 兼容不同设备的样式 */
@media (max-width: 768px) {
  .chart-container {
    height: 340px;
    padding: 50px 15px 25px;
    width: 100%;
    box-sizing: border-box;
    overflow: visible;
    box-shadow: 0 6px 18px rgba(158, 142, 126, 0.12);
  }
  
  .chart-bar {
    width: 55px;
    margin: 0 12px;
    border-radius: 6px 6px 0 0;
  }
  
  .chart-bars {
    height: 72%;
    margin-bottom: 20px;
  }
  
  .chart-label {
    width: 55px;
    margin: 0 12px;
    font-size: 13px;
    font-weight: 500;
  }
  
  .bar-count {
    font-size: 16px;
    top: -30px;
    background-color: rgba(255, 255, 255, 0.95);
    padding: 5px 10px;
    border-radius: 16px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
    min-width: 40px;
    border: 1px solid #f0e8dc;
  }
}

/* 手机端专用样式优化 */
@media (max-width: 480px) {
  .page {
    padding: 10px;
    width: 100%;
    box-sizing: border-box;
  }
  
  .content {
    padding: 20rpx 24rpx 24rpx 24rpx;
    width: 100%;
    box-sizing: border-box;
  }
  
  .toolbar {
    margin: 0 0 4rpx !important;
  }
  
  .grid {
    width: 100%;
    box-sizing: border-box;
    padding-top: 4rpx !important;
    gap: 8rpx !important;
  }
  
  .card {
    padding: 20rpx;
    margin-bottom: 20rpx;
    width: 100%;
    box-sizing: border-box;
  }
  
  .accordion {
    width: 100%;
    box-sizing: border-box;
  }
  
  .chart-container {
    padding: 15px;
    height: 300px;
    box-shadow: 0 4px 12px rgba(158, 142, 126, 0.1);
  }
}

/* 优化柱状图的视觉效果 */
.bar {
  position: relative;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.bar::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0,0,0,0.1);
  border-radius: 0 0 8px 8px;
}

/* 为图表容器添加网格背景 */
.chart-container::before {
  content: '';
  position: absolute;
  top: 60px;
  left: 25px;
  right: 25px;
  bottom: 50px;
  background: 
    linear-gradient(to top, rgba(232, 224, 212, 0.3) 1px, transparent 1px),
    linear-gradient(to right, rgba(232, 224, 212, 0.3) 1px, transparent 1px);
  background-size: 20% 20%;
  z-index: 1;
  border-radius: 8px;
}

/* 为柱状图添加动画效果 */
@keyframes chartBarAppear {
  0% {
    height: 0 !important;
    opacity: 0;
  }
  100% {
    height: var(--target-height, 100%) !important;
    opacity: 1;
  }
}

.chart-bar {
  animation: chartBarAppear 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

/* 手风琴样式 */
.accordion {
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 2rpx dashed rgba(158, 142, 126, 0.1);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-8rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 文本行 */
.line {
  font-size: 24rpx;
  line-height: 1.8;
  padding: 6rpx 0;
  color: #4a4036;
}

/* 结果框样式 */
.result-boxes {
  display:flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.result-box {
  flex: 1;
  text-align:center;
  padding: 16rpx 0;
  border-radius: 16rpx;
  background: #f9f7f4;
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  transition: all 0.2s ease;
}

.result-box.active {
  border-color: #f89b6b;
  background: rgba(248, 155, 107, 0.08);
  transform: translateY(-2rpx);
}

.result-label {
  display:block;
  font-size: 32rpx;
  font-weight: 800;
  color: #f89b6b;
  margin-bottom: 4rpx;
}

.result-desc {
  font-size: 20rpx;
  color: #9e8e7e;
}

/* 段落样式 */
.para {
  font-size: 24rpx;
  line-height: 1.6;
  color: #4a4036;
}

/* 对话项样式 - 温暖舒适 */
.dialog-item {
  margin-bottom: 16rpx;
  padding: 16rpx;
  background: #f9f7f4;
  border-radius: 16rpx;
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  transition: all 0.2s ease;
}

.dialog-item:active {
  background: #f5f2ee;
  transform: scale(0.99);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.dialog-time {
  font-size: 20rpx;
  color: #f89b6b;
  font-weight: 500;
}

.dialog-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.file-size {
  font-size: 18rpx;
  color: #9e8e7e;
  padding: 4rpx 10rpx;
  background: rgba(158, 142, 126, 0.1);
  border-radius: 10rpx;
}

.view-detail-btn {
  font-size: 20rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  background: rgba(248, 155, 107, 0.15);
  color: #f89b6b;
  border: 2rpx solid rgba(248, 155, 107, 0.2);
  transition: all 0.2s ease;
}

.view-detail-btn:active {
  background: rgba(248, 155, 107, 0.25);
  transform: scale(0.98);
}

/* 对话预览 */
.dialog-preview {
  font-size: 22rpx;
  color: #4a4036;
  line-height: 1.5;
}

/* 摘要样式 */
.summary-item {
  margin-bottom: 12rpx;
  line-height: 1.5;
}

.summary-label {
  font-size: 22rpx;
  color: #f89b6b;
  margin-right: 8rpx;
  font-weight: 600;
}

.summary-value {
  font-size: 24rpx;
  color: #4a4036;
  font-weight: bold;
}

/* 关键词样式 */
.keywords {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin: 8rpx 0;
}

.keyword-tag {
  padding: 6rpx 16rpx;
  background: rgba(248, 155, 107, 0.15);
  border-radius: 12rpx;
  font-size: 20rpx;
  color: #f89b6b;
  border: 2rpx solid rgba(248, 155, 107, 0.2);
  transition: all 0.2s ease;
}

.keyword-tag:active {
  background: rgba(248, 155, 107, 0.25);
  transform: scale(0.98);
}

.summary-analysis {
  font-size: 22rpx;
  color: #4a4036;
  line-height: 1.6;
  background: #f9f7f4;
  padding: 16rpx;
  border-radius: 12rpx;
  margin-top: 8rpx;
}

/* 无数据样式 */
.no-data, .no-dialog-data {
  text-align: center;
  padding: 40rpx 20rpx;
  color: #9e8e7e;
  font-size: 22rpx;
  background: #f9f7f4;
  border-radius: 16rpx;
  border: 2rpx dashed rgba(158, 142, 126, 0.2);
}

/* 对话详情弹窗样式 - 温暖舒适 */
.dialog-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  animation: fadeIn 0.2s ease;
}

.dialog-detail-content {
  width: 88%;
  max-height: 80vh;
  background: #ffffff;
  border-radius: 28rpx;
  border: 2rpx solid rgba(248, 155, 107, 0.2);
  overflow: hidden;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.1);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.dialog-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  border-bottom: 2rpx solid rgba(158, 142, 126, 0.1);
  background: #f9f7f4;
}

.dialog-detail-title {
  font-size: 28rpx;
  font-weight: 800;
  color: #4a4036;
}

.dialog-detail-close {
  font-size: 36rpx;
  color: #9e8e7e;
  padding: 4rpx;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.dialog-detail-close:active {
  background: rgba(158, 142, 126, 0.1);
  transform: scale(0.95);
}

.dialog-detail-body {
  padding: 24rpx;
  max-height: calc(80vh - 120rpx);
  overflow-y: auto;
}

.dialog-message {
  margin-bottom: 24rpx;
  animation: fadeIn 0.2s ease;
}

.dialog-speaker {
  font-size: 20rpx;
  color: #f89b6b;
  margin-bottom: 10rpx;
  font-weight: 600;
  padding: 4rpx 12rpx;
  background: rgba(248, 155, 107, 0.1);
  border-radius: 10rpx;
  display: inline-block;
}

.dialog-text {
  font-size: 24rpx;
  color: #4a4036;
  line-height: 1.6;
  padding: 16rpx;
  background: #f9f7f4;
  border-radius: 16rpx;
  border: 2rpx solid rgba(158, 142, 126, 0.1);
}
</style>