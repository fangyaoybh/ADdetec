# 项目目录结构说明

## 目录结构

```
src/
├── assets/           # 静态资源目录
│   └── images/       # 图片资源
├── components/       # 公共组件目录
│   └── AccountManager.vue  # 账户管理组件
├── pages/            # 页面组件目录
│   ├── auth/         # 认证相关页面
│   │   ├── login.vue     # 登录页面
│   │   └── register.vue  # 注册页面
│   ├── dialog/       # 对话相关页面
│   │   └── dialog-view.vue  # 对话视图页面
│   ├── doctor/       # 医生/机构页面
│   │   └── index.vue      # 医生列表页面
│   └── index/        # 首页
│       └── index.vue      # 首页入口
├── services/         # 服务层目录
│   └── api.js        # API服务
├── utils/            # 工具类目录
│   ├── api-config.js       # API配置
│   ├── helpers.js          # 通用工具函数
│   ├── router-config.js    # 路由配置
│   ├── styles.js           # 样式配置
│   └── store.js            # 状态管理
├── App.vue           # 根组件
├── main.js           # 入口文件
├── manifest.json     # 应用配置
├── pages.json        # 页面配置
└── uni.scss          # 全局样式
```

## 目录说明

### 1. assets/
存放项目的静态资源，包括图片、字体、音频等。

### 2. components/
存放公共组件，这些组件可以在多个页面中复用。

### 3. pages/
存放页面组件，每个页面组件对应一个路由。

#### 3.1 auth/
认证相关页面，包括登录和注册功能。

#### 3.2 dialog/
对话相关页面，包括对话视图和对话详情。

#### 3.3 doctor/
医生/机构相关页面，包括医生列表和机构信息。

#### 3.4 index/
首页，应用的入口页面。

### 4. services/
服务层，封装了与后端API的交互逻辑，提供统一的服务接口。

### 5. utils/
工具类目录，包含各种通用工具函数和配置。

#### 5.1 api-config.js
API配置文件，定义了API的基础地址、路径和请求配置。

#### 5.2 helpers.js
通用工具函数，包括日期格式化、本地存储、防抖节流等。

#### 5.3 router-config.js
路由配置文件，定义了页面的路由信息和导航方法。

#### 5.4 styles.js
样式配置文件，定义了全局的样式变量和主题。

#### 5.5 store.js
状态管理文件，用于管理应用的全局状态。

## 文件命名规范

### 组件文件
- 使用PascalCase命名，如 `AccountManager.vue`

### 页面文件
- 使用kebab-case命名，如 `dialog-view.vue`

### 工具类文件
- 使用camelCase命名，如 `apiConfig.js`

### 目录命名
- 使用kebab-case命名，如 `dialog-view`
- 功能模块目录使用语义化命名，如 `auth`, `dialog`, `doctor`

## 代码规范

- 遵循Vue 3 Composition API规范
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化
- 组件化开发，提高代码复用性
- 注释清晰，说明功能和用途

## 开发流程

1. 创建新页面时，在pages目录下创建对应的目录和文件
2. 在pages.json中配置页面路由
3. 公共组件放在components目录下
4. API调用封装在services目录下
5. 通用工具函数放在utils目录下

## 注意事项

- 确保所有文件引用路径正确
- 遵循命名规范，保持代码一致性
- 定期清理无用文件和代码
- 确保代码的可读性和可维护性
