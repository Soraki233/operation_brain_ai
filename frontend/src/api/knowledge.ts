/**
 * 知识库 API 封装
 *
 * ============================================================================
 * 【当前为 MOCK 实现】
 *   - 数据保存在内存（刷新页面会重置）。
 *   - 通过 mockDelay 模拟网络延迟，方便观察 loading 态。
 *
 * 【替换为真实后端时】
 *   1) 删除下方 mock 存储与 mockDelay，改用项目统一 HTTP 封装：
 *        import request from '@/utils/request'
 *   2) 建议接口（可按后端实际调整）：
 *        GET    /knowledge/libraries                                 -> listLibraries
 *        GET    /knowledge/folders?libraryId=                        -> listFolders
 *        POST   /knowledge/folders                                   -> createFolder
 *        PATCH  /knowledge/folders/:id   { name }                    -> renameFolder
 *        DELETE /knowledge/folders/:id                               -> deleteFolder
 *        GET    /knowledge/files                                     -> listFiles
 *          (query: libraryId, folderId, keyword, page, pageSize)
 *        PATCH  /knowledge/files/:id     { name }                    -> renameFile
 *        DELETE /knowledge/files/:id                                 -> deleteFile
 *        POST   /knowledge/files/upload  (multipart/form-data)       -> uploadFiles
 *        GET    /knowledge/files/:id/preview (responseType: blob)    -> getFilePreviewBlob
 *   3) 保持本文件对外的函数签名不变，上层页面/组件无需修改。
 * ============================================================================
 */

import type {
  KnowledgeFile,
  KnowledgeFolder,
  KnowledgeLibrary,
  KnowledgeLibraryId,
  KnowledgeQueryParams,
  PagedResult,
  UploadPayload,
} from '@/types/knowledge'

/** 模拟网络延迟 */
function mockDelay(ms = 260) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}

function nowIso() {
  return new Date().toISOString()
}

