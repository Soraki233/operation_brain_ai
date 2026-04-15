import request from '@/utils/request'

export interface KnowledgeFile {
  id: string
  name: string
  type: string
  size: number
  uploadedAt: string
  status: 'processing' | 'ready' | 'failed'
}

export function getKnowledgeFiles() {
  return request.get<KnowledgeFile[]>('/knowledge/files')
}

export function uploadKnowledgeFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/knowledge/files', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteKnowledgeFile(id: string) {
  return request.delete(`/knowledge/files/${id}`)
}

export function previewKnowledgeFile(id: string) {
  return request.get<{ content: string; contentType: string }>(`/knowledge/files/${id}/preview`)
}
