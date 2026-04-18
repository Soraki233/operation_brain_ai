<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { NCollapse, NCollapseItem, NTag, NEllipsis, NIcon, NPopconfirm } from 'naive-ui'
import type { ChatMessage } from '@/api/chat'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  msg: ChatMessage
  /** 父组件正在执行删除动效 */
  deleting?: boolean
}>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

const rendered = computed(() => renderMarkdown(props.msg.content || ''))

/* -------------------- 证据阅读（thinking）折叠 -------------------- */
const hasThinking = computed(
  () => props.msg.role === 'assistant' && !!props.msg.thinkingContent,
)
const renderedThinking = computed(() =>
  renderMarkdown(props.msg.thinkingContent || ''),
)

// streaming 过程中展开，答案完成后自动折叠
const thinkingExpanded = ref(true)
watch(
  () => props.msg.streaming,
  (streaming) => {
    if (streaming === false && props.msg.thinkingContent) {
      // 答案流式完成 → 自动折叠思考过程
      thinkingExpanded.value = false
    }
  },
)
function toggleThinking() {
  thinkingExpanded.value = !thinkingExpanded.value
}

const createdAt = computed(() => {
  const raw = props.msg.created_at
  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return raw
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
})

const hasCitations = computed(() => (props.msg.citations?.length || 0) > 0)

/* ---------------------- 流式计时器 ---------------------- */
// 起点锚定到消息的 created_at（assistant msg 一创建就写了 ISO 时间），
// 这样切走再切回来重新挂载时，elapsed 依然相对于"提问那一刻"，不会重置。
const elapsedMs = ref(0)
let timerId: ReturnType<typeof setInterval> | null = null

function resolveStartedAt(): number {
  const raw = props.msg.created_at
  if (raw) {
    const t = new Date(raw).getTime()
    if (!Number.isNaN(t)) return t
  }
  return Date.now()
}

function tick(startedAt: number) {
  // 保证非负（防止 created_at 是未来时间导致初始显示 "-0.1s"）
  elapsedMs.value = Math.max(0, Date.now() - startedAt)
}

function startTimer() {
  if (timerId) return
  const startedAt = resolveStartedAt()
  tick(startedAt)
  timerId = setInterval(() => tick(startedAt), 100)
}

