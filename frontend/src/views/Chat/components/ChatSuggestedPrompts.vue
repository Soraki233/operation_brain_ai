<script setup lang="ts">
/** 占位数据，后续可改为接口或 props */
const suggestedQuestions = [
  '如何用 Obsidian 建立知识体系？',
  '常用缩写 RBQ 代表什么？',
  '自己在家怎么安全卸甲？',
  '首创环保的主要业务有哪些？',
] as const

const emit = defineEmits<{
  pick: [text: string]
}>()
</script>

<template>
  <div class="suggested-prompts" role="list" aria-label="推荐问题">
    <button
      v-for="text in suggestedQuestions"
      :key="text"
      type="button"
      class="prompt-bubble"
      role="listitem"
      @click="emit('pick', text)"
    >
      {{ text }}
    </button>
  </div>
</template>

<style scoped lang="less">
.suggested-prompts {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  align-items: flex-start;
  gap: 6px 8px;
  padding: 0 24px 6px;
  flex-shrink: 0;
}

.prompt-bubble {
  display: inline-block;
  width: auto;
  max-width: 100%;
  margin: 0;
  padding: 5px 10px;
  text-align: left;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.35;
  color: @text-primary;
  background: @bg-white;
  border: 1px solid @border-color;
  border-radius: @border-radius-md;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;

  &:hover {
    border-color: fade(@primary-blue, 45%);
    box-shadow: @shadow-sm;
  }

  &:active {
    background: @primary-blue-light;
  }
}
</style>
