import request from '@/utils/request'

export interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

export function getChatSessions() {
  return request.get<ChatSession[]>('/chat/sessions')
}

export function createChatSession() {
  return request.post<ChatSession>('/chat/sessions')
}

export function deleteChatSession(id: string) {
  return request.delete(`/chat/sessions/${id}`)
}

export function getChatMessages(sessionId: string) {
  return request.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
}

export function sendMessage(sessionId: string, content: string) {
  return request.post<ChatMessage>(`/chat/sessions/${sessionId}/messages`, { content })
}
