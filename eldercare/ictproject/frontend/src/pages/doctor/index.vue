<template>
  <view class="page">
    <!-- 顶部品牌与时间 - 参考dialog-view样式 -->
    <view class="header">
      <view class="brand">
        <view class="brand-badge">
          <text class="brand-star">★</text>
        </view>
        <text class="brand-text">关爱·守护</text>
        <text class="role-tag">医生</text>
      </view>
      <text class="header-time">{{ timeText }}</text>
    </view>

    <!-- 内容区域 - 使用scroll-view确保可滚动 -->
    <scroll-view class="content" :scroll-y="true">
      <!-- 工具栏 -->
      <view class="toolbar">
        <text class="toolbar-title">患者列表</text>
        <text class="toolbar-subtitle">共{{ patients.length }}位患者</text>
      </view>

      <!-- 网格布局 - 参考dialog-view的卡片式设计 -->
      <view class="grid">
        <view v-for="(p, index) in patients" :key="p.id" class="card">
          <!-- 患者基本信息 -->
          <view class="patient-main">
            <view class="patient-header">
              <text class="patient-name">{{ p.name }}</text>
              <text class="patient-age">{{ p.age }}岁</text>
            </view>
            <view class="patient-footer">
              <text class="assessment-time">上次：{{ p.date }}</text>
              <view class="status-tag" :class="getResultClass(p.result)">
                {{ p.result }}
              </view>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
    <!-- 退出/切换账号组件 -->
    <AccountManager />
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AccountManager from '../../components/AccountManager.vue'

const timeText = ref('')
function updateTime(){
  const d = new Date()
  const week = ['周日','周一','周二','周三','周四','周五','周六']
  const y = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2,'0')
  const day = String(d.getDate()).padStart(2,'0')
  const h = String(d.getHours()).padStart(2,'0')
  const m = String(d.getMinutes()).padStart(2,'0')
  timeText.value = `${y}-${month}-${day} ${week[d.getDay()]} ${h}:${m}`
}

// 医生页面的患者数据
const patients = reactive([
  { id: 1, name: '王大爷', age: 78, result: '健康', date: '2025/11/24 10:30', assessments: [
    { time: '2025/11/24 10:30', score: 85, result: '健康' },
    { time: '2025/11/23 14:20', score: 87, result: '健康' }
  ]},
  { id: 2, name: '李奶奶', age: 82, result: '轻微认知障碍', date: '2025/11/24 09:15', assessments: [
    { time: '2025/11/24 09:15', score: 62, result: '轻微认知障碍' },
    { time: '2025/11/23 16:40', score: 65, result: '轻微认知障碍' }
  ]},
  { id: 3, name: '张爷爷', age: 85, result: '老年痴呆', date: '2025/11/24 11:45', assessments: [
    { time: '2025/11/24 11:45', score: 40, result: '老年痴呆' },
    { time: '2025/11/23 08:30', score: 42, result: '老年痴呆' }
  ]},
  { id: 4, name: '赵奶奶', age: 79, result: '健康', date: '2025/11/24 08:20', assessments: [
    { time: '2025/11/24 08:20', score: 90, result: '健康' },
    { time: '2025/11/23 10:15', score: 88, result: '健康' }
  ]}
])

function refresh(){ /* 预留API，后续接后端 */ }

// 获取结果样式类 - 参考dialog-view的颜色方案
function getResultClass(result){
  if(result.includes('健康')) return 'healthy'
  if(result.includes('轻微认知障碍')) return 'mild'
  if(result.includes('老年痴呆')) return 'dementia'
  return ''
}

onMounted(()=>{
  updateTime()
  setInterval(updateTime, 15000)
})
</script>

