<script setup lang="ts">
import { ref, nextTick, watch, computed } from 'vue'
import { useMessage, NScrollbar } from 'naive-ui'
import type { ChatSession, ChatMessage } from '@/api/chat'
import ChatSidebar from './components/ChatSidebar.vue'
import ChatHeader from './components/ChatHeader.vue'
import ChatEmptyState from './components/ChatEmptyState.vue'
import ChatMessageRow from './components/ChatMessageRow.vue'
import ChatInputBar from './components/ChatInputBar.vue'

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

const activeSession = computed(() => sessions.value.find((s) => s.id === activeSessionId.value))
</script>

<template>
  <div class="chat-page">
    <ChatSidebar
      :sessions="sessions"
      :active-session-id="activeSessionId"
      @create="createSession"
      @select="selectSession"
      @delete="deleteSession"
    />

    <div class="chat-main">
      <ChatHeader :title="activeSession?.title || 'AI 对话'" />

      <NScrollbar ref="scrollbarRef" class="chat-messages">
        <ChatEmptyState
          v-if="currentMessages.length === 0"
          @pick-suggestion="(text) => (inputValue = text)"
        />
        <TransitionGroup v-else name="msg-appear">
          <ChatMessageRow v-for="msg in currentMessages" :key="msg.id" :msg="msg" />
        </TransitionGroup>
      </NScrollbar>

      <ChatInputBar v-model="inputValue" :sending="sending" @send="handleSend" />
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

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: @bg-color;
  box-sizing: border-box;
}

.chat-messages {
  flex: 1;
  padding: 24px 28px 8px 24px;
}

.msg-appear-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.msg-appear-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

@keyframes pageEnter {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}
</style>