function stopTimer() {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

watch(
  () => props.msg.role === 'assistant' && !!props.msg.streaming,
  (active) => {
    if (active) startTimer()
    else stopTimer()
  },
  { immediate: true },
)

onBeforeUnmount(stopTimer)

const elapsedLabel = computed(() => {
  // 小于 10s 保留 1 位小数；更长直接展示整秒，读起来更稳
  const s = elapsedMs.value / 1000
  return s < 10 ? `${s.toFixed(1)}s` : `${Math.floor(s)}s`
})

const showStreamTimer = computed(
  () => props.msg.role === 'assistant' && !!props.msg.streaming,
)
</script>

<template>
  <div :class="['message-row', msg.role, { 'message-row--deleting': deleting }]">
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
      <!-- 流式计时器（仅 assistant 且流式中可见，答案完成即消失） -->
      <div v-if="showStreamTimer" class="stream-timer" role="status" aria-live="polite">
        <NIcon :size="12" class="stream-timer__icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15 1H9v2h6V1zm-4 13h2V8h-2v6zm8.03-6.61l1.42-1.42c-.43-.51-.9-.99-1.41-1.41l-1.42 1.42C16.07 4.74 14.12 4 12 4c-4.97 0-9 4.03-9 9s4.02 9 9 9 9-4.03 9-9c0-2.12-.74-4.07-1.97-5.61zM12 20c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" />
          </svg>
        </NIcon>
        <span class="stream-timer__label">思考中</span>
        <span class="stream-timer__dot">·</span>
        <span class="stream-timer__time">{{ elapsedLabel }}</span>
      </div>

      <!-- 证据阅读（thinking）折叠卡片 -->
      <div v-if="hasThinking" class="thinking-block">
        <button class="thinking-header" @click="toggleThinking">
          <NIcon :size="13" class="thinking-icon" :class="{ 'thinking-icon--spin': msg.streaming }">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          </NIcon>
          <span class="thinking-title">
            {{ msg.streaming ? '正在阅读证据…' : '已阅读证据' }}
          </span>
          <NIcon :size="12" class="thinking-toggle" :class="{ 'thinking-toggle--open': thinkingExpanded }">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
            </svg>
          </NIcon>
        </button>
        <Transition name="thinking-slide">
          <div v-show="thinkingExpanded" class="thinking-content markdown-body" v-html="renderedThinking" />
        </Transition>
      </div>

      <!-- 流式且尚未产出内容：保留三点 typing 气泡 -->
      <div
        v-if="msg.role === 'assistant' && msg.streaming && !msg.content"
        class="typing-indicator"
      >
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
      <div v-else class="message-bubble">
        <!-- user 保持纯文本，assistant 用 markdown -->
        <pre v-if="msg.role === 'user'" class="message-text">{{ msg.content }}</pre>
        <div v-else class="markdown-body" v-html="rendered"></div>
      </div>

      <!-- 引用资料（仅 assistant 有） -->
      <div v-if="hasCitations" class="citations-block">
        <NCollapse :default-expanded-names="[]" arrow-placement="right">
          <NCollapseItem name="citations">
            <template #header>
              <span class="citations-title">
                <NIcon :size="14" class="citations-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 18H6V4h7v5h5v11z" />
                  </svg>
                </NIcon>
                引用资料 · {{ msg.citations.length }} 条
              </span>
            </template>
            <ul class="citation-list">
              <li
                v-for="(c, i) in msg.citations"
                :key="`${c.file_id}-${c.chunk_index}-${i}`"
                class="citation-item"
              >
                <div class="citation-head">
                  <NTag :bordered="false" size="small" type="info" class="citation-index">
                    #{{ i + 1 }}
                  </NTag>
                  <NEllipsis class="citation-name">{{ c.file_name }}</NEllipsis>
                  <span class="citation-score">score {{ c.score.toFixed(2) }}</span>
                </div>
                <div class="citation-snippet">{{ c.snippet }}</div>
              </li>
            </ul>
          </NCollapseItem>
        </NCollapse>
      </div>

      <div class="message-time">{{ createdAt }}</div>

      <!-- 删除按钮：悬浮时出现，点击二次确认后执行 -->
      <NPopconfirm
        v-if="!msg.streaming"
        positive-text="删除"
        negative-text="取消"
        @positive-click="emit('delete', msg.id)"
      >
        <template #trigger>
          <button
            class="msg-delete-btn"
            title="删除消息"
            :disabled="deleting"
          >
            <NIcon :size="13">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
            </NIcon>
          </button>
        </template>
        确定删除这条消息？
      </NPopconfirm>
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

.message-row.assistant .message-body {
  /* assistant 消息附带 markdown 正文 + 引用卡片，给更宽的显示空间 */
  max-width: 82%;
  flex: 1 1 auto;
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

/* 流式计时器 chip：浮在气泡上方，保持克制、和主蓝配色一致 */
.stream-timer {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 6px 2px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11.5px;
  line-height: 1.4;
  color: @primary-blue;
  background: fade(@primary-blue, 10%);
  border: 1px solid fade(@primary-blue, 18%);
  font-variant-numeric: tabular-nums;
  /* 轻微淡入，避免突然出现 */
  animation: streamTimerFadeIn 0.2s ease-out;
}

.stream-timer__icon {
  color: @primary-blue;
  display: inline-flex;
  animation: streamTimerSpin 2.4s linear infinite;
}

.stream-timer__label {
  font-weight: 500;
}

.stream-timer__dot {
  color: fade(@primary-blue, 45%);
}

.stream-timer__time {
  font-weight: 600;
  min-width: 34px;
  text-align: left;
}

@keyframes streamTimerFadeIn {
  from { opacity: 0; transform: translateY(-2px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes streamTimerSpin {
  to { transform: rotate(360deg); }
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

/* 证据阅读（thinking）卡片 */
.thinking-block {
  margin-bottom: 8px;
  border: 1px solid @border-color;
  border-radius: @border-radius-md;
  background: @bg-color;
  overflow: hidden;
  font-size: 13px;
}

.thinking-header {
  all: unset;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  color: @text-secondary;
  user-select: none;

  &:hover {
    background: fade(@primary-blue, 5%);
  }
}

.thinking-icon {
  color: @primary-blue;
  flex-shrink: 0;

  &--spin {
    animation: streamTimerSpin 2.4s linear infinite;
  }
}

.thinking-title {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  color: @text-secondary;
}

.thinking-toggle {
  color: @text-placeholder;
  transition: transform 0.2s ease;
  flex-shrink: 0;

  &--open {
    transform: rotate(180deg);
  }
}

.thinking-content {
  padding: 10px 14px 12px;
  border-top: 1px solid @border-color;
  font-size: 12.5px;
  color: @text-secondary;
  max-height: 320px;
  overflow-y: auto;
}

.thinking-slide-enter-active,
.thinking-slide-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  max-height: 320px;
  overflow: hidden;
}
.thinking-slide-enter-from,
.thinking-slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.citations-block {
  margin-top: 8px;
  padding: 0 14px;
  background: @bg-white;
  border: 1px solid fade(@primary-blue, 15%);
  border-radius: @border-radius-md;
  font-size: 13px;
  overflow: hidden;

  :deep(.n-collapse) {
    --n-title-padding: 0 !important;
  }
  :deep(.n-collapse-item) {
    margin: 0 !important;
    border: none !important;
  }
  :deep(.n-collapse-item__header) {
    padding: 8px 0 !important;
  }
  :deep(.n-collapse-item__header-main) {
    font-size: 12px;
    font-weight: 500;
    color: @primary-blue;
  }
  :deep(.n-collapse-item__content-inner) {
    padding: 0 0 12px !important;
  }
  :deep(.n-collapse-item__content-wrapper) {
    padding-top: 0 !important;
  }
}

.citations-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.citations-icon {
  color: @primary-blue;
}

.citation-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-item {
  padding: 10px 12px;
  background: @bg-color;
  border-radius: @border-radius-sm;
  min-width: 0;
}

.citation-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  min-width: 0;
}

.citation-index {
  flex-shrink: 0;
  font-weight: 600;
}

.citation-name {
  flex: 1;
  min-width: 0;
  color: @text-primary;
  font-weight: 500;
  font-size: 13px;
}

.citation-score {
  flex-shrink: 0;
  color: @text-placeholder;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.citation-snippet {
  color: @text-secondary;
  font-size: 12px;
  line-height: 1.6;
  max-height: 4.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  /* 纯数字/CSV 等长串内容也能换行，避免撑破容器 */
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

/* 删除按钮 */
.message-body {
  position: relative;
}

.msg-delete-btn {
  all: unset;
  position: absolute;
  bottom: 22px;
  right: -32px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: @text-placeholder;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;

  &:hover {
    color: #ef4444;
    background: fade(#ef4444, 10%);
  }

  &:disabled {
    cursor: not-allowed;
    color: @text-placeholder;
  }
}

/* user 气泡：按钮放左侧 */
.message-row.user .msg-delete-btn {
  right: auto;
  left: -32px;
}

/* 悬浮整行时显示删除按钮 */
.message-row:hover .msg-delete-btn {
  opacity: 1;
}

/* 删除消失动效：缩小 + 淡出 */
.message-row--deleting {
  animation: msgDeleteOut 0.3s ease forwards;
  pointer-events: none;
}

@keyframes msgDeleteOut {
  0%   { opacity: 1; transform: scaleY(1) translateX(0); max-height: 200px; }
  40%  { opacity: 0.5; transform: scaleY(0.8) translateX(0); }
  100% { opacity: 0; transform: scaleY(0); max-height: 0; margin: 0; overflow: hidden; }
}
</style>

<!-- 非 scoped：给 v-html 注入的 markdown 内容使用 -->
<style lang="less">
.markdown-body {
  font-size: 14px;
  line-height: 1.75;
  color: @text-primary;
  word-wrap: break-word;

  p { margin: 0 0 8px; }
  p:last-child { margin-bottom: 0; }

  h1, h2, h3, h4, h5, h6 {
    margin: 16px 0 8px;
    font-weight: 600;
    line-height: 1.3;
  }
  h1 { font-size: 20px; }
  h2 { font-size: 18px; }
  h3 { font-size: 16px; }
  h4, h5, h6 { font-size: 14px; }

  ul, ol {
    margin: 0 0 8px;
    padding-left: 20px;
  }
  li { margin: 2px 0; }

  blockquote {
    margin: 8px 0;
    padding: 4px 12px;
    border-left: 3px solid @primary-blue;
    background: rgba(33, 150, 243, 0.06);
    color: @text-secondary;
    border-radius: 0 @border-radius-sm @border-radius-sm 0;
  }

  code {
    padding: 2px 6px;
    margin: 0 2px;
    border-radius: 4px;
    background: rgba(135, 131, 120, 0.15);
    color: #eb5757;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
  }

  pre {
    margin: 8px 0;
    padding: 12px 14px;
    border-radius: @border-radius-sm;
    overflow-x: auto;
    background: #282c34;
    color: #abb2bf;
    font-size: 13px;
    line-height: 1.6;

    code {
      padding: 0;
      margin: 0;
      background: transparent;
      color: inherit;
      font-size: inherit;
    }
  }

  table {
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 13px;

    th, td {
      border: 1px solid @border-color;
      padding: 6px 10px;
    }
    th {
      background: @bg-color;
      font-weight: 600;
    }
  }

  a {
    color: @primary-blue;
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }

  hr {
    margin: 12px 0;
    border: 0;
    border-top: 1px solid @border-color;
  }
}
</style>
