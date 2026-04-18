<script setup lang="ts">
import { ref, nextTick, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { useMessage, NScrollbar } from 'naive-ui'
import * as chatApi from '@/api/chat'
import type { ChatSession, ChatMessage, StreamAskHandle } from '@/api/chat'
import ChatSidebar from './components/ChatSidebar.vue'
import ChatHeader from './components/ChatHeader.vue'
import ChatEmptyState from './components/ChatEmptyState.vue'
import ChatMessageRow from './components/ChatMessageRow.vue'
import ChatInputBar from './components/ChatInputBar.vue'
import ChatSuggestedPrompts from './components/ChatSuggestedPrompts.vue'

const message = useMessage()
const scrollbarRef = ref<InstanceType<typeof NScrollbar> | null>(null)
const inputValue = ref('')
const sending = ref(false)

const sessions = ref<ChatSession[]>([])
const activeSessionId = ref('')
const messagesMap = ref<Record<string, ChatMessage[]>>({})

/** 当前流式请求句柄，切换会话 / 卸载组件时用于中止 */
let currentStream: StreamAskHandle | null = null

const currentMessages = computed(
  () => messagesMap.value[activeSessionId.value] || [],
)
const activeSession = computed(() =>
  sessions.value.find((s) => s.id === activeSessionId.value),
)

/* ------------------------------- 生命周期 ------------------------------- */

onMounted(async () => {
  await refreshSessions()
  if (sessions.value.length > 0) {
    await selectSession(sessions.value[0].id)
  }
})

onBeforeUnmount(() => {
  currentStream?.abort()
})

watch(activeSessionId, () => {
  nextTick(() => scrollToBottom())
})

/* --------------------------------- 工具 --------------------------------- */

function scrollToBottom() {
  nextTick(() => {
    scrollbarRef.value?.scrollTo({ top: 99999, behavior: 'smooth' })
  })
}

async function refreshSessions() {
  try {
    sessions.value = await chatApi.listThreads()
  } catch {
    // 错误提示由 request 拦截器统一处理
  }
}

async function loadMessages(sessionId: string) {
  try {
    const list = await chatApi.listMessages(sessionId)
    messagesMap.value[sessionId] = list
  } catch {
    messagesMap.value[sessionId] = []
  }
}

/* -------------------------------- 会话操作 ------------------------------- */

async function selectSession(id: string) {
  activeSessionId.value = id
  if (!messagesMap.value[id]) {
    await loadMessages(id)
  }
  scrollToBottom()
}

async function createSession() {
  try {
    const session = await chatApi.createThread()
    sessions.value.unshift(session)
    messagesMap.value[session.id] = []
    activeSessionId.value = session.id
  } catch {
    // 错误提示由 request 拦截器统一处理
  }
}

async function deleteSession(id: string) {
  try {
    await chatApi.deleteThread(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    delete messagesMap.value[id]
    if (activeSessionId.value === id) {
      const next = sessions.value[0]
      if (next) {
        await selectSession(next.id)
      } else {
        activeSessionId.value = ''
      }
    }
    message.success('已删除会话')
  } catch {
    // 错误提示由 request 拦截器统一处理
  }
}

/* -------------------------------- 发送消息 ------------------------------- */

function sendSuggestedPrompt(text: string) {
  const t = text.trim()
  if (!t || sending.value) return
  inputValue.value = t
  handleSend()
}

async function handleSend() {
  const content = inputValue.value.trim()
  if (!content || sending.value) return

  // 没有激活会话时先建一个
  if (!activeSessionId.value) {
    await createSession()
    if (!activeSessionId.value) return
  }
  const sessionId = activeSessionId.value

  const now = new Date().toISOString()
  const list = messagesMap.value[sessionId] || (messagesMap.value[sessionId] = [])
  list.push(
    {
      id: `local-user-${Date.now()}`,
      role: 'user',
      content,
      citations: [],
      created_at: now,
    },
    {
      id: `local-assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      citations: [],
      created_at: now,
      streaming: true,
    },
  )
  // ref 在 push 时会把对象包成 reactive Proxy；必须用数组中的引用来修改，
  // 否则直接改原对象的属性不会触发 set trap，SSE token 到来时视图不会更新。
  const assistantMsg = list[list.length - 1] as ChatMessage

  inputValue.value = ''
  sending.value = true
  scrollToBottom()

  currentStream = chatApi.streamAsk(sessionId, content, {
    onCitations: (citations) => {
      assistantMsg.citations = citations
    },
    onToken: (delta) => {
      assistantMsg.content += delta
      scrollToBottom()
    },
    onDone: ({ title }) => {
      assistantMsg.streaming = false
      const session = sessions.value.find((s) => s.id === sessionId)
      if (session && title) session.title = title
    },
    onError: (err) => {
      assistantMsg.streaming = false
      assistantMsg.content = assistantMsg.content || `（请求失败：${err}）`
      message.error(err || '请求失败')
    },
  })

  try {
    await currentStream.done
  } catch {
    // 已在回调里 message.error
  } finally {
    sending.value = false
    currentStream = null
    scrollToBottom()
  }
}
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

      <ChatSuggestedPrompts @pick="sendSuggestedPrompt" />
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
