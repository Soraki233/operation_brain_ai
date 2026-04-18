<script setup lang="ts">
import { NButton, NIcon, NScrollbar, NEmpty, NText, NEllipsis, NTooltip } from 'naive-ui'
import type { ChatSession } from '@/api/chat'

defineProps<{
  sessions: ChatSession[]
  activeSessionId: string
}>()

const emit = defineEmits<{
  create: []
  select: [id: string]
  delete: [id: string]
}>()

/** ISO 字符串 → 本地 yyyy-MM-dd HH:mm */
function formatTime(value: string | null | undefined): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <div class="chat-sidebar">
    <div class="sidebar-top">
      <NButton type="primary" block strong class="new-chat-btn" @click="emit('create')">
        <template #icon>
          <NIcon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" /></svg></NIcon>
        </template>
        新建对话
      </NButton>
    </div>
    <NScrollbar class="sidebar-list">
      <div v-if="sessions.length === 0" class="sidebar-empty">
        <NEmpty description="暂无会话" :show-icon="false" />
      </div>
      <TransitionGroup name="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === activeSessionId }]"
          @click="emit('select', session.id)"
        >
          <div class="session-icon-wrap">
            <NIcon :size="16" class="session-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
              </svg>
            </NIcon>
          </div>
          <div class="session-info">
            <NEllipsis class="session-title">{{ session.title }}</NEllipsis>
            <NText depth="3" class="session-time">{{ formatTime(session.last_message_at || session.updated_at) }}</NText>
          </div>
          <NTooltip trigger="hover" placement="right">
            <template #trigger>
              <NButton
                size="tiny"
                quaternary
                class="session-delete"
                @click.stop="emit('delete', session.id)"
              >
                <template #icon>
                  <NIcon :size="14"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" /></svg></NIcon>
                </template>
              </NButton>
            </template>
            删除会话
          </NTooltip>
        </div>
      </TransitionGroup>
    </NScrollbar>
  </div>
</template>

<style scoped lang="less">
.chat-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid @border-color;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, @bg-white 0%, @bg-color 100%);
}

.sidebar-top {
  padding: 16px;
  flex-shrink: 0;
}

.new-chat-btn {
  height: 42px;
  border-radius: @border-radius-md;
  background: @gradient-primary !important;
  border: none !important;
  letter-spacing: 1px;
  transition: opacity 0.2s, transform 0.15s;

  &:hover { opacity: 0.9; }
  &:active { transform: scale(0.98); }
}

.sidebar-list {
  flex: 1;
  padding: 8px 8px 0;
}

.sidebar-empty {
  padding: 40px 16px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 2px;
  border-radius: @border-radius-md;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: @bg-white;
    box-shadow: @shadow-sm;
    .session-delete { opacity: 1; }
  }

  &.active {
    background: @bg-white;
    box-shadow: 0 2px 12px rgba(33, 150, 243, 0.12);

    .session-icon-wrap {
      background: @primary-blue-light;
      .session-icon { color: @primary-blue; }
    }
    .session-title { color: @primary-blue; font-weight: 600; }
  }
}

.session-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: @border-radius-sm;
  background: @bg-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s;
}

.session-icon {
  color: @text-placeholder;
  transition: color 0.2s;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
}

.session-title {
  font-size: 14px;
  color: @text-primary;
  display: block;
  width: 100%;
  line-height: 1.35;
  transition: color 0.2s;
}

.session-time {
  font-size: 11px;
  line-height: 1.2;
  margin-top: 0;
}

.session-delete {
  opacity: 0;
  flex-shrink: 0;
  color: @text-placeholder;
  transition: opacity 0.15s, color 0.15s;

  &:hover { color: #e53935; }
}

.session-list-enter-active {
  transition: all 0.3s ease;
}
.session-list-leave-active {
  transition: all 0.2s ease;
}
.session-list-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.session-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
