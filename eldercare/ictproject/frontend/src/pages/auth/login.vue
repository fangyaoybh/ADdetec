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
      <view class="login-card">
        <text class="card-title">用户登录</text>
        <text class="card-subtitle">请选择您的身份并登录</text>
        
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

        <!-- 账号密码 -->
        <view class="form-group">
          <text class="label">账号</text>
          <uni-easyinput class="input" type="text" v-model="form.account" placeholder="请输入账号" />
        </view>

        <view class="form-group">
          <text class="label">密码</text>
          <uni-easyinput class="input" type="password" v-model="form.password" placeholder="请输入密码" />
        </view>

        <view class="actions">
          <button class="btn primary full-width" @tap="onLogin">登录</button>
        </view>
        <view class="register-link" @tap="goToRegisterPage">
          <text>还没有账号？立即注册</text>
        </view>

        <text class="tips">登录即表示同意《隐私政策》与《用户协议》</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { authApi } from '@/services/api.js'

const role = ref('child')
const form = reactive({ account: '', password: '' })

function onLogin(){
  // 简单验证
  if (!form.account || !form.password) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }
  
  // 调用后端登录接口
  uni.showLoading({ title: '登录中...' })
  authApi.login({
    account: form.account,
    password: form.password,
    role: role.value
  }).then(res => {
    uni.hideLoading()
    if (res.code === 200) {
      // 登录成功
      uni.showToast({ title: '登录成功', icon: 'success' })
      
      // 保存token和用户信息到本地存储
      uni.setStorageSync('token', res.data.token)
      uni.setStorageSync('user', res.data.user)
      uni.setStorageSync('role', role.value)
      
      // 登录成功后根据角色跳转到对应界面
      setTimeout(() => {
        if(role.value === 'child'){
            uni.reLaunch({ url: '/pages/dialog/dialog-view' })
          } else {
            uni.reLaunch({ url: '/pages/doctor/index' })
          }
      }, 1000)
    } else {
      // 登录失败
      uni.showToast({ title: res.message || '登录失败', icon: 'none' })
    }
  }).catch(err => {
    uni.hideLoading()
    console.error('登录失败:', err)
    uni.showToast({ title: '登录失败，请稍后重试', icon: 'none' })
  })
}

function goToRegisterPage() {
  uni.navigateTo({ url: '/pages/auth/register' })
}
</script>

<style>
/* 全局字体设置 - 与dialog-view保持一致 */
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
  width: 100%;
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

/* 内容区域 - 与dialog-view保持一致 */
.content {
  height: calc(100vh - 120rpx);
  padding: 120rpx 20rpx 20rpx;
  width: 100%;
  box-sizing: border-box;
}

.login-card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 12rpx rgba(158, 142, 126, 0.05);
  max-width: 1000rpx;
  margin: 0 auto;
  box-sizing: border-box;
}

.card-title {
  font-weight: 700;
  font-size: 32rpx;
  color: #4a4036;
  display: block;
  margin-bottom: 8rpx;
}

.card-subtitle {
  color: #9e8e7e;
  font-size: 24rpx;
  display: block;
  margin-bottom: 24rpx;
}

.label {
  display: block;
  margin-top: 20rpx;
  margin-bottom: 12rpx;
  color: #4a4036;
  font-size: 24rpx;
  font-weight: 500;
}

.form-group {
  margin-bottom: 24rpx;
}

.roles {
  display: flex;
  gap: 16rpx;
  margin: 24rpx 0 32rpx;
}

.role {
  flex: 1;
  padding: 20rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, .04);
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  display: flex;
  align-items: center;
  gap: 10rpx;
  justify-content: center;
  box-sizing: border-box;
  min-width: 0;
  transition: all 0.3s ease;
}

.role.active {
  background: linear-gradient(135deg, #f89b6b, #fcb677);
  color: #ffffff;
  border-color: transparent;
  transform: translateY(-2rpx);
  box-shadow: 0 4rpx 12rpx rgba(248, 155, 107, 0.2);
}

.role:active {
  transform: translateY(0);
}

.icon {
  font-size: 34rpx;
}

.role-text {
  font-weight: 500;
  font-size: 24rpx;
}

.input {
  width: 100%;
  background: #f9f7f4;
  border: 2rpx solid rgba(158, 142, 126, 0.1);
  border-radius: 12rpx;
  padding: 20rpx 16rpx;
  color: #4a4036;
  box-sizing: border-box;
  font-size: 28rpx;
}

.input::placeholder {
  color: #9e8e7e;
  font-size: 24rpx;
}

.actions {
  display: flex;
  justify-content: center;
  margin: 32rpx 0 24rpx;
}

.btn {
  border-radius: 12rpx;
  padding: 20rpx 0;
  font-weight: 500;
  font-size: 28rpx;
  transition: all 0.3s ease;
}

.btn:active {
  transform: scale(0.98);
}

.btn.full-width {
  width: 100%;
}

.primary {
  color: #ffffff;
  background: linear-gradient(135deg, #f89b6b, #fcb677);
  box-shadow: 0 4rpx 16rpx rgba(248, 155, 107, 0.25);
}

.register-link {
  text-align: center;
  margin: 24rpx 0;
  color: #f89b6b;
  font-size: 26rpx;
  font-weight: 500;
  padding: 16rpx;
  border-radius: 12rpx;
  transition: background-color 0.3s ease;
}

.register-link:active {
  background-color: rgba(248, 155, 107, 0.1);
}

.tips {
  display: block;
  text-align: center;
  margin-top: 24rpx;
  color: #9e8e7e;
  font-size: 22rpx;
  line-height: 1.6;
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
    padding: 100rpx 16rpx 16rpx;
  }
  
  .login-card {
    padding: 24rpx;
    margin: 0 auto;
  }
  
  .card-title {
    font-size: 32rpx;
    margin-bottom: 12rpx;
  }
  
  .card-subtitle {
    font-size: 22rpx;
    margin-bottom: 28rpx;
  }
  
  .label {
    font-size: 22rpx;
    margin-top: 16rpx;
    margin-bottom: 10rpx;
  }
  
  .form-group {
    margin-bottom: 20rpx;
  }
  
  .roles {
    margin: 20rpx 0 28rpx;
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
  
  .input {
    font-size: 26rpx;
    padding: 18rpx;
  }
  
  .input::placeholder {
    font-size: 22rpx;
  }
  
  .btn {
    padding: 18rpx 0;
    font-size: 26rpx;
  }
  
  .register-link {
    font-size: 24rpx;
    margin: 20rpx 0;
    padding: 12rpx;
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
    padding: 90rpx 12rpx 12rpx;
  }
  
  .login-card {
    padding: 20rpx;
    margin: 0 auto;
  }
  
  .card-title {
    font-size: 28rpx;
    margin-bottom: 10rpx;
  }
  
  .card-subtitle {
    font-size: 20rpx;
    margin-bottom: 24rpx;
  }
  
  .label {
    font-size: 20rpx;
    margin-top: 12rpx;
    margin-bottom: 8rpx;
  }
  
  .form-group {
    margin-bottom: 16rpx;
  }
  
  .roles {
    margin: 16rpx 0 24rpx;
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
  
  .input {
    font-size: 24rpx;
    padding: 16rpx;
  }
  
  .input::placeholder {
    font-size: 20rpx;
  }
  
  .btn {
    padding: 16rpx 0;
    font-size: 24rpx;
  }
  
  .register-link {
    font-size: 22rpx;
    margin: 16rpx 0;
    padding: 10rpx;
  }
  
  .tips {
    font-size: 16rpx;
    margin-top: 10rpx;
  }
}
</style>


