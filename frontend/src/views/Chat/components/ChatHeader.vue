<script setup lang="ts">
import { NText } from 'naive-ui'

withDefaults(
  defineProps<{
    title: string
    hint?: string
  }>(),
  { hint: '基于 RAG 知识库的智能问答' },
)
</script>

<template>
  <div class="chat-header">
    <div class="chat-header-left">
      <div class="chat-header-dot"></div>
      <span class="chat-title">{{ title }}</span>
    </div>
    <NText depth="3" class="chat-header-hint">{{ hint }}</NText>
  </div>
</template>

<style scoped lang="less">
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: @bg-white;
  border-bottom: 1px solid @border-color;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-header-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: @primary-green;
  animation: pulse 2s ease-in-out infinite;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: @text-primary;
}

.chat-header-hint {
  font-size: 12px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}
</style>
