<script setup lang="ts">
import { ref, nextTick, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import {
  NButton,
  NInput,
  NIcon,
  NScrollbar,
  NEmpty,
  NText,
  NEllipsis,
  NTooltip,
} from 'naive-ui'
import type { ChatSession, ChatMessage } from '@/api/chat'

const message = useMessage()
const scrollbarRef = ref<InstanceType<typeof NScrollbar> | null>(null)
const inputValue = ref('')
const sending = ref(false)

const sessions = ref<ChatSession[]>([
  { id: '1', title: '运维故障排查', createdAt: '2026-04-13 10:00', updatedAt: '2026-04-13 10:30' },
  { id: '2', title: '系统监控方案', createdAt: '2026-04-12 14:00', updatedAt: '2026-04-12 15:00' },
])

const activeSessionId = ref('1')

const messagesMap = ref<Record<string, ChatMessage[]>>({
  '1': [
    { id: 'm1', role: 'assistant', content: '你好！我是运行智脑 AI 助手，可以帮您解答运维相关问题。请问有什么可以帮您的？', createdAt: '2026-04-13 10:00' },
    { id: 'm2', role: 'user', content: '服务器 CPU 使用率持续超过 90%，应该如何排查？', createdAt: '2026-04-13 10:01' },
    { id: 'm3', role: 'assistant', content: '**CPU 使用率过高的排查步骤：**\n\n1. **查看进程列表**\n   使用 `top` 或 `htop` 命令查看占用 CPU 最高的进程\n\n2. **分析进程详情**\n   - `ps aux --sort=-%cpu | head -20` 查看 CPU 占用 Top 20 进程\n   - 确认是否有异常进程\n\n3. **检查系统负载**\n   - `uptime` 查看系统负载\n   - `vmstat 1 10` 观察 CPU 等待情况\n\n4. **日志分析**\n   - 检查应用日志是否有死循环或大量请求\n   - 查看 `/var/log/syslog` 或 `dmesg`\n\n5. **针对性处理**\n   - 如果是应用进程：考虑优化代码或扩容\n   - 如果是系统进程：检查是否有安全问题\n\n需要我进一步分析某个具体场景吗？', createdAt: '2026-04-13 10:02' },
  ],
  '2': [
    { id: 'm4', role: 'assistant', content: '你好！请问您想了解哪方面的系统监控方案？', createdAt: '2026-04-12 14:00' },
  ],
})

const currentMessages = computed(() => messagesMap.value[activeSessionId.value] || [])

watch(activeSessionId, () => {
  nextTick(() => scrollToBottom())
})

function scrollToBottom() {
  nextTick(() => {
    scrollbarRef.value?.scrollTo({ top: 99999, behavior: 'smooth' })
  })
}

function selectSession(id: string) {
  activeSessionId.value = id
}

function createSession() {
  const id = Date.now().toString()
  const session: ChatSession = {
    id,
    title: '新对话',
    createdAt: new Date().toLocaleString('zh-CN'),
    updatedAt: new Date().toLocaleString('zh-CN'),
  }
  sessions.value.unshift(session)
  messagesMap.value[id] = [
    {
      id: `m-${id}-welcome`,
      role: 'assistant',
      content: '你好！我是运行智脑 AI 助手，请问有什么可以帮您的？',
      createdAt: new Date().toLocaleString('zh-CN'),
    },
  ]
  activeSessionId.value = id
}

function deleteSession(id: string) {
  sessions.value = sessions.value.filter((s) => s.id !== id)
  delete messagesMap.value[id]
  if (activeSessionId.value === id) {
    activeSessionId.value = sessions.value[0]?.id || ''
  }
  message.success('已删除会话')
}

function handleSend() {
  const content = inputValue.value.trim()
  if (!content || sending.value) return
  if (!activeSessionId.value) createSession()

  const userMsg: ChatMessage = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content,
    createdAt: new Date().toLocaleString('zh-CN'),
  }

  if (!messagesMap.value[activeSessionId.value]) {
    messagesMap.value[activeSessionId.value] = []
  }
  messagesMap.value[activeSessionId.value].push(userMsg)

  const session = sessions.value.find((s) => s.id === activeSessionId.value)
  if (session && session.title === '新对话') {
    session.title = content.slice(0, 20)
  }

  inputValue.value = ''
  scrollToBottom()
  simulateAIResponse()
}

