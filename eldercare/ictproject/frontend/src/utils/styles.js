// 统一样式配置 - 提供主题色、间距、字体大小等样式常量

/**
 * 主题色彩配置 - 温暖舒适的配色方案，体现人文关怀理念
 */
export const COLORS = {
  // 主色调 - 温暖的橙色，代表关怀和温暖
  PRIMARY: '#f89b6b',
  PRIMARY_GRADIENT: 'linear-gradient(135deg, #f89b6b, #fcb677)',
  PRIMARY_LIGHT: '#fcb677',
  
  // 辅助色 - 柔和的绿色，代表健康和希望
  SECONDARY: '#7ecb9d',
  SECONDARY_GRADIENT: 'linear-gradient(135deg, #7ecb9d, #9ed7b3)',
  
  // 背景色 - 温暖的浅色调
  BACKGROUND: '#f9f7f4',
  BACKGROUND_GRADIENT: 'linear-gradient(180deg, #ffffff, #f9f7f4)',
  CARD_BACKGROUND: 'rgba(255, 255, 255, 0.95)',
  MODAL_BACKGROUND: 'rgba(240, 238, 234, 0.95)',
  
  // 文字颜色 - 深暖色调
  TEXT_PRIMARY: '#4a4036',
  TEXT_SECONDARY: '#7d7162',
  TEXT_TERTIARY: '#9e8e7e',
  TEXT_HIGHLIGHT: '#c86738',
  TEXT_INVERSE: '#ffffff',
  
  // 边框颜色 - 柔和的暖灰色
  BORDER: 'rgba(158, 142, 126, 0.2)',
  BORDER_ACTIVE: 'rgba(248, 155, 107, 0.3)',
  
  // 状态颜色
  SUCCESS: '#6bb588',
  SUCCESS_BG: 'rgba(107, 181, 136, 0.15)',
  WARNING: '#e6a967',
  WARNING_BG: 'rgba(230, 169, 103, 0.15)',
  DANGER: '#e97865',
  DANGER_BG: 'rgba(233, 120, 101, 0.15)',
  INFO: '#6db0d9',
  INFO_BG: 'rgba(109, 176, 217, 0.15)',
  
  // 透明度
  OPACITY_LOW: 'rgba(74, 64, 54, 0.05)',
  OPACITY_MEDIUM: 'rgba(74, 64, 54, 0.1)',
  OPACITY_HIGH: 'rgba(74, 64, 54, 0.15)',
}

/**
 * 间距配置
 */
export const SPACING = {
  XS: 10,
  SM: 16,
  MD: 24,
  LG: 32,
  XL: 40,
  XXL: 50,
}

/**
 * 字体大小配置
 */
export const FONT_SIZE = {
  XS: 20,
  SM: 22,
  BASE: 24,
  MD: 26,
  LG: 28,
  XL: 30,
  XXL: 40,
  XXXL: 48,
}

/**
 * 圆角配置
 */
export const BORDER_RADIUS = {
  SM: 10,
  MD: 16,
  LG: 18,
  XL: 20,
  XXL: 24,
  FULL: 999,
}

/**
 * 阴影配置
 */
export const SHADOW = {
  SM: '0 8rpx 24rpx rgba(0, 0, 0, .35)',
  MD: '0 12rpx 36rpx rgba(0, 0, 0, .25)',
  LG: '0 16rpx 40rpx rgba(0, 0, 0, .35)',
}

/**
 * 通用样式类
 */
export const COMMON_CLASSES = {
  // 容器样式
  CONTAINER: {
    width: '100%',
    boxSizing: 'border-box',
  },
  
  // 卡片样式
  CARD: {
    backgroundColor: COLORS.CARD_BACKGROUND,
    border: `2rpx solid ${COLORS.BORDER}`,
    borderRadius: `${BORDER_RADIUS.XL}rpx`,
    padding: `${SPACING.SM}rpx`,
  },
  
  // 按钮样式
  BUTTON_PRIMARY: {
    backgroundColor: COLORS.PRIMARY,
    backgroundImage: COLORS.PRIMARY_GRADIENT,
    color: COLORS.TEXT_INVERSE,
    borderRadius: `${BORDER_RADIUS.LG}rpx`,
    padding: `${SPACING.XS}rpx ${SPACING.SM}rpx`,
    fontWeight: '800',
    fontSize: `${FONT_SIZE.BASE}rpx`,
  },
  
  BUTTON_GHOST: {
    backgroundColor: 'transparent',
    border: `2rpx solid ${COLORS.BORDER}`,
    color: COLORS.TEXT_PRIMARY,
    borderRadius: `${BORDER_RADIUS.LG}rpx`,
    padding: `${SPACING.XS}rpx ${SPACING.SM}rpx`,
    fontWeight: '800',
    fontSize: `${FONT_SIZE.BASE}rpx`,
  },
  
  // 输入框样式
  INPUT: {
    width: '100%',
    backgroundColor: COLORS.OPACITY_MEDIUM,
    border: `2rpx solid ${COLORS.BORDER}`,
    borderRadius: `${BORDER_RADIUS.MD}rpx`,
    padding: `${SPACING.SM}rpx ${SPACING.SM}rpx`,
    color: COLORS.TEXT_PRIMARY,
    boxSizing: 'border-box',
  },
  
  // 标签样式
  TAG_SUCCESS: {
    backgroundColor: COLORS.SUCCESS_BG,
    color: COLORS.SUCCESS,
    padding: `6rpx 10rpx`,
    borderRadius: `${BORDER_RADIUS.FULL}rpx`,
    fontSize: `${FONT_SIZE.XS}rpx`,
  },
  
  TAG_WARNING: {
    backgroundColor: COLORS.WARNING_BG,
    color: COLORS.WARNING,
    padding: `6rpx 10rpx`,
    borderRadius: `${BORDER_RADIUS.FULL}rpx`,
    fontSize: `${FONT_SIZE.XS}rpx`,
  },
  
  TAG_DANGER: {
    backgroundColor: COLORS.DANGER_BG,
    color: COLORS.DANGER,
    padding: `6rpx 10rpx`,
    borderRadius: `${BORDER_RADIUS.FULL}rpx`,
    fontSize: `${FONT_SIZE.XS}rpx`,
  },
}

/**
 * 导出样式配置对象
 */
const STYLES_CONFIG = {
  COLORS,
  SPACING,
  FONT_SIZE,
  BORDER_RADIUS,
  SHADOW,
  COMMON_CLASSES,
}

export default STYLES_CONFIG