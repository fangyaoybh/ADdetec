<template>
  <view class="account-manager">
    <view class="account-actions">
      <button class="btn danger" @tap="logout">退出登录</button>
    </view>
    
    <!-- 退出确认弹窗 -->
    <view class="modal" v-if="showLogoutConfirm">
      <view class="modal-content">
        <text class="modal-title">确认退出</text>
        <text class="modal-desc">您确定要退出当前账号吗？</text>
        <view class="modal-actions">
          <button class="btn ghost" @tap="cancelLogout">取消</button>
          <button class="btn danger" @tap="confirmLogout">确认退出</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import appStore from '../utils/store.js'
import ROUTER_CONFIG from '../utils/router-config.js'

const showLogoutConfirm = ref(false)

// 退出登录 - 显示确认弹窗
function logout() {
  showLogoutConfirm.value = true
}

// 取消退出
function cancelLogout() {
  showLogoutConfirm.value = false
}

// 确认退出
function confirmLogout() {
  showLogoutConfirm.value = false
  
  // 执行退出操作
  appStore.actions.logout()
  
  // 跳转到登录页面
  ROUTER_CONFIG.redirectTo(ROUTER_CONFIG.PAGES.LOGIN)
  
  // 显示退出成功提示
  uni.showToast({
    title: '已退出登录',
    icon: 'success'
  })
}
</script>

<style>
.account-manager {
  position: fixed;
  bottom: 40rpx;
  right: 40rpx;
  z-index: 999;
}

.account-actions {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.btn {
  border-radius: 18rpx;
  padding: 16rpx 24rpx;
  font-weight: 800;
  font-size: 28rpx;
  border: none;
  outline: none;
}

.btn.secondary {
  background: rgba(255,255,255,.08);
  border: 2rpx solid rgba(255,255,255,.18);
  color: #cfe1ff;
}

.btn.danger {
  background: linear-gradient(135deg,#ff6b6b,#ff8e8e);
  color: white;
}

.btn.ghost {
  background: rgba(255,255,255,.08);
  border: 2rpx solid rgba(255,255,255,.18);
  color: #cfe1ff;
}

/* 弹窗样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 24rpx;
  padding: 40rpx;
  width: 80%;
  max-width: 500rpx;
  box-sizing: border-box;
}

.modal-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 20rpx;
  color: #333;
}

.modal-desc {
  display: block;
  font-size: 28rpx;
  text-align: center;
  margin-bottom: 40rpx;
  color: #666;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.modal-actions .btn {
  flex: 1;
}
</style>