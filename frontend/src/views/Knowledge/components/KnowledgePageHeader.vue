<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'

defineEmits<{
  upload: []
}>()
</script>

<template>
  <div class="page-header">
    <div class="header-text">
      <h2 class="page-title">知识库管理</h2>
      <p class="page-desc">上传文档构建 RAG 知识库，支持 PDF、Word、TXT、Markdown、Excel、CSV</p>
    </div>
    <NButton type="primary" @click="$emit('upload')">
      <template #icon>
        <NIcon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 10.04A7.49 7.49 0 0 0 12 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 0 0 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" /></svg></NIcon>
      </template>
      上传文件
    </NButton>
  </div>
</template>

<style scoped lang="less">
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
  animation: fadeSlideDown 0.4s ease;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: @text-primary;
  margin-bottom: 4px;
}

.page-desc {
  font-size: 14px;
  color: @text-secondary;
}

@keyframes fadeSlideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