<style>
/* 全局字体设置 - 参考dialog-view样式 */
.page {
  min-height: 100vh;
  background: linear-gradient(180deg,#f9f7f4,#ffffff);
  color: #4a4036;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  width: 100%;
  box-sizing: border-box;
}

/* 头部样式 - 与dialog-view保持一致 */
.header {
  padding: 24rpx;
  display:flex;
  align-items:center;
  justify-content:space-between;
  background: #ffffff;
  box-shadow: 0 2rpx 16rpx rgba(158, 142, 126, 0.1);
  width: 100%;
  box-sizing: border-box;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
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

/* 内容区域 - 与dialog-view保持一致 */
.content {
  height: calc(100vh - 120rpx);
  padding: 120rpx 20rpx 20rpx;
  width: 100%;
  box-sizing: border-box;
}

/* 工具栏 - 与dialog-view保持一致 */
.toolbar {
  margin: 16rpx 0 24rpx;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding: 16rpx 20rpx;
  background: #ffffff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 12rpx rgba(158, 142, 126, 0.05);
  width: 100%;
  box-sizing: border-box;
}

.toolbar-title {
  font-weight:700;
  font-size:28rpx;
  color:#4a4036;
}

.toolbar-subtitle {
  font-size:22rpx;
  color:#9e8e7e;
}

/* 网格布局 - 与dialog-view保持一致 */
.grid {
  display:flex;
  flex-direction:column;
  gap: 20rpx;
  width: 100%;
  box-sizing: border-box;
}

/* 卡片样式 - 与dialog-view保持一致 */
.card {
  background: rgba(255, 255, 255, 0.95);
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  border-radius: 24rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(158, 142, 126, 0.05);
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
}

.card:active {
  background: #ffffff;
  box-shadow: 0 6rpx 20rpx rgba(158, 142, 126, 0.1);
}

/* 患者主要信息 */
.patient-main {
  margin-bottom: 16rpx;
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
  width: 100%;
}

.patient-name {
  font-weight:800;
  font-size:32rpx;
  color:#4a4036;
  flex-shrink: 0;
}

.patient-age {
  font-size:24rpx;
  color:#9e8e7e;
  flex-shrink: 0;
}

.patient-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.assessment-time {
  font-size:22rpx;
  color:#9e8e7e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 12rpx;
}

/* 状态标签 - 参考dialog-view的assessment-result样式 */
.status-tag {
  padding: 4rpx 12rpx;
  border-radius: 16rpx;
  font-size:20rpx;
  font-weight:500;
  flex-shrink: 0;
}

.status-tag.healthy {
  background: #d4edda;
  color: #155724;
}

.status-tag.mild {
  background: #fff3cd;
  color: #856404;
}

.status-tag.dementia {
  background: #f8d7da;
  color: #721c24;
}

/* 评估历史 */
.assessment-history {
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 2rpx dashed rgba(158, 142, 126, 0.1);
}

.history-title {
  font-size:22rpx;
  color:#9e8e7e;
  margin-bottom: 12rpx;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8rpx 0;
  width: 100%;
  flex-wrap: wrap;
}

.history-time {
  font-size:20rpx;
  color:#4a4036;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12rpx;
  min-width: 0;
}

.history-score {
  font-size:18rpx;
  color:#6c757d;
  margin-right: 8rpx;
  flex-shrink: 0;
}

.history-result {
  font-size:18rpx;
  padding: 2rpx 10rpx;
  border-radius: 12rpx;
  font-weight:500;
  flex-shrink: 0;
}

.history-result.healthy {
  background: #d4edda;
  color: #155724;
}

.history-result.mild {
  background: #fff3cd;
  color: #856404;
}

.history-result.dementia {
  background: #f8d7da;
  color: #721c24;
}

/* 兼容不同设备的样式 - 移动端优化 */
@media (max-width: 768px) {
  .page {
    padding: 0;
  }
  
  .header {
    padding: 20rpx 16rpx;
  }
  
  .content {
    padding: 110rpx 12rpx 16rpx;
    height: calc(100vh - 110rpx);
  }
  
  .toolbar {
    padding: 14rpx 16rpx;
    margin: 12rpx 0 20rpx;
  }
  
  .card {
    padding: 16rpx;
    margin-bottom: 16rpx;
  }
  
  .patient-name {
    font-size:30rpx;
  }
  
  .patient-age {
    font-size:22rpx;
  }
  
  .assessment-time {
    font-size:20rpx;
    margin-right: 8rpx;
  }
  
  .status-tag {
    font-size:18rpx;
    padding: 3rpx 10rpx;
  }
  
  .history-title {
    font-size:20rpx;
  }
  
  .history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4rpx;
  }
  
  .history-time {
    width: 100%;
    font-size:18rpx;
    margin-right: 0;
  }
  
  .history-score {
    font-size:16rpx;
    margin-right: 0;
  }
  
  .history-result {
    font-size:16rpx;
    padding: 2rpx 8rpx;
  }
}

/* 手机端专用样式优化 - 确保在小屏幕上内容完整显示 */
@media (max-width: 480px) {
  .content {
    padding: 100rpx 10rpx 16rpx;
    height: calc(100vh - 100rpx);
  }
  
  .card {
    padding: 14rpx;
  }
  
  /* 保持水平布局与浏览器端一致 */
  .patient-header {
    flex-direction: row;
    align-items: center;
    gap: 0;
  }
  
  .patient-footer {
    flex-direction: row;
    align-items: center;
    gap: 0;
  }
  
  .assessment-time {
    width: auto;
    flex: 1;
  }
}
</style>