function simulateAIResponse() {
  sending.value = true
  const thinkingMsg: ChatMessage = {
    id: `msg-thinking-${Date.now()}`,
    role: 'assistant',
    content: '',
    createdAt: new Date().toLocaleString('zh-CN'),
  }
  messagesMap.value[activeSessionId.value].push(thinkingMsg)
  scrollToBottom()

  setTimeout(() => {
    const msgs = messagesMap.value[activeSessionId.value]
    const idx = msgs.findIndex((m) => m.id === thinkingMsg.id)
    if (idx !== -1) {
      msgs[idx] = {
        ...thinkingMsg,
        content:
          '根据知识库中的资料，我为您整理了以下信息：\n\n这是一个模拟回复。后续接入后端 AI 接口后，这里将返回基于 RAG 知识库的真实回答。\n\n如果您有更具体的问题，请继续提问。',
      }
    }
    sending.value = false
    scrollToBottom()
  }, 1500)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const activeSession = computed(() => sessions.value.find((s) => s.id === activeSessionId.value))
</script>

<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-top">
        <NButton type="primary" block strong class="new-chat-btn" @click="createSession">
          <template #icon>
            <NIcon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
              </svg></NIcon>
          </template>
          新建对话
        </NButton>
      </div>
      <NScrollbar class="sidebar-list">
        <div v-if="sessions.length === 0" class="sidebar-empty">
          <NEmpty description="暂无会话" :show-icon="false" />
        </div>
        <TransitionGroup name="session-list">
          <div v-for="session in sessions" :key="session.id"
            :class="['session-item', { active: session.id === activeSessionId }]" @click="selectSession(session.id)">
            <div class="session-icon-wrap">
              <NIcon :size="16" class="session-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                </svg>
              </NIcon>
            </div>
            <div class="session-info">
              <NEllipsis class="session-title">{{ session.title }}</NEllipsis>
              <NText depth="3" class="session-time">{{ session.updatedAt }}</NText>
            </div>
            <NTooltip trigger="hover" placement="right">
              <template #trigger>
                <NButton size="tiny" quaternary class="session-delete" @click.stop="deleteSession(session.id)">
                  <template #icon>
                    <NIcon :size="14"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                      </svg></NIcon>
                  </template>
                </NButton>
              </template>
              删除会话
            </NTooltip>
          </div>
        </TransitionGroup>
      </NScrollbar>
    </div>

    <!-- 右侧对话区 -->
    <div class="chat-main">
      <div class="chat-header">
        <div class="chat-header-left">
          <div class="chat-header-dot"></div>
          <span class="chat-title">{{ activeSession?.title || 'AI 对话' }}</span>
        </div>
        <NText depth="3" class="chat-header-hint">基于 RAG 知识库的智能问答</NText>
      </div>
      <div class="chat-messages-container">
        <NScrollbar ref="scrollbarRef" class="chat-messages">
          <div v-if="currentMessages.length === 0" class="messages-empty">
            <div class="empty-hero">
              <div class="empty-logo">AI</div>
              <h3 class="empty-title">运行智脑 AI 助手</h3>
              <p class="empty-desc">基于知识库为您提供智能问答服务</p>
              <div class="empty-suggestions">
                <div class="suggestion-chip" @click="inputValue = '服务器 CPU 过高如何排查？'">服务器 CPU 过高如何排查？</div>
                <div class="suggestion-chip" @click="inputValue = '如何配置系统监控告警？'">如何配置系统监控告警？</div>
                <div class="suggestion-chip" @click="inputValue = '数据库备份最佳实践'">数据库备份最佳实践</div>
              </div>
            </div>
          </div>

          <TransitionGroup name="msg-appear">
            <div v-for="msg in currentMessages" :key="msg.id" :class="['message-row', msg.role]">
              <div class="message-avatar">
                <div v-if="msg.role === 'assistant'" class="avatar ai-avatar">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="currentColor">
                    <path
                      d="M21 10.5h-1V8c0-1.1-.9-2-2-2h-3V4.5C15 3.12 13.88 2 12.5 2h-1C10.12 2 9 3.12 9 4.5V6H6c-1.1 0-2 .9-2 2v2.5H3c-.55 0-1 .45-1 1s.45 1 1 1h1V15c0 1.1.9 2 2 2h3v1.5c0 1.38 1.12 2.5 2.5 2.5h1c1.38 0 2.5-1.12 2.5-2.5V17h3c1.1 0 2-.9 2-2v-2.5h1c.55 0 1-.45 1-1s-.45-1-1-1zM9.5 12c-.83 0-1.5-.67-1.5-1.5S8.67 9 9.5 9s1.5.67 1.5 1.5S10.33 12 9.5 12zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 9 14.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" />
                  </svg>
                </div>
                <div v-else class="avatar user-avatar">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                    fill="currentColor">
                    <path
                      d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
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
          </TransitionGroup>
        </NScrollbar>
      </div>
      <div class="chat-input-area">
        <div class="input-wrapper">
          <NInput v-model:value="inputValue" type="textarea" placeholder="输入消息，Enter 发送，Shift + Enter 换行..."
            :autosize="{ minRows: 1, maxRows: 5 }" :disabled="sending" class="chat-input" @keydown="handleKeydown" />
          <NButton type="primary" circle :disabled="!inputValue.trim() || sending" :loading="sending" class="send-btn"
            @click="handleSend">
            <template v-if="!sending" #icon>
              <NIcon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg></NIcon>
            </template>
          </NButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.chat-page {
  display: flex;
  height: calc(100vh - 100px);
  background: @bg-white;
  border-radius: @border-radius-lg;
  overflow: hidden;
  box-shadow: @shadow-sm;
  animation: pageEnter 0.4s ease;
}

/* ── 左侧会话 ── */
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

  &:hover {
    opacity: 0.9;
  }

  &:active {
    transform: scale(0.98);
  }
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

    .session-delete {
      opacity: 1;
    }
  }

  &.active {
    background: @bg-white;
    box-shadow: 0 2px 12px rgba(33, 150, 243, 0.12);

    .session-icon-wrap {
      background: @primary-blue-light;

      .session-icon {
        color: @primary-blue;
      }
    }

    .session-title {
      color: @primary-blue;
      font-weight: 600;
    }
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

  &:hover {
    color: #e53935;
  }
}

/* ── 右侧对话区 ── */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: @bg-color;
  box-sizing: border-box;
}

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

.chat-messages {
  flex: 1;
  padding: 24px 28px 8px 24px;
}

/* ── 空状态 ── */
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

/* ── 消息 ── */
.message-row {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  margin-bottom: 0;
  max-width: 900px;

  &.user {
    flex-direction: row-reverse;
    margin-left: auto;

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

/* ── Typing 动效 ── */
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

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
}

/* ── 输入区 ── */
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

  &:hover:not(:disabled) {
    opacity: 0.9;
  }

  &:active:not(:disabled) {
    transform: scale(0.92);
  }

  &:disabled {
    opacity: 0.4;
    background: @bg-color !important;
  }
}

/* ── 动效 ── */
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

.msg-appear-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.msg-appear-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: scale(0.98);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.5;
    transform: scale(0.85);
  }
}

@keyframes typingBounce {

  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}
</style>
