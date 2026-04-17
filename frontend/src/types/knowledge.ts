/**
 * 知识库模块核心类型定义
 *
 * 设计原则：
 * 1. 前后端字段语义对齐，方便后续把 mock 层直接替换为真实接口。
 * 2. 所有页面 / 组件 / composable 的数据形态都以本文件为源。
 */

/** 固定知识库标识（当前业务只有个人/共享两种，后端可改成数字 ID） */
export type Knowledgekb_id = 'personal' | 'shared' | string

/** 知识库节点（当前业务为 2 个固定节点） */
export interface KnowledgeLibrary {
  id: Knowledgekb_id
  name: string
  /** 固定节点：前端不允许删除 */
  fixed: boolean
}

/** 文件夹（仅一层，不允许嵌套） */
export interface KnowledgeFolder {
  id: string
  kb_id: Knowledgekb_id
  name: string
}

export interface KnowledgeFolderUpdateSchema {
  id: string
  name: string
}

export interface KnowledgeFolderCreateSchema {
  kb_id: Knowledgekb_id
  name: string
}
/** 文件元信息 */
export interface KnowledgeFile {
  id: string
  kb_id: Knowledgekb_id
  /** null 表示挂在知识库根目录（未归入任何文件夹） */
  folderId: string | null
  name: string
  /** 小写扩展名，不含点，例如 md、xlsx、png */
  extension: string
  mimeType: string
  sizeBytes: number
  updatedAt: string
}

/** 文件列表查询参数（搜索 + 分页） */
export interface KnowledgeQueryParams {
  kb_id: Knowledgekb_id
  folderId: string | null
  keyword: string
  page: number
  pageSize: number
}

/** 上传目标：归属哪个知识库 + 可选文件夹 */
export interface UploadPayload {
  kb_id: Knowledgekb_id
  folderId: string | null
}

/** 前端预览分类（用于在预览组件里做条件渲染） */
export type FilePreviewType =
  | 'image'
  | 'text'
  | 'markdown'
  | 'excel'
  | 'word'
  | 'unsupported'

/** 通用分页结果 */
export interface PagedResult<T> {
  list: T[]
  total: number
}

/** 预览弹层状态 */
export interface KnowledgePreviewModel {
  visible: boolean
  loading: boolean
  file: KnowledgeFile | null
  previewType: FilePreviewType
  /** 图片 blob URL */
  imageUrl?: string
  /** txt / markdown 源文本 */
  textContent?: string
  /** mammoth / sheet_to_html 生成的 HTML */
  htmlContent?: string
  /** 错误 / 不支持的提示 */
  errorMessage?: string
}
