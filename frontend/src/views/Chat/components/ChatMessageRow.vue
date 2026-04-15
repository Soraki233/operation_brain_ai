<script setup lang="ts">
import type { ChatMessage } from '@/api/chat'

defineProps<{
  msg: ChatMessage
}>()
</script>

<template>
  <div :class="['message-row', msg.role]">
    <div class="message-avatar">
      <div v-if="msg.role === 'assistant'" class="avatar ai-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M21 10.5h-1V8c0-1.1-.9-2-2-2h-3V4.5C15 3.12 13.88 2 12.5 2h-1C10.12 2 9 3.12 9 4.5V6H6c-1.1 0-2 .9-2 2v2.5H3c-.55 0-1 .45-1 1s.45 1 1 1h1V15c0 1.1.9 2 2 2h3v1.5c0 1.38 1.12 2.5 2.5 2.5h1c1.38 0 2.5-1.12 2.5-2.5V17h3c1.1 0 2-.9 2-2v-2.5h1c.55 0 1-.45 1-1s-.45-1-1-1zM9.5 12c-.83 0-1.5-.67-1.5-1.5S8.67 9 9.5 9s1.5.67 1.5 1.5S10.33 12 9.5 12zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 9 14.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" />
        </svg>
      </div>
      <div v-else class="avatar user-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
        </svg>
      </div>
    </div>
    <div class="message-body">
      <div v-if="msg.role === 'assistant' && msg.content === ''" class="typing-indicator">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
      <div v-else class="message-bubble">
        <pre class="message-text">{{ msg.content }}</pre>
      </div>
      <div class="message-time">{{ msg.createdAt }}</div>
    </div>
  </div>
</template>

<style scoped lang="less">
.message-row {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  margin-bottom: 0;
  max-width: 800px;

  &.user {
    flex-direction: row-reverse;
    margin-left: auto;
    margin-right: 20px;

    .message-bubble {
      background: @primary-blue;
      color: #fff;
      border-radius: 18px 18px 4px 18px;
    }
    .message-time {
      text-align: right;
    }
  }

  &.assistant {
    padding-left: 20px;
    .message-bubble {
      background: @bg-white;
      color: @text-primary;
      border-radius: 18px 18px 18px 4px;
      box-shadow: @shadow-sm;
    }
  }
}

.message-avatar {
  flex-shrink: 0;
  padding-top: 2px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-avatar {
  background: @gradient-primary;
  color: #fff;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

.user-avatar {
  background: @primary-blue-light;
  color: @primary-blue;
}

.message-body {
  max-width: 70%;
  min-width: 0;
}

.message-bubble {
  padding: 12px 16px;
  transition: transform 0.15s ease;
}

.message-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.7;
  font-family: inherit;
}

.message-time {
  font-size: 11px;
  color: transparent;
  margin-top: 6px;
  padding: 0 4px;
  letter-spacing: 0.3px;
  transition: color 0.25s ease;
}

.message-row:hover .message-time {
  color: @text-placeholder;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 14px 18px;
  background: @bg-white;
  border-radius: 18px 18px 18px 4px;
  box-shadow: @shadow-sm;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: @primary-blue;
  opacity: 0.4;
  animation: typingBounce 1.4s ease-in-out infinite;

  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}
</style>
