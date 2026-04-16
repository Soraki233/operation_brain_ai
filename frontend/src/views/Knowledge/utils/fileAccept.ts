/**
 * 上传文件类型白名单（前端二次校验；后端仍需做权威校验）
 *
 * 业务要求支持：markdown / excel / txt / 图片 / word
 */

export const KNOWLEDGE_ACCEPT_EXTS = [
  '.md',
  '.markdown',
  '.txt',
  '.csv',
  '.xls',
  '.xlsx',
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.webp',
  '.doc',
  '.docx',
] as const

export const KNOWLEDGE_ACCEPT_MIMES = [
  'text/markdown',
  'text/plain',
  'text/csv',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
] as const

/** NUpload accept 属性值 */
export const KNOWLEDGE_UPLOAD_ACCEPT = KNOWLEDGE_ACCEPT_EXTS.join(',')

/** 取小写扩展名（不含点） */
export function getExtensionLower(filename: string): string {
  const i = filename.lastIndexOf('.')
  if (i <= 0 || i === filename.length - 1) return ''
  return filename.slice(i + 1).toLowerCase()
}

/** 是否属于允许上传的文件类型 */
export function isAllowedKnowledgeFile(file: File): boolean {
  const ext = `.${getExtensionLower(file.name)}`
  if ((KNOWLEDGE_ACCEPT_EXTS as readonly string[]).includes(ext)) return true
  if (file.type && (KNOWLEDGE_ACCEPT_MIMES as readonly string[]).includes(file.type)) {
    return true
  }
  return false
}
