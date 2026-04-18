<script setup lang="ts">
/**
 * 知识库右侧文件面板（与 Chat 右侧风格保持一致）
 *
 * - 顶部：面包屑 / 标题 + 搜索 + 上传按钮（渐变主按钮）
 * - 主体：NDataTable 展示文件；NEmpty 空态；NSpin loading
 * - 底部：NPagination 分页
 */
import { h, inject } from 'vue'
import {
  NButton,
  NDataTable,
  NIcon,
  NInput,
  NPagination,
  NPopconfirm,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { KnowledgeFile } from '@/types/knowledge'
import { KNOWLEDGE_WORKSPACE_KEY } from '../composables/knowledgeWorkspace'

const injected = inject(KNOWLEDGE_WORKSPACE_KEY)
if (!injected) throw new Error('KnowledgeFilePanel 必须在 Knowledge 工作区内使用')
const workspace = injected

/**
 * 按文件扩展名返回视觉元数据（标签颜色 / 图标路径 / 图标主色）
 * 用一个彩色的小图标 + 彩色 pill，整体风格与产品渐变主色互补。
 */
interface FileMeta {
  /** 类型列的文字，如 PDF / Excel */
  label: string
  /** 类型 pill 的背景色（浅） */
  pillBg: string
  /** 类型 pill 的文字色 */
  pillColor: string
  /** 文件名前的小图标颜色 */
  iconColor: string
  /** 图标 SVG path */
  iconPath: string
}

const FILE_ICON_DOC =
  'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 7V3.5L18.5 9H13z'
const FILE_ICON_IMG =
  'M21 19V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z'
const FILE_ICON_SHEET =
  'M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-9 14H5v-4h5v4zm0-6H5V7h5v4zm4 6h-3v-4h3v4zm5 0h-4v-4h4v4zm0-6h-4V7h4v4z'
const FILE_ICON_PDF =
  'M7 2h10a2 2 0 012 2v16a2 2 0 01-2 2H7a2 2 0 01-2-2V4a2 2 0 012-2zm5 14l-4-4h3V8h2v4h3l-4 4z'
// Markdown 官方 logo 的"M + 向下箭头"剪影，比之前的图标更能一眼识别为 MD
const FILE_ICON_MD =
  'M3 7h2l2 2.5 2-2.5h2v10h-2v-6l-2 2-2-2v6H3V7zM15 7h2v5h2l-3 4.5-3-4.5h2V7z'

function fileMetaOf(file: KnowledgeFile): FileMeta {
  // 小写扩展名，含点号，去掉点号
  const ext = file.file_ext.replace('.', '')
  
  // 图片
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) {
    return {
      label: '图片',
      pillBg: '#f3e8ff',
      pillColor: '#7c3aed',
      iconColor: '#8b5cf6',
      iconPath: FILE_ICON_IMG,
    }
  }
  // PDF
  if (ext === 'pdf') {
    return {
      label: 'PDF',
      pillBg: '#fee2e2',
      pillColor: '#dc2626',
      iconColor: '#ef4444',
      iconPath: FILE_ICON_PDF,
    }
  }
  // Excel / CSV
  if (['xls', 'xlsx', 'csv'].includes(ext)) {
    return {
      label: 'Excel',
      pillBg: '#dcfce7',
      pillColor: '#15803d',
      iconColor: '#10b981',
      iconPath: FILE_ICON_SHEET,
    }
  }
  // Markdown
  if (['md', 'markdown'].includes(ext)) {
    return {
      label: 'Markdown',
      pillBg: '#ffedd5',
      pillColor: '#c2410c',
      iconColor: '#f97316',
      iconPath: FILE_ICON_MD,
    }
  }
  // TXT
  if (ext === 'txt') {
    return {
      label: 'TXT',
      pillBg: '#f1f5f9',
      pillColor: '#475569',
      iconColor: '#64748b',
      iconPath: FILE_ICON_DOC,
    }
  }
  // Word
  if (['doc', 'docx'].includes(ext)) {
    return {
      label: 'Word',
      pillBg: '#dbeafe',
      pillColor: '#1d4ed8',
      iconColor: '#3b82f6',
      iconPath: FILE_ICON_DOC,
    }
  }
  // 其它
  return {
    label: ext ? ext.toUpperCase() : '未知',
    pillBg: '#f1f5f9',
    pillColor: '#475569',
    iconColor: '#94a3b8',
    iconPath: FILE_ICON_DOC,
  }
}

