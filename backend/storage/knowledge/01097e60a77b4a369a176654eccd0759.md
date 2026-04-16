# 前端代码结构说明

本文档描述 `frontend` 目录下的技术栈、目录职责与路由组织，便于新成员快速上手。

## 技术栈与构建

| 类别 | 选型 |
|------|------|
| 框架 | Vue 3 |
| 语言 | TypeScript |
| 构建 | Vite 8 |
| 路由 | Vue Router 4（`createWebHistory`） |
| 状态 | Pinia |
| UI | Naive UI（全局主题、中文 locale、`NMessageProvider`） |
| HTTP | Axios |
| 样式 | Less（全局样式 + 变量；Vite 中 Less 自动注入变量文件） |
| 其他依赖 | docx、mammoth、xlsx（文档/表格相关能力） |

## 工程配置要点

- **路径别名**：`@` → `src`（见 `vite.config.ts`）。
- **Less**：通过 `additionalData` 全局注入 `@/styles/variables.less`。
- **开发代理**：`/api` 代理到 `http://localhost:8000`，并重写去掉 `/api` 前缀。

## 源码目录（`src/`）

| 路径 | 职责 |
|------|------|
| `main.ts` | 应用入口：创建应用、注册 Pinia 与 Router、引入全局样式 |
| `App.vue` | 根组件：`NConfigProvider` / `NMessageProvider`、`<router-view />` |
| `router/index.ts` | 路由定义；`beforeEach` 设置标题、基于 `localStorage.token` 的登录拦截与公开页重定向 |
| `stores/` | Pinia：`index.ts` 创建实例；`user.ts` 等业务状态 |
| `api/` | 按领域划分的接口层：`core.ts`（通用类型等）、`users.ts`、`chat.ts`、`knowledge.ts` |
| `utils/` | 工具：`request.ts`（Axios 封装）；知识库预览相关 `knowledgePreview*.ts` |
| `styles/` | `global.less`、`variables.less` |
| `views/` | 页面视图；复杂页面在同目录下使用 `components/` 子目录拆分 |
| `env.d.ts` | 环境/模块类型声明 |

## 路由与页面

### 公开路由（无需登录）

| 路径 | 名称 | 页面 |
|------|------|------|
| `/login` | Login | `views/Login/Login.vue` |
| `/register` | Register | `views/Register/Register.vue` |

### 主布局（需登录）

根路径 `/` 对应 `views/Home/Home.vue`，默认重定向到 `/dashboard`，子路由如下：

| 路径 | 名称 | 页面 | 说明 |
|------|------|------|------|
| `/dashboard` | Dashboard | `views/Dashboard/Dashboard.vue` | 工作台 |
| `/knowledge` | Knowledge | `views/Knowledge/Knowledge.vue` | 知识库 |
| `/chat` | Chat | `views/Chat/Chat.vue` | AI 对话 |

路由元信息：

- `meta.title`：用于设置 `document.title`（后缀为「运行智脑」）。
- `meta.public`：为 `true` 时跳过登录校验。

## 主要页面子组件（当前仓库）

### 知识库 `views/Knowledge/`

- `components/KnowledgeFolderSidebar.vue`：文件夹侧栏
- `components/KnowledgeFilePanel.vue`：文件列表/操作区
- `components/KnowledgePageHeader.vue`：页头
- `components/KnowledgeUploadModal.vue`：上传弹窗
- `components/KnowledgePreviewModal.vue`：预览弹窗
- `types.ts`：页面相关类型

### 对话 `views/Chat/`

- `components/ChatSidebar.vue`：会话侧栏
- `components/ChatHeader.vue`：顶栏
- `components/ChatMessageRow.vue`：单条消息
- `components/ChatInputBar.vue`：输入区
- `components/ChatEmptyState.vue`：空状态
- `components/ChatSuggestedPrompts.vue`：建议提示

## 代码组织习惯

1. **按路由/功能分 `views/**`**，页面专用组件放在同目录 `components/`，避免全局组件目录过度膨胀。
2. **接口集中在 `api/`**，与 `utils/request.ts` 配合统一请求行为。
3. **跨页面状态放在 `stores/`**；鉴权与标题在路由守卫中处理。

## 常用脚本

```bash
npm run dev      # 开发（Vite，默认端口见 vite.config）
npm run build    # vue-tsc 检查 + 生产构建
npm run preview  # 预览构建产物
```

---

*文档随仓库演进可手动更新；若目录与文件有增减，请以实际代码为准。*
