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
 *        GET    /knowledge/folders?kb_id=                        -> listFolders
 *        POST   /knowledge/folders                                   -> createFolder
 *        PATCH  /knowledge/folders/:id   { name }                    -> renameFolder
 *        DELETE /knowledge/folders/:id                               -> deleteFolder
 *        GET    /knowledge/files                                     -> listFiles
 *          (query: kb_id, folder_id, keyword, page, pageSize)
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
  Knowledgekb_id,
  KnowledgeQueryParams,
  PagedResult,
  UploadPayload,
  KnowledgeFolderCreateSchema,
  KnowledgeFolderUpdateSchema,
  KnowledgeFolderDeleteSchema,
} from '@/types/knowledge'
import request from '@/utils/request'

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
  { id: 'fd_demo_ops', kb_id: 'personal', name: '运维手册' },
  { id: 'fd_demo_prod', kb_id: 'personal', name: '产品文档' },
  { id: 'fd_demo_team', kb_id: 'shared', name: '团队规范' },
]

let mockFiles: KnowledgeFile[] = [
  {
    id: 'fl_demo_readme',
    kb_id: 'personal',
    folder_id: null,
    file_name: '欢迎.md',
    file_ext: 'md',
    mime_type: 'text/markdown',
    file_size: 120,
    created_at: nowIso(),
    parse_status: 'pending',
  },
  {
    id: 'fl_demo_note',
    kb_id: 'personal',
    folder_id: 'fd_demo_ops',
    file_name: '值班记录.txt',
    file_ext: 'txt',
    mime_type: 'text/plain',
    file_size: 512,
    created_at: nowIso(),
    parse_status: 'pending',
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

/** 获取知识库列表 */
export async function listLibraries(): Promise<KnowledgeLibrary[]> {
  const res = await request.get<{ code: number; message: string; data: KnowledgeLibrary[] }>('/knowledge/list')
  return res.data
}

/** 获取某个知识库下的文件夹（单层） */
export async function listFolders(
  kb_id: Knowledgekb_id,
): Promise<KnowledgeFolder[]> {
  // 真实实现: return request.get<KnowledgeFolder[]>('/knowledge/folders', { params: { kb_id } })
  const res = await request.get<{ code: number; message: string; data: KnowledgeFolder[] }>('/knowledge/folder/list', { params: { kb_id: kb_id } })
  return res.data
}

/** 新建文件夹 */
export async function createFolder(
  kb_id: Knowledgekb_id,
  name: string,
): Promise<KnowledgeFolder> {
  // 真实实现: return request.post<KnowledgeFolder>('/knowledge/folders', { kb_id, name })

  const trimmed = name.trim()
  if (!trimmed) throw new Error('文件夹名称不能为空')
  if (mockFolders.some((f) => f.kb_id === kb_id && f.name === trimmed)) {
    throw new Error('同一知识库下已存在同名文件夹')
  }
  const folder: KnowledgeFolderCreateSchema = { kb_id: kb_id, name: trimmed }
  const res = await request.post<{ data: KnowledgeFolder }>('/knowledge/folder/create', folder)
  return res.data
}

/** 重命名文件夹 */
export async function renameFolder(
  folder_id: string,
  name: string,
): Promise<KnowledgeFolder> {
  // 真实实现: return request.patch<KnowledgeFolder>(`/knowledge/folders/${folder_id}`, { name }
  const trimmed = name.trim()
  if (!trimmed) throw new Error('文件夹名称不能为空')
  const updated: KnowledgeFolderUpdateSchema = { id: folder_id, name: trimmed }
  const res = await request.put<{ data: KnowledgeFolder }>('/knowledge/folder/update', updated)
  return res.data
}

/** 删除文件夹（同时删除其中所有文件，真实后端按约定调整） */
export async function deleteFolder(folder_id: string, kb_id: Knowledgekb_id): Promise<KnowledgeFolder> {
  // 使用body传递参数
  const body: KnowledgeFolderDeleteSchema = { folder_id: folder_id, kb_id: kb_id }
  const res = await request.delete<{ data: KnowledgeFolder }>('/knowledge/folder/delete', { data: body })
  return res.data
}

/** 获取文件列表（支持搜索 + 分页） */
export async function listFiles(
  params: KnowledgeQueryParams,
): Promise<PagedResult<KnowledgeFile>> {
  // 真实实现: return request.get<PagedResult<KnowledgeFile>>('/knowledge/files', { params })
  const res = await request.get<{ code: number; message: string; data: PagedResult<KnowledgeFile> }>('/knowledge/files/list', { params })
  return res.data
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
    : target.file_ext
      ? `${trimmed}.${target.file_ext}`
      : trimmed
  const finalExt = extFromName(finalName) || target.file_ext

  // 同目录下重名校验
  if (
    mockFiles.some(
      (f) =>
        f.id !== fileId &&
        f.kb_id === target.kb_id &&
        f.folder_id === target.folder_id &&
        f.file_name === finalName,
    )
  ) {
    throw new Error('当前目录下已存在同名文件')
  }

  const updated: KnowledgeFile = {
    ...target,
    file_name: finalName,
    file_ext: finalExt,
    created_at: nowIso(),
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
  console.log(files);

  // 真实实现示例：
  const form = new FormData()
  form.append('kb_id', payload.kb_id)
  if (payload.folder_id) form.append('folder_id', payload.folder_id)
  files.forEach(f => form.append('files', f))
  const res = await request.post<{ data: KnowledgeFile[] }>('/knowledge/files/upload', form)
  return res.data
  // await mockDelay(320)
  // const created: KnowledgeFile[] = []
  // for (const file of files) {
  //   const id = randomId('fl')
  //   const record: KnowledgeFile = {
  //     id,
  //     kb_id: payload.kb_id,
  //     folder_id: payload.folder_id,
  //     name: file.name,
  //     extension: extFromFile(file),
  //     mimeType: file.type || 'application/octet-stream',
  //     sizeBytes: file.size,
  //     updatedAt: nowIso(),
  //   }
  //   mockBlobStore.set(id, file)
  //   mockFiles = [record, ...mockFiles]
  //   created.push(record)
  // }
  // return created
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