/** 根据 updatedAt 衍生状态：最近 6 秒内的文件显示“处理中”，否则“就绪” */
function statusOf(file: KnowledgeFile): { label: string; tone: 'pending' | 'processing' | 'success' | 'failed' | 'unknown' } {
// 根据 parse_status 衍生状态
if (file.parse_status === 'pending') return { label: '待处理', tone: 'pending' }
if (file.parse_status === 'processing') return { label: '处理中', tone: 'processing' }
if (file.parse_status === 'success') return { label: '就绪', tone: 'success' }
if (file.parse_status === 'failed') return { label: '失败', tone: 'failed' }
return { label: '未知', tone: 'unknown' }
}

/** 将日期格式化为 YYYY-MM-DD HH:mm（与图中示例一致） */
function formatDate(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`
}

/** 渲染文件名前的小图标（纯色方块圆角 + 白色 SVG） */
function renderFileIcon(meta: FileMeta) {
  return h(
    'span',
    {
      class: 'file-icon',
      style: { background: meta.iconColor },
    },
    [
      h(NIcon, { size: 14, color: '#fff' }, () =>
        h(
          'svg',
          { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' },
          [h('path', { d: meta.iconPath })],
        ),
      ),
    ],
  )
}

/** 表格列定义 */
const columns: DataTableColumns<KnowledgeFile> = [
  {
    title: '文件名',
    key: 'file_name',
    align: 'left',
    ellipsis: { tooltip: true },
    render: (row) => {
      const meta = fileMetaOf(row)
      return h('div', { class: 'name-cell' }, [
        renderFileIcon(meta),
        h('span', { class: 'name-text' }, row.file_name),
      ])
    },
  },
  {
    title: '类型',
    key: 'file_ext',
    align: 'center',
    width: 120,
    render: (row) => {
      const meta = fileMetaOf(row)
      return h(
        'span',
        {
          class: 'type-pill',
          style: { background: meta.pillBg, color: meta.pillColor, textAlign: 'center' },
        },
        meta.label,
      )
    },
  },
  {
    title: '大小',
    key: 'size',
    align: 'center',
    width: 110,
    render: (row) => h('span', { class: 'muted-cell' }, workspace.formatBytes(row.file_size)),
  },
  {
    title: '上传时间',
    key: 'created_at',
    align: 'center',
    width: 180,
    render: (row) => h('span', { class: 'muted-cell' }, formatDate(row.created_at)),
  },
  {
    title: '状态',
    key: 'parse_status',
    align: 'center',
    width: 100,
    render: (row) => {
      const s = statusOf(row)
      return h(
        'span',
        {
          class: ['status-pill', `status-pill--${s.tone}`],
          style: { justifyContent: 'center' },
        },
        [h('span', { class: 'status-dot' }), s.label],
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    width: 200,
    render: (row) => {
      // 向量解析中（pending / processing）禁止重命名和移动，避免与后台
      // ingest 线程并发写同一条记录
      const parsing =
        row.parse_status === 'pending' || row.parse_status === 'processing'
      const disabledTip = '文件正在向量解析中，完成后再进行此操作'
      return h(
        'div',
        { class: 'row-actions', style: { justifyContent: 'center' } },
        [
          h(
            'a',
            {
              class: 'link-btn link-btn--primary',
              onClick: () => void workspace.openPreview(row),
            },
            '预览',
          ),
          h(
            'a',
            {
              class: [
                'link-btn',
                parsing ? 'link-btn--disabled' : 'link-btn--primary',
              ],
              title: parsing ? disabledTip : undefined,
              onClick: () => {
                if (parsing) return
                workspace.openRenameFile(row)
              },
            },
            '重命名',
          ),
          h(
            'a',
            {
              class: [
                'link-btn',
                parsing ? 'link-btn--disabled' : 'link-btn--primary',
              ],
              title: parsing ? disabledTip : undefined,
              onClick: () => {
                if (parsing) return
                workspace.openMoveFile(row)
              },
            },
            '移动',
          ),
          h(
            NPopconfirm,
            {
              positiveText: '删除',
              negativeText: '取消',
              onPositiveClick: () => workspace.deleteFileNow(row),
            },
            {
              trigger: () =>
                h('a', { class: 'link-btn link-btn--danger' }, '删除'),
              default: () => `确定删除「${row.file_name}」？此操作不可恢复。`,
            },
          ),
        ],
      )
    },
  },
]
</script>

<template>
  <div class="file-panel">
    <!-- 顶部工具栏 -->
    <div class="panel-header">
      <div class="title-wrap">
        <div class="title-row">
          <span class="title-dot"></span>
          <span class="title">{{ workspace.breadcrumbLabel }}</span>
        </div>
        <div class="sub">共 {{ workspace.total }} 个文件</div>
      </div>

      <div class="toolbar">
        <NInput
          v-model:value="workspace.keyword"
          clearable
          size="medium"
          placeholder="搜索当前目录下的文件..."
          class="search-input"
        >
          <template #prefix>
            <NIcon :size="16">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
                />
              </svg>
            </NIcon>
          </template>
        </NInput>

        <NButton type="primary" class="upload-btn" @click="workspace.openUploadModal">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z" />
              </svg>
            </NIcon>
          </template>
          上传文件
        </NButton>
      </div>
    </div>

    <!-- 主体 -->
    <div class="panel-body">
      <div class="body-inner">
        <div
          v-if="!workspace.files.length && !workspace.listLoading"
          class="empty-wrap"
        >
          <div class="empty-card">
            <div class="empty-illustration">
              <div class="empty-orb empty-orb--a"></div>
              <div class="empty-orb empty-orb--b"></div>
              <div class="empty-icon">
                <NIcon :size="42">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-1 9h-3v3h-2v-3h-3v-2h3v-3h2v3h3v2z"
                    />
                  </svg>
                </NIcon>
              </div>
            </div>

            <div class="empty-title">
              {{ workspace.keyword ? '未找到匹配的文件' : '当前目录暂无文件' }}
            </div>
            <div class="empty-sub">
              <template v-if="workspace.keyword">
                试试更换关键词，或清空搜索查看全部文件。
              </template>
              <template v-else>
                支持 Markdown / Excel / TXT / 图片 / Word，立即上传开始构建知识库。
              </template>
            </div>

            <div class="empty-actions">
              <NButton
                v-if="workspace.keyword"
                size="medium"
                tertiary
                @click="workspace.keyword = ''"
              >
                清空搜索
              </NButton>
              <NButton
                size="medium"
                type="primary"
                class="empty-primary"
                @click="workspace.openUploadModal"
              >
                <template #icon>
                  <NIcon>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z" />
                    </svg>
                  </NIcon>
                </template>
                立即上传
              </NButton>
            </div>
          </div>
        </div>

        <div v-else class="table-wrap">
          <!-- 表格外壳：固定高度容器，NDataTable 通过 flex-height 填满 -->
          <div class="table-shell">
            <NDataTable
              :columns="columns"
              :data="workspace.files"
              :loading="workspace.listLoading"
              :bordered="false"

              flex-height
              size="medium"
              class="file-table"
              style="height: 100%"
            />
          </div>

          <!-- 固定底部分页栏 -->
          <div class="pager-bar">
            <div class="pager-info">
              第 <b>{{ workspace.page }}</b> 页 ·
              共 <b>{{ workspace.total }}</b> 条记录
            </div>
            <NPagination
              v-model:page="workspace.page"
              v-model:page-size="workspace.pageSize"
              :item-count="workspace.total"
              :page-sizes="[10, 20, 50]"
              show-size-picker
              show-quick-jumper
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.file-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  background: @bg-color;
}

/* 顶部工具栏 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px;
  background: @bg-white;
  border-bottom: 1px solid @border-color;
  flex-wrap: wrap;
}

.title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: @text-primary;
}

.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: @gradient-primary;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.12);
}

.title {
  line-height: 1.3;
}

.sub {
  font-size: 12px;
  color: @text-secondary;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.search-input {
  width: 280px;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}

.search-input:hover {
  transform: translateY(-1px);
}

.upload-btn {
  height: 36px;
  border-radius: @border-radius-md;
  background: @gradient-primary !important;
  border: none !important;
  letter-spacing: 0.5px;
  transition: opacity 0.2s, transform 0.15s;

  &:hover {
    opacity: 0.92;
  }
  &:active {
    transform: scale(0.98);
  }
}

/* 主体：固定视口占位，让表格高度可预测 */
.panel-body {
  flex: 1;
  min-height: 0;
  padding: 20px 24px;
  overflow: hidden;
  display: flex;
}

.body-inner {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.empty-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 48px 36px;
  background: @bg-white;
  border-radius: @border-radius-xl;
  box-shadow: @shadow-sm;
  max-width: 520px;
  width: 100%;
  text-align: center;
  animation: emptyEnter 0.4s ease;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.empty-card:hover {
  box-shadow: @shadow-md;
  transform: translateY(-2px);
}

/* 插画区：发光光晕 + 圆形图标 */
.empty-illustration {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.empty-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(18px);
  opacity: 0.55;
  animation: orbFloat 4s ease-in-out infinite;
}

.empty-orb--a {
  width: 90px;
  height: 90px;
  background: @primary-blue;
  top: 8px;
  left: 0;
}

.empty-orb--b {
  width: 80px;
  height: 80px;
  background: @primary-green;
  bottom: 6px;
  right: 0;
  animation-delay: 1.2s;
}

.empty-icon {
  position: relative;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: @bg-white;
  color: @primary-blue;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(33, 150, 243, 0.18),
    inset 0 0 0 1px rgba(33, 150, 243, 0.1);
}

.empty-title {
  font-size: 17px;
  font-weight: 600;
  color: @text-primary;
  margin-top: 4px;
}

.empty-sub {
  font-size: 13px;
  color: @text-secondary;
  line-height: 1.7;
  max-width: 360px;
}

.empty-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.empty-primary {
  height: 38px;
  padding: 0 22px;
  border-radius: @border-radius-md;
  background: @gradient-primary !important;
  border: none !important;
  letter-spacing: 0.5px;
  transition: opacity 0.2s, transform 0.15s;

  &:hover {
    opacity: 0.92;
  }
  &:active {
    transform: scale(0.98);
  }
}

@keyframes emptyEnter {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes orbFloat {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-6px) scale(1.05);
  }
}

/* 表格外层：一个整体"卡片"，包含 table + 底部分页条 */
.table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: @bg-white;
  border-radius: @border-radius-lg;
  box-shadow: @shadow-sm;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
  animation: tableEnter 0.35s ease;
}

.table-wrap:hover {
  box-shadow: @shadow-md;
}

/* 固定高度的表格容器，NDataTable 通过 flex-height 撑满该容器 */
.table-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.file-table {
  background: @bg-white;
}

/* 让 NDataTable 内部正确撑满（flex-height 模式下需要） */
:deep(.file-table .n-data-table) {
  height: 100%;
}

/* 表头：细腻分层，贴合图中的淡灰 */
:deep(.file-table .n-data-table-thead .n-data-table-th) {
  background: #fafbfc;
  font-weight: 600;
  color: #6b7280;
  font-size: 12px;
  letter-spacing: 0.5px;
  padding: 14px 16px;
  border-bottom: 1px solid @border-color;
}

/* 单元格：更舒适的行高与内边距 */
:deep(.file-table .n-data-table-td) {
  padding: 16px 16px;
  font-size: 13px;
  color: @text-primary;
  border-bottom: 1px solid fade(@border-color, 60%);
  transition: background-color 0.15s ease;
  vertical-align: middle;
}

/* 行悬浮：主色浅底 */
:deep(.file-table .n-data-table-tr:hover .n-data-table-td) {
  background: @primary-blue-light !important;
}

/* 去掉最后一行的底边（更干净） */
:deep(.file-table .n-data-table-tbody .n-data-table-tr:last-child .n-data-table-td) {
  border-bottom: none;
}

/* 空数据占位 */
:deep(.file-table .n-data-table-empty) {
  padding: 48px 0;
}

/* 底部固定分页条 */
.pager-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  background: @bg-color;
  border-top: 1px solid @border-color;
}

.pager-info {
  font-size: 12px;
  color: @text-secondary;

  b {
    color: @primary-blue;
    font-weight: 600;
    margin: 0 2px;
  }
}

/* 分页器中的 input / select 统一圆角 */
:deep(.pager-bar .n-pagination .n-pagination-item) {
  border-radius: @border-radius-sm;
  transition: background-color 0.15s, color 0.15s;
}

/* 非 active 项 hover：浅灰底 + 主题蓝文字 */
:deep(.pager-bar .n-pagination .n-pagination-item:not(.n-pagination-item--active):not(.n-pagination-item--disabled):hover) {
  background: #eef2ff;
  color: @primary-blue;
}

:deep(.pager-bar .n-pagination .n-pagination-item--active) {
  background: @gradient-primary;
  color: #fff;
  border-color: transparent;
}

/* active 项 hover：保持渐变背景 + 白字，避免 naive-ui 默认把 color 改回蓝色造成“蓝底蓝字”看似消失 */
:deep(.pager-bar .n-pagination .n-pagination-item--active:hover) {
  background: @gradient-primary;
  color: #fff;
  border-color: transparent;
  filter: brightness(1.05);
}

@keyframes tableEnter {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<!--
  ==========================================================================
  非 scoped 样式：专门服务于 NDataTable 通过 render 函数生成的节点
  ----------------------------------------------------------------------
  Vue 的 scoped CSS 不会把 [data-v-xxx] 作用域属性透传到 naive-ui 内部
  通过 render 函数动态创建的 vnode 上，导致在 `columns.render` 中写的
  class（例如 .type-pill / .status-pill / .link-btn）在 scoped 块里无效。
  所以这里把这些“单元格内容类”放到非 scoped 块，并都挂在 `.file-table` 下
  做命名空间隔离，避免污染全局。
  ==========================================================================
-->
<style lang="less">
/* ---------- 文件名单元格 ---------- */
.file-table .name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.file-table .file-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.file-table .name-text {
  font-weight: 500;
  color: @text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ---------- 类型 pill（浅底 + 对应主色文字） ---------- */
.file-table .type-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 12px;
  min-width: 64px;
  height: 22px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
  line-height: 1;
  white-space: nowrap;
}

/* ---------- 状态 pill ---------- */
.file-table .status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  height: 22px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
}

.file-table .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.file-table .status-pill--pending {
  background: #dcfce7;
  color: #15803d;
}
.file-table .status-pill--pending .status-dot {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.file-table .status-pill--processing {
  background: #ffedd5;
  color: #c2410c;
}
.file-table .status-pill--processing .status-dot {
  background: #f97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25);
  animation: kbFileStatusPulse 1.4s ease-in-out infinite;
}

.file-table .status-pill--success {
  background: #dbeafe;
  color: #1d4ed8;
}
.file-table .status-pill--success .status-dot {
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.file-table .status-pill--failed {
  background: #fee2e2;
  color: #b91c1c;
}
.file-table .status-pill--failed .status-dot {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.22);
}

@keyframes kbFileStatusPulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.75;
    transform: scale(1.15);
  }
}

/* ---------- 大小 / 时间 弱化文字 ---------- */
.file-table .muted-cell {
  color: #6b7280;
  font-size: 13px;
}

/* ---------- 操作列：纯文字链接 ---------- */
.file-table .row-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-table .link-btn {
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  user-select: none;
  transition: opacity 0.15s, transform 0.1s;
}
.file-table .link-btn:hover {
  opacity: 0.75;
}
.file-table .link-btn:active {
  transform: scale(0.96);
}
.file-table .link-btn--primary {
  color: @primary-blue;
}
.file-table .link-btn--danger {
  color: #ef4444;
}
.file-table .link-btn--disabled {
  color: #b1b5bd;
  cursor: not-allowed;
}
.file-table .link-btn--disabled:hover {
  opacity: 1;
}
.file-table .link-btn--disabled:active {
  transform: none;
}
</style>
