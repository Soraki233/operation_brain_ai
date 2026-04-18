/**
 * 知识库 API 封装
 *
 * 对接后端接口：
 *   GET    /knowledge/list                                       -> listLibraries
 *   GET    /knowledge/folder/list?kb_id=                         -> listFolders
 *   POST   /knowledge/folder/create                              -> createFolder
 *   PUT    /knowledge/folder/update                              -> renameFolder
 *   DELETE /knowledge/folder/delete  (body)                      -> deleteFolder
 *   GET    /knowledge/files/list   (query)                       -> listFiles
 *   PUT    /knowledge/files/update (body)                        -> renameFile / moveFile
 *   DELETE /knowledge/files/:id                                  -> deleteFile  (mock)
 *   POST   /knowledge/files/upload (multipart/form-data)         -> uploadFiles
 *   GET    /knowledge/files/:id/preview (responseType: blob)     -> getFilePreviewBlob
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
  KnowledgeFileUpdateSchema,
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

/**
 * 重命名文件
 *
 * 规则（后端同样会校验）：
 * - 文件名非空；未带扩展名时后端自动拼回原扩展名。
 * - 同一知识库 + 文件夹下的文件名必须唯一。
 */
export async function renameFile(
  fileId: string,
  name: string,
): Promise<KnowledgeFile> {
  const body: KnowledgeFileUpdateSchema = { id: fileId, file_name: name.trim() }
  const res = await request.put<{ data: KnowledgeFile }>(
    '/knowledge/files/update',
    body,
  )
  return res.data
}

/**
 * 移动文件
 *
 * - folder_id 为 null 表示移动到知识库根目录（后端走 move_to_root=true 分支）。
 * - 只允许在同一知识库内移动；目标文件夹由后端做二次校验。
 */
export async function moveFile(
  fileId: string,
  folder_id: string | null,
): Promise<KnowledgeFile> {
  const body: KnowledgeFileUpdateSchema = folder_id
    ? { id: fileId, folder_id }
    : { id: fileId, move_to_root: true }
  const res = await request.put<{ data: KnowledgeFile }>(
    '/knowledge/files/update',
    body,
  )
  return res.data
}

/** 删除文件 */
export async function deleteFile(fileId: string): Promise<void> {
  // 真实实现: return request.delete(`/knowledge/files/${fileId}`)
  await mockDelay(180)
  if (!mockFiles.some((f) => f.id === fileId)) throw new Error('文件不存在')
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

/** 获取文件二进制（用于预览，后端直接返回 FileResponse） */
export async function getFilePreviewBlob(fileId: string): Promise<Blob> {
  return request.get<Blob>(`/knowledge/files/${fileId}/preview`, {
    responseType: 'blob',
  })
}
