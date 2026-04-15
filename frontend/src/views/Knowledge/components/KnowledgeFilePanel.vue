<script setup lang="ts">
import { NInput, NIcon, NText, NDataTable, NEmpty } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { KnowledgeFile } from '@/api/knowledge'

defineProps<{
  columns: DataTableColumns<KnowledgeFile & { folderId: string }>
  data: (KnowledgeFile & { folderId: string })[]
}>()

const searchQuery = defineModel<string>('searchQuery', { required: true })
</script>

<template>
  <div class="file-main">
    <div class="file-toolbar">
      <NInput
        v-model:value="searchQuery"
        placeholder="搜索文件名或类型..."
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <NIcon :size="16"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" /></svg></NIcon>
        </template>
      </NInput>
      <NText depth="3" class="file-count">{{ data.length }} 个文件</NText>
    </div>

    <div class="file-table-wrap">
      <NDataTable
        :columns="columns"
        :data="data"
        :bordered="false"
        :row-key="(row: KnowledgeFile & { folderId: string }) => row.id"
        :row-class-name="() => 'file-row'"
        max-height="calc(100vh - 300px)"
        virtual-scroll
      >
        <template #empty>
          <NEmpty description="暂无文件，请上传文档" />
        </template>
      </NDataTable>
    </div>
  </div>
</template>

<style scoped lang="less">
.file-main {
  flex: 1;
  background: @bg-white;
  border-radius: @border-radius-lg;
  box-shadow: @shadow-sm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.file-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid @border-color;
  flex-shrink: 0;
}

.search-input {
  max-width: 280px;
}

.file-count {
  margin-left: auto;
  font-size: 13px;
  white-space: nowrap;
}

.file-table-wrap {
  flex: 1;
  padding: 0 12px 12px;
  overflow: hidden;
}

:deep(.file-row) {
  animation: fadeIn 0.3s ease;
}

:deep(.file-name-cell) {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.file-icon) {
  flex-shrink: 0;
}
:deep(.file-icon-pdf) { color: #e53935; }
:deep(.file-icon-word) { color: #1976D2; }
:deep(.file-icon-excel) { color: #388E3C; }
:deep(.file-icon-markdown) { color: #F57C00; }
:deep(.file-icon-txt) { color: #757575; }
:deep(.file-icon-csv) { color: #388E3C; }

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
