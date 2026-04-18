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

export interface KnowledgeFolderDeleteSchema {
  kb_id: Knowledgekb_id
  folder_id: string
}

export interface KnowledgeFolderCreateSchema {
  kb_id: Knowledgekb_id
  name: string
}

/** 更新文件（重命名 / 移动） */
export interface KnowledgeFileUpdateSchema {
  id: string
  file_name?: string
  folder_id?: string
  move_to_root?: boolean
}
/** 文件元信息 */
export interface KnowledgeFile {
  id: string
  kb_id: Knowledgekb_id
  /** null 表示挂在知识库根目录（未归入任何文件夹） */
  folder_id: string | null
  file_name: string
  /** 小写扩展名，含点，例如 md、xlsx、png */
  file_ext: string
  mime_type: string
  file_size: number
  created_at: string
  parse_status: 'pending' | 'processing' | 'success' | 'failed'
}
// 
/** 文件列表查询参数（搜索 + 分页） */
export interface KnowledgeQueryParams {
  kb_id: Knowledgekb_id
  folder_id: string | null
  keyword: string
  page: number
  page_size: number
}

/** 上传目标：归属哪个知识库 + 可选文件夹 */
export interface UploadPayload {
  kb_id: Knowledgekb_id
  folder_id: string | null
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
  items: T[]
  total: number
}

/** Excel 工作簿单个 sheet 的预览片段
 *
 * 不再用 sheet_to_html 生成大段 DOM（几万行会把浏览器卡死），
 * 改成二维数组交给 NDataTable 做虚拟滚动。
 */
export interface PreviewSheet {
  name: string
  /** 表头显示名（允许同名，key 在渲染侧用列下标保证唯一） */
  columns: string[]
  /** 数据行；每行数组长度固定 = columns.length，已按列对齐好 */
  rows: string[][]
  /** 空 sheet / 解析失败等无法表格化时的占位提示（优先级高于 columns/rows） */
  placeholder?: string
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
  /** mammoth / sheet_to_html 生成的 HTML（word / 单 sheet 的退路） */
  htmlContent?: string
  /** Excel 多 sheet 列表 */
  sheets?: PreviewSheet[]
  /** 当前选中的 sheet 名 */
  activeSheetName?: string
  /** 错误 / 不支持的提示 */
  errorMessage?: string
}
