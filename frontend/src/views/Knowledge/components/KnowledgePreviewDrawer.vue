<script setup lang="ts">
/**
 * 预览抽屉
 * - 图片：<img>
 * - 文本 / markdown：<pre> 原文展示
 * - excel：NDataTable + 虚拟滚动（几万行也不卡）+ 横向滚动（列宽保证可读性）
 * - word：mammoth 转出的 HTML
 * - 错误或不支持：NEmpty 提示
 */
import { computed, inject, ref, watch } from 'vue'
import type { DataTableColumn, PaginationProps } from 'naive-ui'
import {
  NDrawer,
  NDrawerContent,
  NEmpty,
  NScrollbar,
  NSpin,
  NTabs,
  NTabPane,
  NTag,
  NDataTable,
} from 'naive-ui'
import { KNOWLEDGE_WORKSPACE_KEY } from '../composables/knowledgeWorkspace'
import type { PreviewSheet } from '@/types/knowledge'

const injected = inject(KNOWLEDGE_WORKSPACE_KEY)
if (!injected) throw new Error('KnowledgePreviewDrawer 必须在 Knowledge 工作区内使用')
const workspace = injected

const sheets = computed<PreviewSheet[]>(() => workspace.preview.sheets || [])

/** 当前激活 sheet */
const activeSheet = computed<PreviewSheet | null>(() => {
  const list = sheets.value
  if (!list.length) return null
  const name = workspace.preview.activeSheetName
  return list.find((s) => s.name === name) || list[0]
})

/** 估算一列的 min-width：按表头 + 采样的前 30 行内容字符数估算。
 *  中文按 2 个像素权重，最短 96px，最长 360px，够读又不至于单列吃满屏幕。
 */
function estimateColumnWidth(
  header: string,
  rows: string[][],
  colIndex: number,
): number {
  const weigh = (s: string) => {
    let w = 0
    for (const ch of s) w += ch.charCodeAt(0) > 127 ? 16 : 9
    return w
  }
  let max = weigh(header)
  const probe = Math.min(rows.length, 30)
  for (let i = 0; i < probe; i++) {
    const s = rows[i]?.[colIndex] ?? ''
    if (s) {
      const w = weigh(String(s))
      if (w > max) max = w
    }
  }
  return Math.min(360, Math.max(96, max + 32))
}

/** 把 PreviewSheet 转成 NDataTable 的 columns 配置 */
const tableColumns = computed<DataTableColumn<Record<string, string>>[]>(() => {
  const s = activeSheet.value
  if (!s || !s.columns.length) return []
  return s.columns.map((label, idx) => {
    const key = `c${idx}`
    const col: DataTableColumn<Record<string, string>> = {
      title: label,
      key,
      minWidth: estimateColumnWidth(label, s.rows, idx),
      ellipsis: { tooltip: true },
      render: (row) => (row[key] as string) ?? '',
    }
    return col
  })
})

/** 把 rows 二维数组转成对象数组（按 c{index} 做 key，避免同名列冲突） */
const tableData = computed<Record<string, string>[]>(() => {
  const s = activeSheet.value
  if (!s || !s.columns.length) return []
  return s.rows.map((row, rowIndex) => {
    const obj: Record<string, string> = { __key: String(rowIndex) }
    for (let i = 0; i < s.columns.length; i++) {
      obj[`c${i}`] = row[i] ?? ''
    }
    return obj
  })
})

/** 表格横向总宽（超过容器宽度时 NDataTable 会自己出现横滚条） */
const tableScrollX = computed(() => {
  return tableColumns.value.reduce(
    (sum, col) => sum + Number(col.minWidth || 120),
    0,
  )
})

// 让每行都有稳定 key，方便 NDataTable 重绘
const rowKey = (row: Record<string, string>) => row.__key

/** 表格分页：当前页 / 每页条数。
 *  虚拟滚动在大表上仍有开销，这里改成每页 50 行纯 DOM 渲染，最稳、最快。
 */
const currentPage = ref(1)
const pageSize = ref(50)

const pagination = computed<PaginationProps>(() => ({
  page: currentPage.value,
  pageSize: pageSize.value,
  pageSizes: [20, 50, 100, 200, 500],
  showSizePicker: true,
  itemCount: tableData.value.length,
  prefix: ({ itemCount }) => `共 ${itemCount} 行`,
  onUpdatePage: (p: number) => {
    currentPage.value = p
  },
  onUpdatePageSize: (ps: number) => {
    pageSize.value = ps
    currentPage.value = 1
  },
}))

// 切换 sheet / 打开新文件时，分页要回到第一页
watch(
  () => workspace.preview.activeSheetName,
  () => {
    currentPage.value = 1
  },
)
watch(
  () => workspace.preview.file?.id,
  () => {
    currentPage.value = 1
    pageSize.value = 50
  },
)
</script>

