<template>
  <view class="page">
    <!-- 顶部品牌 -->
    <view class="header">
      <view class="brand">
        <view class="brand-badge">
          <text class="brand-star">★</text>
        </view>
        <text class="brand-text">关爱·守护</text>
      </view>
    </view>

    <scroll-view class="content" :scroll-y="true">
      <view class="register-card">
        <text class="card-title">用户注册</text>
        <text class="card-subtitle">请填写以下信息完成注册</text>
        
        <!-- 身份选择 -->
        <view class="roles">
          <view class="role" :class="{active: role==='child'}" @tap="role='child'">
            <text class="icon">👪</text>
            <text class="role-text">子女</text>
          </view>
          <view class="role" :class="{active: role==='doctor'}" @tap="role='doctor'">
            <text class="icon">🏥</text>
            <text class="role-text">机构/医生</text>
          </view>
        </view>

        <!-- 注册表单 -->
        <view class="form-group">
          <text class="label">用户名</text>
          <uni-easyinput class="input" type="text" v-model="form.username" placeholder="请输入用户名" />
        </view>

        <view class="form-group">
          <text class="label">账号</text>
          <uni-easyinput class="input" type="text" v-model="form.account" placeholder="请输入账号" />
        </view>

        <view class="form-group">
          <text class="label">密码</text>
          <uni-easyinput class="input" type="password" v-model="form.password" placeholder="请输入密码" />
        </view>

        <view class="form-group">
          <text class="label">确认密码</text>
          <uni-easyinput class="input" type="password" v-model="form.confirmPassword" placeholder="请再次输入密码" />
        </view>

        <view class="actions">
          <button class="btn primary full-width" @tap="onRegister">注册</button>
          <button class="btn ghost full-width" @tap="goToLoginPage">返回登录</button>
        </view>

        <text class="tips">注册即表示同意《隐私政策》与《用户协议》</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { authApi } from '@/services/api.js'

const role = ref('child')
const form = reactive({ username: '', account: '', password: '', confirmPassword: '' })

function onRegister(){
  // 简单验证
  if (!form.username || !form.account || !form.password || !form.confirmPassword) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  if (form.password !== form.confirmPassword) {
    uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
    return
  }
  
  // 调用后端注册接口
  uni.showLoading({ title: '注册中...' })
  authApi.register({
    username: form.username,
    account: form.account,
    password: form.password,
    role: role.value
  }).then(res => {
    uni.hideLoading()
    if (res.code === 200) {
      // 注册成功
      uni.showToast({ title: '注册成功', icon: 'success' })
      
      // 注册成功后跳转到登录页
      setTimeout(() => {
        uni.redirectTo({ url: '/pages/auth/login' })
      }, 1000)
    } else {
      // 注册失败
      uni.showToast({ title: res.message || '注册失败', icon: 'none' })
    }
  }).catch(err => {
    uni.hideLoading()
    console.error('注册失败:', err)
    uni.showToast({ title: '注册失败，请稍后重试', icon: 'none' })
  })
}

function goToLoginPage() {
  uni.redirectTo({ url: '/pages/auth/login' })
}
</script>

