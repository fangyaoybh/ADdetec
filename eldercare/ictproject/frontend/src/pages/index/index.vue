<template>
  <view class="page">
    <!-- 主页重定向到dialog-view页面 -->
    <!-- 根据状态显示不同内容 -->
    <view class="loading-container" v-if="redirecting">
      <view class="loading-spinner"></view>
      <text class="loading-text">正在加载系统...</text>
    </view>
    
    <!-- 错误状态显示 -->
    <view class="error-container" v-else-if="redirectError">
      <view class="error-icon">⚠️</view>
      <text class="error-title">加载失败</text>
      <text class="error-message">{{ errorMessage }}</text>
      <button class="retry-button" @click="retryRedirect">重试加载</button>
      <button class="direct-button" @click="() => uni.switchTab({url: '/pages/index/index'})")>返回首页</button>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const redirecting = ref(true)
const redirectError = ref(false)
const errorMessage = ref('')

// 重试重定向函数
function retryRedirect() {
  redirecting.value = true
  redirectError.value = false
  redirectToLoginPage()
}

// 重定向到dialog-view页面的核心函数
function redirectToLoginPage() {
  // 设置5秒超时，防止导航API阻塞
  const timeout = setTimeout(() => {
    redirecting.value = false
    redirectError.value = true
    errorMessage.value = '页面跳转超时，请重试'
    console.error('页面重定向超时')
  }, 5000)
  
  // 使用uni-app的导航API进行重定向到登录页面
  uni.redirectTo({
    url: '/pages/auth/login',
    success: () => {
      clearTimeout(timeout)
      redirecting.value = false
      console.log('重定向到登录页面成功')
    },
    fail: (error) => {
      clearTimeout(timeout)
      redirecting.value = false
      redirectError.value = true
      errorMessage.value = error.errMsg || '跳转失败，请重试'
      console.error('重定向失败:', error)
    }
  })
}

// 页面加载时尝试重定向到登录页面
onMounted(() => {
  redirectToLoginPage()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg,#0f1522,#0a0e1a);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.loading-spinner {
  width: 80rpx;
  height: 80rpx;
  border: 6rpx solid rgba(77, 208, 255, 0.3);
  border-top-color: #4dd0ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 24rpx;
}

.loading-text {
  color: #4dd0ff;
  font-size: 28rpx;
}

/* 错误状态样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  text-align: center;
  max-width: 600rpx;
}

.error-icon {
  font-size: 100rpx;
  margin-bottom: 24rpx;
}

.error-title {
  color: #ff6b6b;
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.error-message {
  color: #e0e0e0;
  font-size: 28rpx;
  margin-bottom: 40rpx;
  line-height: 1.5;
}

.retry-button, .direct-button {
  width: 280rpx;
  margin-bottom: 20rpx;
  border-radius: 8rpx;
}

.retry-button {
  background-color: #4dd0ff;
  color: #0f1522;
  font-weight: bold;
}

.direct-button {
  background-color: transparent;
  border: 2rpx solid #4dd0ff;
  color: #4dd0ff;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>