function randomId(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`
}

/* --------------------------------- Mock 数据 --------------------------------- */

const libraries: KnowledgeLibrary[] = [
  { id: 'personal', name: '个人知识库', fixed: true },
  { id: 'shared', name: '共享知识库', fixed: true },
]

let mockFolders: KnowledgeFolder[] = [
  { id: 'fd_demo_ops', libraryId: 'personal', name: '运维手册', createdAt: nowIso() },
  { id: 'fd_demo_prod', libraryId: 'personal', name: '产品文档', createdAt: nowIso() },
  { id: 'fd_demo_team', libraryId: 'shared', name: '团队规范', createdAt: nowIso() },
]

let mockFiles: KnowledgeFile[] = [
  {
    id: 'fl_demo_readme',
    libraryId: 'personal',
    folderId: null,
    name: '欢迎.md',
    extension: 'md',
    mimeType: 'text/markdown',
    sizeBytes: 120,
    updatedAt: nowIso(),
  },
  {
    id: 'fl_demo_note',
    libraryId: 'personal',
    folderId: 'fd_demo_ops',
    name: '值班记录.txt',
    extension: 'txt',
    mimeType: 'text/plain',
    sizeBytes: 512,
    updatedAt: nowIso(),
  },
]

/** Mock 文件二进制缓存（真实后端走下载接口即可） */
const mockBlobStore = new Map<string, Blob>()

function seedBlobForFile(file: KnowledgeFile, content: string, mime: string) {
  mockBlobStore.set(file.id, new Blob([content], { type: mime }))
}

seedBlobForFile(
  mockFiles[0],
  '# 欢迎使用知识库\n\n这是一个 **mock** 示例 Markdown 文件。\n\n- 支持图片 / txt / md / excel / word 预览\n- 支持搜索与分页\n',
  'text/markdown',
)
seedBlobForFile(
  mockFiles[1],
  '示例文本内容：\n1. 检查网络连通性\n2. 重启相关服务\n3. 记录处理过程\n',
  'text/plain',
)

/* --------------------------------- API 封装 --------------------------------- */

/** 获取知识库列表（固定两项） */
export async function listLibraries(): Promise<KnowledgeLibrary[]> {
  // 真实实现: return request.get<KnowledgeLibrary[]>('/knowledge/libraries')
  await mockDelay(120)
  return [...libraries]
}

/** 获取某个知识库下的文件夹（单层） */
export async function listFolders(
  libraryId: KnowledgeLibraryId,
): Promise<KnowledgeFolder[]> {
  // 真实实现: return request.get<KnowledgeFolder[]>('/knowledge/folders', { params: { libraryId } })
  await mockDelay(160)
  return mockFolders
    .filter((f) => f.libraryId === libraryId)
    .sort((a, b) => a.name.localeCompare(b.name))
}

/** 新建文件夹 */
export async function createFolder(
  libraryId: KnowledgeLibraryId,
  name: string,
): Promise<KnowledgeFolder> {
  // 真实实现: return request.post<KnowledgeFolder>('/knowledge/folders', { libraryId, name })
  await mockDelay(200)
  const trimmed = name.trim()
  if (!trimmed) throw new Error('文件夹名称不能为空')
  if (mockFolders.some((f) => f.libraryId === libraryId && f.name === trimmed)) {
    throw new Error('同一知识库下已存在同名文件夹')
  }
  const folder: KnowledgeFolder = {
    id: randomId('fd'),
    libraryId,
    name: trimmed,
    createdAt: nowIso(),
  }
  mockFolders = [...mockFolders, folder]
  return folder
}

/** 重命名文件夹 */
export async function renameFolder(
  folderId: string,
  name: string,
): Promise<KnowledgeFolder> {
  // 真实实现: return request.patch<KnowledgeFolder>(`/knowledge/folders/${folderId}`, { name })
  await mockDelay(200)
  const trimmed = name.trim()
  if (!trimmed) throw new Error('文件夹名称不能为空')

  const target = mockFolders.find((f) => f.id === folderId)
  if (!target) throw new Error('文件夹不存在')

  // 同库下重名校验（排除自身）
  if (
    mockFolders.some(
      (f) =>
        f.id !== folderId &&
        f.libraryId === target.libraryId &&
        f.name === trimmed,
    )
  ) {
    throw new Error('同一知识库下已存在同名文件夹')
  }

  const updated: KnowledgeFolder = { ...target, name: trimmed }
  mockFolders = mockFolders.map((f) => (f.id === folderId ? updated : f))
  return updated
}

/** 删除文件夹（同时删除其中所有文件，真实后端按约定调整） */
export async function deleteFolder(folderId: string): Promise<void> {
  // 真实实现: return request.delete(`/knowledge/folders/${folderId}`)
  await mockDelay(200)
  if (!mockFolders.some((f) => f.id === folderId)) {
    throw new Error('文件夹不存在')
  }
  mockFolders = mockFolders.filter((f) => f.id !== folderId)
  const gone = mockFiles.filter((f) => f.folderId === folderId)
  gone.forEach((f) => mockBlobStore.delete(f.id))
  mockFiles = mockFiles.filter((f) => f.folderId !== folderId)
}

/** 获取文件列表（支持搜索 + 分页） */
export async function listFiles(
  params: KnowledgeQueryParams,
): Promise<PagedResult<KnowledgeFile>> {
  // 真实实现: return request.get<PagedResult<KnowledgeFile>>('/knowledge/files', { params })
  await mockDelay(200)
  const kw = params.keyword.trim().toLowerCase()
  let list = mockFiles.filter(
    (f) =>
      f.libraryId === params.libraryId &&
      (params.folderId === null
        ? f.folderId === null
        : f.folderId === params.folderId),
  )
  if (kw) list = list.filter((f) => f.name.toLowerCase().includes(kw))
  list = [...list].sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1))
  const total = list.length
  const start = (params.page - 1) * params.pageSize
  return { list: list.slice(start, start + params.pageSize), total }
}

/** 根据文件名推断扩展名（小写，不含点） */
function extFromName(name: string): string {
  const i = name.lastIndexOf('.')
  return i <= 0 || i === name.length - 1 ? '' : name.slice(i + 1).toLowerCase()
}

/**
 * 重命名文件
 *
 * 规则：
 * - 用户传入完整新文件名（可包含扩展名），内部重新推断 extension。
 * - 若未包含扩展名，则沿用原扩展名（避免用户误删后缀）。
 * - 同一 library + folder 下的文件名必须唯一。
 */
export async function renameFile(
  fileId: string,
  name: string,
): Promise<KnowledgeFile> {
  // 真实实现: return request.patch<KnowledgeFile>(`/knowledge/files/${fileId}`, { name })
  await mockDelay(200)
  const trimmed = name.trim()
  if (!trimmed) throw new Error('文件名不能为空')

  const target = mockFiles.find((f) => f.id === fileId)
  if (!target) throw new Error('文件不存在')

  // 如果用户没写扩展名，自动补回原扩展名
  const hasExt = trimmed.includes('.')
  const finalName = hasExt
    ? trimmed
    : target.extension
      ? `${trimmed}.${target.extension}`
      : trimmed
  const finalExt = extFromName(finalName) || target.extension

  // 同目录下重名校验
  if (
    mockFiles.some(
      (f) =>
        f.id !== fileId &&
        f.libraryId === target.libraryId &&
        f.folderId === target.folderId &&
        f.name === finalName,
    )
  ) {
    throw new Error('当前目录下已存在同名文件')
  }

  const updated: KnowledgeFile = {
    ...target,
    name: finalName,
    extension: finalExt,
    updatedAt: nowIso(),
  }
  mockFiles = mockFiles.map((f) => (f.id === fileId ? updated : f))
  return updated
}

/** 删除文件 */
export async function deleteFile(fileId: string): Promise<void> {
  // 真实实现: return request.delete(`/knowledge/files/${fileId}`)
  await mockDelay(180)
  if (!mockFiles.some((f) => f.id === fileId)) throw new Error('文件不存在')
  mockBlobStore.delete(fileId)
  mockFiles = mockFiles.filter((f) => f.id !== fileId)
}

function extFromFile(file: File): string {
  const i = file.name.lastIndexOf('.')
  return i <= 0 ? '' : file.name.slice(i + 1).toLowerCase()
}

/** 上传文件（多文件） */
export async function uploadFiles(
  payload: UploadPayload,
  files: File[],
): Promise<KnowledgeFile[]> {
  // 真实实现示例：
  //   const form = new FormData()
  //   form.append('libraryId', payload.libraryId)
  //   if (payload.folderId) form.append('folderId', payload.folderId)
  //   files.forEach(f => form.append('files', f))
  //   return request.post('/knowledge/files/upload', form)
  await mockDelay(320)
  const created: KnowledgeFile[] = []
  for (const file of files) {
    const id = randomId('fl')
    const record: KnowledgeFile = {
      id,
      libraryId: payload.libraryId,
      folderId: payload.folderId,
      name: file.name,
      extension: extFromFile(file),
      mimeType: file.type || 'application/octet-stream',
      sizeBytes: file.size,
      updatedAt: nowIso(),
    }
    mockBlobStore.set(id, file)
    mockFiles = [record, ...mockFiles]
    created.push(record)
  }
  return created
}

/** 获取文件二进制（用于预览，真实后端应以 blob 方式下载） */
export async function getFilePreviewBlob(fileId: string): Promise<Blob> {
  // 真实实现:
  //   return request.get<Blob>(`/knowledge/files/${fileId}/preview`, { responseType: 'blob' })
  await mockDelay(120)
  const blob = mockBlobStore.get(fileId)
  if (!blob) {
    return new Blob(['该文件暂无可用内容（mock 未写入二进制）。'], {
      type: 'text/plain;charset=utf-8',
    })
  }
  return blob
}
