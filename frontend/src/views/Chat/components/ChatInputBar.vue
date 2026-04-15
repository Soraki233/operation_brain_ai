<script setup lang="ts">
import { NButton, NIcon, NInput } from 'naive-ui'

defineProps<{
  sending: boolean
}>()

const model = defineModel<string>({ required: true })

const emit = defineEmits<{
  send: []
}>()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('send')
  }
}
</script>

<template>
  <div class="chat-input-area">
    <div class="input-wrapper">
      <NInput
        v-model:value="model"
        type="textarea"
        placeholder="输入消息，Enter 发送，Shift + Enter 换行..."
        :autosize="{ minRows: 1, maxRows: 5 }"
        :disabled="sending"
        class="chat-input"
        @keydown="handleKeydown"
      />
      <NButton
        type="primary"
        circle
        :disabled="!model.trim() || sending"
        :loading="sending"
        class="send-btn"
        @click="emit('send')"
      >
        <template v-if="!sending" #icon>
          <NIcon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg></NIcon>
        </template>
      </NButton>
    </div>
  </div>
</template>

<style scoped lang="less">
.chat-input-area {
  padding: 12px 24px 16px;
  background: @bg-color;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: @bg-white;
  border-radius: @border-radius-lg;
  padding: 8px 8px 8px 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid @border-color;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:focus-within {
    border-color: @primary-blue;
    box-shadow: 0 2px 16px rgba(33, 150, 243, 0.12);
  }
}

.chat-input {
  flex: 1;

  :deep(.n-input__border),
  :deep(.n-input__state-border) {
    display: none !important;
  }
  :deep(.n-input-wrapper) {
    padding: 0;
  }
}

.send-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  background: @gradient-primary !important;
  border: none !important;
  transition: opacity 0.2s, transform 0.15s;

  &:hover:not(:disabled) { opacity: 0.9; }
  &:active:not(:disabled) { transform: scale(0.92); }
  &:disabled { opacity: 0.4; background: @bg-color !important; }
}
</style>
