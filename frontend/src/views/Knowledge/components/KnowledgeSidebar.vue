<script setup lang="ts">
/**
 * 知识库左侧导航（与 ChatSidebar 保持风格一致）
 *
 * - 顶部：渐变主按钮「新建文件夹」
 * - 中部：NTree 展示两个固定知识库 + 其下一层文件夹
 * - 每个文件夹节点右侧有删除按钮（NPopconfirm 二次确认）
 * - 知识库节点不可删除
 */
import { h, inject } from 'vue'
import {
  NButton,
  NIcon,
  NPopconfirm,
  NScrollbar,
  NTooltip,
  NTree,
} from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import { KNOWLEDGE_WORKSPACE_KEY } from '../composables/knowledgeWorkspace'

const injected = inject(KNOWLEDGE_WORKSPACE_KEY)
if (!injected) throw new Error('KnowledgeSidebar 必须在 Knowledge 工作区内使用')
const workspace = injected

/** 渲染一个小图标按钮（用于文件夹节点右侧的快捷操作） */
function renderFolderIconButton(options: {
  svgPath: string
  tooltip: string
  className: string
  onClick: (e: MouseEvent) => void
}) {
  return h(
    NTooltip,
    { placement: 'right' },
    {
      trigger: () =>
        h(
          NButton,
          {
            size: 'tiny',
            quaternary: true,
            class: options.className,
            onClick: (e: MouseEvent) => {
              e.stopPropagation()
              options.onClick(e)
            },
          },
          {
            icon: () =>
              h(NIcon, { size: 14 }, {
                default: () =>
                  h(
                    'svg',
                    {
                      xmlns: 'http://www.w3.org/2000/svg',
                      viewBox: '0 0 24 24',
                      fill: 'currentColor',
                    },
                    h('path', { d: options.svgPath }),
                  ),
              }),
          },
        ),
      default: () => options.tooltip,
    },
  )
}

/** 文件夹节点右侧操作：重命名 + 删除 */
function renderSuffix({ option }: { option: TreeOption }) {
  const key = String(option.key ?? '')
  if (!key.startsWith('folder:')) return undefined
  const folderId = key.slice(7)
  const folder = workspace.folders.find((f) => f.id === folderId)
  if (!folder) return undefined

  // 重命名按钮：直接打开弹窗
  const renameBtn = renderFolderIconButton({
    // Material Icons: edit（铅笔）
    svgPath:
      'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z',
    tooltip: '重命名',
    className: 'folder-action-btn folder-rename-btn',
    onClick: () => workspace.openRenameFolder(folder),
  })

  // 删除按钮：NPopconfirm 包裹
  const deleteBtn = h(
    NPopconfirm,
    {
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => workspace.deleteFolderNow(folder),
    },
    {
      trigger: () =>
        renderFolderIconButton({
          svgPath:
            'M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z',
          tooltip: '删除文件夹',
          className: 'folder-action-btn folder-del-btn',
          onClick: () => {
            // 点击不做额外处理，交给 NPopconfirm 弹出确认
          },
        }),
      default: () => `确定删除文件夹「${folder.name}」？其中的文件也会被删除。`,
    },
  )

  return h('span', { class: 'folder-actions' }, [renameBtn, deleteBtn])
}

/** 自定义节点前缀图标：库 & 文件夹 使用不同图标 */
function renderPrefix({ option }: { option: TreeOption }) {
  const key = String(option.key ?? '')
  const isLib = key.startsWith('lib:')
  const libId = isLib ? key.slice(4) : ''
  const svg = isLib
    ? libId === 'personal'
      ? 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'
      : 'M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z'
    : 'M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z'

  return h(
    'span',
    { class: ['tree-prefix', isLib ? 'tree-prefix--lib' : 'tree-prefix--folder'] },
    h(NIcon, { size: 14 }, {
      default: () =>
        h(
          'svg',
          { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' },
          h('path', { d: svg }),
        ),
    }),
  )
}
</script>

<template>
  <div class="knowledge-sidebar">
    <div class="sidebar-top">
      <NButton
        type="primary"
        block
        strong
        class="new-folder-btn"
        @click="workspace.openCreateFolderModal"
      >
        <template #icon>
          <NIcon>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
            </svg>
          </NIcon>
        </template>
        新建文件夹
      </NButton>
    </div>

    <NScrollbar class="sidebar-list">
      <NTree
        block-line
        :data="workspace.treeOptions"
        :selected-keys="workspace.selectedKeysForTree"
        default-expand-all
        :render-prefix="renderPrefix"
        :render-suffix="renderSuffix"
        class="knowledge-tree"
        @update:selected-keys="workspace.onTreeSelect"
      />
    </NScrollbar>

    <div class="sidebar-hint">
      个人 / 共享知识库为固定节点；文件夹仅一层，悬浮节点可删除。
    </div>
  </div>
</template>

<style scoped lang="less">
.knowledge-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid @border-color;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, @bg-white 0%, @bg-color 100%);
}

.sidebar-top {
  padding: 16px;
  flex-shrink: 0;
}

.new-folder-btn {
  height: 42px;
  border-radius: @border-radius-md;
  background: @gradient-primary !important;
  border: none !important;
  letter-spacing: 1px;
  transition: opacity 0.2s, transform 0.15s;

  &:hover {
    opacity: 0.9;
  }
  &:active {
    transform: scale(0.98);
  }
}

.sidebar-list {
  flex: 1;
  padding: 4px 10px;
}

.sidebar-hint {
  padding: 10px 16px 14px;
  font-size: 12px;
  color: @text-placeholder;
  line-height: 1.5;
  border-top: 1px solid @border-color;
}

/* 前缀小图标 */
:deep(.tree-prefix) {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: @border-radius-sm;
  margin-right: 2px;
  background: @bg-color;
  color: @text-placeholder;
  transition: background 0.2s, color 0.2s;
}

:deep(.tree-prefix--lib) {
  background: @primary-blue-light;
  color: @primary-blue;
}

/* NTree 节点美化：行高 / 圆角 / 悬浮 / 选中 */
:deep(.n-tree .n-tree-node) {
  border-radius: @border-radius-md;
  margin: 2px 0;
  padding: 2px 4px;
  transition: background 0.2s, box-shadow 0.2s;
}

:deep(.n-tree .n-tree-node:hover) {
  background: @bg-white;
  box-shadow: @shadow-sm;
  .folder-action-btn {
    opacity: 1;
  }
}

:deep(.n-tree .n-tree-node--selected) {
  background: @bg-white !important;
  box-shadow: 0 2px 12px rgba(33, 150, 243, 0.12);
}

:deep(.n-tree .n-tree-node--selected .n-tree-node-content__text) {
  color: @primary-blue;
  font-weight: 600;
}

:deep(.n-tree .n-tree-node--selected .tree-prefix) {
  background: @primary-blue-light;
  color: @primary-blue;
}

:deep(.n-tree-node-switcher) {
  height: 40px !important;
}

:deep(.n-tree-node-content) {
  padding: 6px 4px;
  min-height: 36px;
}

/* 文件夹行右侧操作区 */
:deep(.folder-actions) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

/* 操作按钮：默认半透明，节点悬浮时显现 */
:deep(.folder-action-btn) {
  opacity: 0;
  color: @text-placeholder;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
}

:deep(.folder-rename-btn:hover) {
  color: @primary-blue;
}

:deep(.folder-del-btn:hover) {
  color: #e53935;
}
</style>
