<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NSpin, NTabs, NTabPane } from 'naive-ui'
import type { ExcelSheetHtml } from '@/utils/knowledgePreview.types'

const props = withDefaults(
  defineProps<{
    title: string
    loading?: boolean
    mode: 'text' | 'html' | 'excel'
    content: string
    html: string
    sheets: ExcelSheetHtml[]
  }>(),
  { loading: false, sheets: () => [] },
)

const show = defineModel<boolean>('show', { required: true })

const modalStyle = computed(() =>
  props.mode === 'excel'
    ? 'width: 920px; max-width: 96vw;'
    : 'width: 720px; max-width: 96vw;',
)

const firstTab = computed(() => props.sheets[0]?.name ?? '')

const tabsKey = computed(() => props.sheets.map((s) => s.name).join('|'))
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="title"
    :style="modalStyle"
    :mask-closable="true"
  >
    <NSpin :show="loading" class="preview-spin">
      <div v-if="mode === 'text'" class="preview-content">
        <pre class="preview-text">{{ content }}</pre>
      </div>
      <div v-else-if="mode === 'html'" class="preview-content preview-html" v-html="html" />
      <div v-else-if="mode === 'excel'" class="preview-content preview-excel">
        <NTabs v-if="sheets.length > 1" :key="tabsKey" type="line" :default-value="firstTab">
          <NTabPane v-for="s in sheets" :key="s.name" :name="s.name" :tab="s.name">
            <div class="sheet-html" v-html="s.html" />
          </NTabPane>
        </NTabs>
        <div v-else-if="sheets.length === 1" class="sheet-html" v-html="sheets[0].html" />
        <p v-else class="preview-empty">无法解析工作表</p>
      </div>
    </NSpin>
  </NModal>
</template>

<style scoped lang="less">
.preview-spin {
  min-height: 120px;
}

.preview-content {
  max-height: 65vh;
  overflow: auto;
}

.preview-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.8;
  color: @text-primary;
  margin: 0;
  font-family: inherit;
}

.preview-empty {
  color: @text-secondary;
  font-size: 14px;
  margin: 0;
}

.preview-html {
  font-size: 14px;
  line-height: 1.75;
  color: @text-primary;

  :deep(p) {
    margin: 0 0 0.75em;
  }
  :deep(h1, h2, h3) {
    margin: 1em 0 0.5em;
    font-weight: 600;
    color: @text-primary;
  }
  :deep(h1) { font-size: 1.35em; }
  :deep(h2) { font-size: 1.2em; }
  :deep(h3) { font-size: 1.08em; }
  :deep(ul, ol) {
    margin: 0 0 0.75em;
    padding-left: 1.4em;
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5em 0;
  }
  :deep(td, th) {
    border: 1px solid @border-color;
    padding: 6px 10px;
  }
}

.preview-excel {
  :deep(.sheet-html table) {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    background: @bg-white;
  }
  :deep(.sheet-html td, .sheet-html th) {
    border: 1px solid @border-color;
    padding: 8px 10px;
    text-align: left;
  }
  :deep(.sheet-html th) {
    background: @bg-color;
    font-weight: 600;
  }
  :deep(.sheet-html tr:nth-child(even)) {
    background: fade(@bg-color, 60%);
  }
}
</style>
