/**
 * 会话 + RAG 问答 API 封装
 *
 * 对接后端接口：
 *   POST   /chat/threads                              -> createThread
 *   GET    /chat/threads                              -> listThreads
 *   DELETE /chat/threads/:id                          -> deleteThread
 *   GET    /chat/threads/:id/messages                 -> listMessages
 *   POST   /chat/threads/:id/ask   (SSE text/event-stream) -> streamAsk
 */

import request from '@/utils/request'

/* --------------------------------- 类型 --------------------------------- */

export type ChatRole = 'user' | 'assistant' | 'system'

export interface ChatCitation {
  file_id: string
  file_name: string
  chunk_index: number
  score: number
  snippet: string
}

export interface ChatSession {
  id: string
  title: string
  summary: string | null
  message_count: number
  last_message_at: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  citations: ChatCitation[]
  created_at: string
  /** 前端流式输出标记，后端不返回 */
  streaming?: boolean
}

/* ------------------------------ 普通 CRUD ------------------------------ */

export async function listThreads(): Promise<ChatSession[]> {
  const res = await request.get<{ data: ChatSession[] }>('/chat/threads')
  return res.data
}

export async function createThread(title?: string): Promise<ChatSession> {
  const res = await request.post<{ data: ChatSession }>('/chat/threads', { title })
  return res.data
}

export async function deleteThread(threadId: string): Promise<ChatSession> {
  const res = await request.delete<{ data: ChatSession }>(`/chat/threads/${threadId}`)
  return res.data
}

export async function listMessages(threadId: string): Promise<ChatMessage[]> {
  const res = await request.get<{ data: ChatMessage[] }>(
    `/chat/threads/${threadId}/messages`,
  )
  return res.data
}

/* --------------------------------- SSE --------------------------------- */

export interface StreamAskCallbacks {
  onCitations?: (citations: ChatCitation[]) => void
  onToken?: (delta: string) => void
  onDone?: (payload: { message_id: string; title: string }) => void
  onError?: (message: string) => void
}

export interface StreamAskHandle {
  /** 主动取消当前流式请求 */
  abort: () => void
  /** 请求 Promise，resolve 时表示 done，reject 时表示 error 或取消 */
  done: Promise<void>
}

/**
 * 流式请求 RAG 问答。基于 fetch + ReadableStream 解析 SSE，
 * 与 axios 拦截器解耦以获得真正的增量下发能力。
 */
export function streamAsk(
  threadId: string,
  content: string,
  callbacks: StreamAskCallbacks = {},
  options?: { kb_ids?: string[] },
): StreamAskHandle {
  const controller = new AbortController()
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')

  const done = (async () => {
    let response: Response
    try {
      response = await fetch(`${baseURL}/chat/threads/${threadId}/ask`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          content,
          kb_ids: options?.kb_ids,
        }),
      })
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        callbacks.onError?.((err as Error).message || '网络错误')
      }
      throw err
    }

    if (!response.ok || !response.body) {
      let message = `请求失败(${response.status})`
      try {
        const data = await response.json()
        message = data?.message || data?.detail || message
      } catch {
        // ignore
      }
      callbacks.onError?.(message)
      throw new Error(message)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { value, done: streamDone } = await reader.read()
      if (streamDone) break
      buffer += decoder.decode(value, { stream: true })

      // SSE 以 \n\n 分隔事件帧；可能一次收到多帧
      let sepIndex = buffer.indexOf('\n\n')
      while (sepIndex !== -1) {
        const rawEvent = buffer.slice(0, sepIndex)
        buffer = buffer.slice(sepIndex + 2)
        dispatchEvent(rawEvent, callbacks)
        sepIndex = buffer.indexOf('\n\n')
      }
    }
  })()

  return {
    abort: () => controller.abort(),
    done,
  }
}

function dispatchEvent(rawEvent: string, callbacks: StreamAskCallbacks) {
  let eventName = 'message'
  const dataLines: string[] = []
  for (const line of rawEvent.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }
  if (dataLines.length === 0) return
  let data: any = null
  try {
    data = JSON.parse(dataLines.join('\n'))
  } catch {
    return
  }
  switch (eventName) {
    case 'citations':
      callbacks.onCitations?.(data.citations || [])
      break
    case 'token':
      if (typeof data.delta === 'string') callbacks.onToken?.(data.delta)
      break
    case 'done':
      callbacks.onDone?.({
        message_id: data.message_id,
        title: data.title,
      })
      break
    case 'error':
      callbacks.onError?.(data.message || '服务端异常')
      break
  }
}
