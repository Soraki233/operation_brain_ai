<script setup lang="ts">
/**
 * 预览抽屉
 * - 图片：<img>
 * - 文本 / markdown：<pre> 原文展示
 * - excel / word：mammoth / xlsx 生成的 HTML
 * - 错误或不支持：NEmpty 提示
 */
import { inject } from 'vue'
import { NDrawer, NDrawerContent, NEmpty, NScrollbar, NSpin, NTag } from 'naive-ui'
import { KNOWLEDGE_WORKSPACE_KEY } from '../composables/knowledgeWorkspace'

const injected = inject(KNOWLEDGE_WORKSPACE_KEY)
if (!injected) throw new Error('KnowledgePreviewDrawer 必须在 Knowledge 工作区内使用')
const workspace = injected
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

.preview-type-tag {
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
