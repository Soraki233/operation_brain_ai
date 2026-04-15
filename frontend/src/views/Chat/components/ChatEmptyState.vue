<script setup lang="ts">
const emit = defineEmits<{
  pickSuggestion: [text: string]
}>()

const suggestions = [
  '服务器 CPU 过高如何排查？',
  '如何配置系统监控告警？',
  '数据库备份最佳实践',
] as const
</script>

<template>
  <div class="messages-empty">
    <div class="empty-hero">
      <div class="empty-logo">AI</div>
      <h3 class="empty-title">运行智脑 AI 助手</h3>
      <p class="empty-desc">基于知识库为您提供智能问答服务</p>
      <div class="empty-suggestions">
        <div
          v-for="text in suggestions"
          :key="text"
          class="suggestion-chip"
          @click="emit('pickSuggestion', text)"
        >
          {{ text }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.messages-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.empty-hero {
  text-align: center;
  animation: fadeSlideUp 0.5s ease;
}

.empty-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 20px;
  background: @gradient-primary;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.25);
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: @text-primary;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: @text-secondary;
  margin-bottom: 24px;
}

.empty-suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.suggestion-chip {
  padding: 8px 16px;
  background: @bg-white;
  border: 1px solid @border-color;
  border-radius: 20px;
  font-size: 13px;
  color: @text-primary;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: @primary-blue;
    color: @primary-blue;
    background: @primary-blue-light;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
  }
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