<template>
  <NDrawer
    :show="workspace.preview.visible"
    width="82%"
    placement="right"
    display-directive="show"
    class="preview-drawer"
    @update:show="(v) => { if (!v) workspace.closePreview() }"
  >
    <NDrawerContent closable @close="workspace.closePreview">
      <!--
        NDrawerContent 没有 header-extra 插槽，这里直接用 header 插槽
        自行组合标题 + 类型标签
      -->
      <template #header>
        <div class="preview-header">
          <span class="preview-title">
            {{ workspace.preview.file?.file_name || '文件预览' }}
          </span>
          <NTag
            v-if="workspace.preview.file"
            size="small"
            round
            :bordered="false"
            type="info"
            class="preview-type-tag"
          >
            {{ workspace.displayFileType(workspace.preview.file) }}
          </NTag>
          <NTag
            v-if="sheets.length"
            size="small"
            round
            :bordered="false"
            type="default"
            class="preview-sheet-count-tag"
          >
            共 {{ sheets.length }} 个工作表
          </NTag>
        </div>
      </template>

      <NSpin :show="workspace.preview.loading" class="preview-spin">
        <div v-if="workspace.preview.errorMessage" class="preview-error">
          <NEmpty :description="workspace.preview.errorMessage" />
        </div>
        <template v-else>
          <div v-if="workspace.preview.imageUrl" class="preview-image-wrap">
            <img
              :src="workspace.preview.imageUrl"
              alt="preview"
              class="preview-image"
            />
          </div>
          <NScrollbar
            v-else-if="workspace.preview.textContent != null"
            class="preview-scroll"
          >
            <pre class="preview-text">{{ workspace.preview.textContent }}</pre>
          </NScrollbar>
          <div
            v-else-if="sheets.length"
            class="preview-sheets"
          >
            <!-- 即使只有 1 个 sheet 也展示 tabs，方便用户确认看到的是哪一张 -->
            <NTabs
              type="line"
              size="small"
              animated
              :value="workspace.preview.activeSheetName"
              class="preview-sheet-tabs"
              @update:value="(v: string) => workspace.setActiveSheet(v)"
            >
              <NTabPane
                v-for="s in sheets"
                :key="s.name"
                :name="s.name"
                :tab="s.name"
              />
            </NTabs>
            <!-- 空 sheet / 解析失败的 sheet：直接显示占位，不走表格 -->
            <div
              v-if="activeSheet?.placeholder"
              class="preview-sheet-placeholder"
            >
              <NEmpty :description="activeSheet.placeholder" />
            </div>
            <NDataTable
              v-else-if="tableColumns.length"
              class="preview-data-table"
              size="small"
              :bordered="true"
              :single-line="false"
              striped
              :columns="tableColumns"
              :data="tableData"
              :row-key="rowKey"
              :pagination="pagination"
              :scroll-x="tableScrollX"
            />
            <div v-else class="preview-sheet-placeholder">
              <NEmpty description="（此工作表没有数据）" />
            </div>
          </div>
          <NScrollbar
            v-else-if="workspace.preview.htmlContent"
            class="preview-scroll"
          >
            <div class="preview-html" v-html="workspace.preview.htmlContent" />
          </NScrollbar>
          <div v-else class="preview-error">
            <NEmpty description="暂无可预览内容" />
          </div>
        </template>
      </NSpin>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped lang="less">
/* 自定义 header：标题 + 类型 pill 在同一行，且标题可省略 */
.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: @text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

.preview-type-tag,
.preview-sheet-count-tag {
  flex-shrink: 0;
}

.preview-spin {
  min-height: 240px;
}

.preview-image-wrap {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 16px 0 32px;
}

.preview-image {
  max-width: 100%;
  max-height: calc(100vh - 160px);
  border-radius: @border-radius-md;
  box-shadow: @shadow-md;
  background: @bg-color;
}

.preview-scroll {
  max-height: calc(100vh - 140px);
}

.preview-sheets {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.preview-sheet-tabs {
  margin-bottom: 8px;
}

.preview-scroll--with-tabs {
  /* tabs 占了一行高度，给 scroll 区域稍微减一点高 */
  max-height: calc(100vh - 188px);
}

.preview-data-table {
  /* NDataTable 自带 max-height，这里给外层留点呼吸 */
  padding: 0 4px 24px;
}

/* NDataTable 的表头在长列名场景下让竖排更紧凑，恢复横排 */
.preview-data-table :deep(.n-data-table-th__title-wrapper) {
  white-space: nowrap;
}

.preview-data-table :deep(.n-data-table-td) {
  white-space: nowrap;
}

/* 数据行 hover 高亮，方便用户沿某一行视线追踪 */
.preview-data-table :deep(.n-data-table-tr:hover .n-data-table-td) {
  background: rgba(33, 150, 243, 0.06) !important;
}

.preview-sheet-placeholder {
  padding: 56px 0;
  display: flex;
  justify-content: center;
}

.preview-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    'Liberation Mono', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 16px 20px 32px;
  background: @bg-color;
  border-radius: @border-radius-md;
}

.preview-html {
  font-size: 14px;
  line-height: 1.7;
  color: @text-primary;
  padding: 16px 4px 32px;
}

.preview-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: @bg-white;
}

.preview-html :deep(th),
.preview-html :deep(td) {
  border: 1px solid @border-color;
  padding: 8px 10px;
}

.preview-html :deep(th) {
  background: @bg-color;
  font-weight: 600;
}

.preview-html :deep(tr:nth-child(even) td) {
  background: rgba(33, 150, 243, 0.03);
}

.preview-html :deep(img) {
  max-width: 100%;
  border-radius: @border-radius-sm;
}

.preview-error {
  padding: 72px 0;
}
</style>