<style scoped>
/* 全局字体设置 */
.page {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f5f0eb, #e8e0d8);
  color: #4a4036;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 头部样式 */
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 120rpx;
  background-color: white;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.brand-badge {
  width: 52rpx;
  height: 52rpx;
  background: linear-gradient(135deg, #ff7e00, #ff5200);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 8rpx rgba(255, 126, 0, 0.3);
}

.brand-star {
  font-size: 28rpx;
  color: white;
}

.brand-text {
  font-size: 32rpx;
  font-weight: bold;
  color: #4a4036;
}

/* 内容区布局 */
.content {
  height: calc(100vh - 120rpx);
  padding-top: 120rpx;
  box-sizing: border-box;
}

.register-card {
  background-color: white;
  border-radius: 20rpx;
  padding: 28rpx;
  margin: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 16rpx;
  color: #4a4036;
}

.card-subtitle {
  font-size: 24rpx;
  text-align: center;
  margin-bottom: 32rpx;
  color: #8a7f75;
}

/* 身份选择 */
.roles {
  display: flex;
  gap: 20rpx;
  margin-bottom: 32rpx;
}

.role {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx;
  border-radius: 16rpx;
  background-color: #f5f0eb;
  transition: all 0.3s ease;
  cursor: pointer;
}

.role.active {
  background: linear-gradient(135deg, #ff7e00, #ff5200);
  transform: scale(1.03);
  box-shadow: 0 8rpx 16rpx rgba(255, 126, 0, 0.3);
}

.role.active .icon,
.role.active .role-text {
  color: white;
}

.icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
  color: #4a4036;
}

.role-text {
  font-size: 24rpx;
  color: #4a4036;
  font-weight: 500;
}

/* 表单元素样式 */
.form-group {
  margin-bottom: 24rpx;
}

.label {
  display: block;
  font-size: 24rpx;
  margin-bottom: 12rpx;
  color: #4a4036;
  font-weight: 500;
}

.input ::v-deep .uni-easyinput__content-input {
  font-size: 28rpx !important;
  padding: 20rpx !important;
}

.input ::v-deep .uni-easyinput__content {
  border-radius: 12rpx !important;
  border: 2rpx solid #e0d6cc !important;
}

/* 按钮样式 */
.actions {
  margin-top: 20rpx;
  margin-bottom: 24rpx;
}

.btn {
  padding: 20rpx 0;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  margin-bottom: 16rpx;
  transition: all 0.3s ease;
}

.btn.primary {
  background: linear-gradient(135deg, #ff7e00, #ff5200);
  color: white;
  border: none;
}

.btn.primary:active {
  transform: scale(0.98);
  box-shadow: 0 4rpx 12rpx rgba(255, 126, 0, 0.4);
}

.btn.ghost {
  background: transparent;
  color: #8a7f75;
  border: 2rpx solid #d0c6bc;
}

.btn.ghost:active {
  background-color: #f5f0eb;
}

.full-width {
  width: 100%;
}

/* 提示文本 */
.tips {
  font-size: 20rpx;
  text-align: center;
  color: #8a7f75;
  margin-top: 16rpx;
}

/* 响应式布局适配 */
@media screen and (max-width: 768px) {
  .header {
    height: 100rpx;
  }
  
  .brand-badge {
    width: 48rpx;
    height: 48rpx;
  }
  
  .brand-star {
    font-size: 24rpx;
  }
  
  .brand-text {
    font-size: 28rpx;
  }
  
  .content {
    height: calc(100vh - 100rpx);
    padding-top: 100rpx;
  }
  
  .register-card {
    padding: 24rpx;
    margin: 16rpx;
  }
  
  .card-title {
    font-size: 32rpx;
    margin-bottom: 12rpx;
  }
  
  .card-subtitle {
    font-size: 22rpx;
    margin-bottom: 28rpx;
  }
  
  .roles {
    margin-bottom: 28rpx;
  }
  
  .role {
    padding: 20rpx;
  }
  
  .icon {
    font-size: 44rpx;
  }
  
  .role-text {
    font-size: 22rpx;
  }
  
  .form-group {
    margin-bottom: 20rpx;
  }
  
  .label {
    font-size: 22rpx;
    margin-bottom: 10rpx;
  }
  
  .input ::v-deep .uni-easyinput__content-input {
    font-size: 26rpx !important;
    padding: 18rpx !important;
  }
  
  .btn {
    padding: 18rpx 0;
    font-size: 26rpx;
  }
  
  .tips {
    font-size: 18rpx;
    margin-top: 12rpx;
  }
}

@media screen and (max-width: 480px) {
  .header {
    height: 90rpx;
  }
  
  .brand-badge {
    width: 44rpx;
    height: 44rpx;
  }
  
  .brand-star {
    font-size: 22rpx;
  }
  
  .brand-text {
    font-size: 26rpx;
  }
  
  .content {
    height: calc(100vh - 90rpx);
    padding-top: 90rpx;
  }
  
  .register-card {
    padding: 20rpx;
    margin: 12rpx;
  }
  
  .card-title {
    font-size: 28rpx;
    margin-bottom: 10rpx;
  }
  
  .card-subtitle {
    font-size: 20rpx;
    margin-bottom: 24rpx;
  }
  
  .roles {
    margin-bottom: 24rpx;
  }
  
  .role {
    padding: 16rpx;
  }
  
  .icon {
    font-size: 40rpx;
  }
  
  .role-text {
    font-size: 20rpx;
  }
  
  .form-group {
    margin-bottom: 16rpx;
  }
  
  .label {
    font-size: 20rpx;
    margin-bottom: 8rpx;
  }
  
  .input ::v-deep .uni-easyinput__content-input {
    font-size: 24rpx !important;
    padding: 16rpx !important;
  }
  
  .btn {
    padding: 16rpx 0;
    font-size: 24rpx;
  }
  
  .tips {
    font-size: 16rpx;
    margin-top: 10rpx;
  }
}
</style>