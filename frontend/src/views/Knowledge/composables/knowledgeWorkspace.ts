/**
 * 知识库工作区状态机
 *
 * 通过 provide / inject 在 Knowledge 页面范围内共享：
 *   - 当前选中的知识库 / 文件夹（基于 selectedTreeKey 派生）
 *   - 搜索关键词、分页参数
 *   - 文件列表 loading、上传中、预览弹窗、确认弹窗状态
 *   - 新建文件夹 / 上传 / 删除 等操作方法
 *
 * 子组件只通过 inject(KNOWLEDGE_WORKSPACE_KEY) 访问本工作区，不直连 API。
 */

import { computed, reactive, ref, watch } from 'vue'
import type { InjectionKey } from 'vue'
import { useMessage } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import * as knowledgeApi from '@/api/knowledge'
import type {
  KnowledgeFile,
  KnowledgeFolder,
  KnowledgeLibrary,
  Knowledgekb_id,
  KnowledgePreviewModel,
} from '@/types/knowledge'
import { formatBytes } from '../utils/formatBytes'
import {
  buildPreviewFromBlob,
  inferPreviewType,
  revokeIfObjectUrl,
} from '../utils/filePreview'

/** InjectionKey：由 Knowledge.vue 提供 */
export const KNOWLEDGE_WORKSPACE_KEY: InjectionKey<
  ReturnType<typeof createKnowledgeWorkspace>
> = Symbol('KnowledgeWorkspace')

/** 工作区工厂 */
export function createKnowledgeWorkspace() {
  const message = useMessage()

  /* ---------------------------------- 基础数据 ---------------------------------- */

  const libraries = ref<KnowledgeLibrary[]>([])
  const folders = ref<KnowledgeFolder[]>([])
  const files = ref<KnowledgeFile[]>([])
  const total = ref(0)

  /**
   * 当前选中的树节点 key，格式：
   *   - 库：   lib:personal / lib:shared
   *   - 文件夹：folder:<folder_id>
   * 默认选中个人知识库
   */
  const selectedTreeKey = ref<string>('')

  const keyword = ref('')
  const page = ref(1)
  const pageSize = ref(10)

  const listLoading = ref(false)
  const uploadSubmitting = ref(false)

  /* ---------------------------------- 弹窗状态 ---------------------------------- */

  // 新建文件夹
  const createFolderVisible = ref(false)
  const createFolderName = ref('')
  const createFolderSubmitting = ref(false)

  // 上传
  const uploadVisible = ref(false)
  const uploadFileList = ref<File[]>([])

  // 通用确认弹窗（删除文件夹 / 删除文件 / 确认上传 共用）
  const confirmState = reactive({
    visible: false,
    title: '',
    content: '',
    onConfirm: null as null | (() => Promise<void>),
  })

  // 重命名（文件夹 / 文件 共用同一个弹窗状态）
  const renameState = reactive<{
    visible: boolean
    mode: 'folder' | 'file' | null
    targetId: string | null
    /** 原名，用于在标题提示中展示 */
    originalName: string
    /** 输入框绑定值 */
    draftName: string
    submitting: boolean
  }>({
    visible: false,
    mode: null,
    targetId: null,
    originalName: '',
    draftName: '',
    submitting: false,
  })

  // 预览
  const preview = reactive<KnowledgePreviewModel>({
    visible: false,
    loading: false,
    file: null,
    previewType: 'unsupported',
    imageUrl: undefined,
    textContent: undefined,
    htmlContent: undefined,
    errorMessage: undefined,
  })

  /* ---------------------------------- 派生状态 ---------------------------------- */

  /** 当前所属知识库 id（若选中文件夹则为该文件夹所在的库） */
  const selectedkb_id = computed<Knowledgekb_id | null>(() => {
    if (selectedTreeKey.value.startsWith('lib:')) {
      return selectedTreeKey.value.slice(4) as Knowledgekb_id
    }
    if (selectedTreeKey.value.startsWith('folder:')) {
      const id = selectedTreeKey.value.slice(7)
      return folders.value.find((f) => f.id === id)?.kb_id ?? null
    }
    return null
  })

  /** 当前选中的文件夹 id；未选中时为 null（代表库根目录） */
  const selectedfolder_id = computed<string | null>(() => {
    if (selectedTreeKey.value.startsWith('folder:')) {
      return selectedTreeKey.value.slice(7)
    }
    return null
  })

  /** 面包屑 */
  const breadcrumbLabel = computed(() => {
    const lib = libraries.value.find((l) => l.id === selectedkb_id.value)
    const libName = lib?.name ?? '未选择知识库'
    if (!selectedfolder_id.value) return `${libName} / 根目录`
    const fd = folders.value.find((f) => f.id === selectedfolder_id.value)
    return `${libName} / ${fd?.name ?? '文件夹'}`
  })

  /** NTree 数据 */
  const treeOptions = computed<TreeOption[]>(() =>
    libraries.value.map((lib) => ({
      key: `lib:${lib.id}`,
      label: lib.name,
      children: folders.value
        .filter((fd) => fd.kb_id === lib.id)
        .map((fd) => ({
          key: `folder:${fd.id}`,
          label: fd.name,
          isLeaf: true,
        })),
    })),
  )

  /** NTree v-model:selected-keys 绑定 */
  const selectedKeysForTree = computed(() => [selectedTreeKey.value])

  function onTreeSelect(keys: Array<string | number>) {
    const k = keys[0]
    if (k != null) selectedTreeKey.value = String(k)
  }

  /* ---------------------------------- 数据加载 ---------------------------------- */

  async function refreshLibraries() {
    libraries.value = await knowledgeApi.listLibraries()
  }

  async function setDefaultSelectedTreeKey() {
    selectedTreeKey.value = `lib:${libraries.value[0].id}`
  }

  async function refreshFolders() {
    const reqs = libraries.value.map(lib =>knowledgeApi.listFolders(lib.id))
    const res = await Promise.all(reqs)
    folders.value = res.flat()
  }

  async function refreshFiles() {
    const libId = selectedkb_id.value
    if (!libId) return
    listLoading.value = true
    try {
      const res = await knowledgeApi.listFiles({
        kb_id: libId,
        folder_id: selectedfolder_id.value,
        keyword: keyword.value,
        page: page.value,
        page_size: pageSize.value,
      })
      console.log(res);
      
      files.value = res.items
      total.value = res.total
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '加载文件列表失败')
    } finally {
      listLoading.value = false
    }
  }

  // 依赖项变化时自动刷新列表
  watch([selectedTreeKey, keyword, page, pageSize], () => {
    void refreshFiles()
  })

  // 切换目录 / 搜索时复位到第 1 页
  watch([selectedTreeKey, keyword], () => {
    page.value = 1
  })

  /* --------------------------------- 文件夹操作 --------------------------------- */

  function openCreateFolderModal() {
    if (!selectedkb_id.value) {
      message.warning('请先选择一个知识库')
      return
    }
    createFolderName.value = ''
    createFolderVisible.value = true
  }

  async function submitCreateFolder() {
    const libId = selectedkb_id.value
    if (!libId) return
    if (!createFolderName.value.trim()) {
      message.warning('请输入文件夹名称')
      return
    }
    createFolderSubmitting.value = true
    try {
      await knowledgeApi.createFolder(libId, createFolderName.value)
      message.success('文件夹已创建')
      createFolderVisible.value = false
      await refreshFolders()
    } catch (e: unknown) {
      // message.error(e instanceof Error ? e.message : '创建失败')
    } finally {
      createFolderSubmitting.value = false
    }
  }

  /* --------------------------------- 重命名弹窗 --------------------------------- */

  /** 打开文件夹重命名弹窗 */
  function openRenameFolder(folder: KnowledgeFolder) {
    renameState.mode = 'folder'
    renameState.targetId = folder.id
    renameState.originalName = folder.name
    renameState.draftName = folder.name
    renameState.visible = true
  }

  /** 打开文件重命名弹窗 */
  function openRenameFile(file: KnowledgeFile) {
    renameState.mode = 'file'
    renameState.targetId = file.id
    renameState.originalName = file.file_name
    renameState.draftName = file.file_name
    renameState.visible = true
  }

  function closeRenameDialog() {
    renameState.visible = false
    renameState.mode = null
    renameState.targetId = null
    renameState.originalName = ''
    renameState.draftName = ''
    renameState.submitting = false
  }

  /** 提交重命名，按 mode 分发到对应 API */
  async function submitRename() {
    const { mode, targetId, draftName, originalName } = renameState
    if (!mode || !targetId) return
    const name = draftName.trim()
    if (!name) {
      message.warning(mode === 'folder' ? '请输入文件夹名称' : '请输入文件名')
      return
    }
    // 未修改：静默关闭
    if (name === originalName) {
      closeRenameDialog()
      return
    }
    renameState.submitting = true
    try {
      if (mode === 'folder') {
        await knowledgeApi.renameFolder(targetId, name)
        await refreshFolders()
        message.success('文件夹已重命名')
      } else {
        await knowledgeApi.renameFile(targetId, name)
        await refreshFiles()
        message.success('文件已重命名')
      }
      closeRenameDialog()
    } catch (e: unknown) {
      // message.error(e instanceof Error ? e.message : '重命名失败')
    } finally {
      renameState.submitting = false
    }
  }

  /** 侧边栏行内 NPopconfirm 已做确认；此处直接执行即可 */
  async function deleteFolderNow(folder: KnowledgeFolder) {
    try {
      await knowledgeApi.deleteFolder(folder.id, folder.kb_id)
      if (selectedTreeKey.value === `folder:${folder.id}`) {
        selectedTreeKey.value = `lib:${folder.kb_id}`
      }
      await refreshFolders()
      await refreshFiles()
      message.success('文件夹已删除')
    } catch (e: unknown) {
      // message.error(e instanceof Error ? e.message : '删除失败')
    }
  }

  /* ---------------------------------- 文件操作 ---------------------------------- */

  /** 表格行 NPopconfirm 已做确认；此处直接执行即可 */
  async function deleteFileNow(file: KnowledgeFile) {
    try {
      await knowledgeApi.deleteFile(file.id)
      await refreshFiles()
      message.success('文件已删除')
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '删除失败')
    }
  }

  /* ---------------------------------- 上传流程 ---------------------------------- */

  function openUploadModal() {
    if (!selectedkb_id.value) {
      message.warning('请先选择一个知识库或文件夹')
      return
    }
    uploadFileList.value = []
    uploadVisible.value = true
  }

  function setUploadDraftFiles(list: File[]) {
    uploadFileList.value = list
  }

  /** 弹出二次确认，确认后真正上传 */
  function requestConfirmUpload() {
    if (!uploadFileList.value.length) {
      message.warning('请先选择要上传的文件')
      return
    }
    confirmState.title = '确认上传'
    confirmState.content = `将上传 ${uploadFileList.value.length} 个文件到：${breadcrumbLabel.value}，是否继续？`
    confirmState.onConfirm = async () => {
      const libId = selectedkb_id.value
      if (!libId) return
      uploadSubmitting.value = true
      try {
        await knowledgeApi.uploadFiles(
          { kb_id: libId, folder_id: selectedfolder_id.value },
          uploadFileList.value,
        )
        message.success('上传完成')
        uploadVisible.value = false
        uploadFileList.value = []
        await refreshFiles()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '上传失败')
      } finally {
        uploadSubmitting.value = false
      }
    }
    confirmState.visible = true
  }

  async function handleConfirmOk() {
    const fn = confirmState.onConfirm
    confirmState.visible = false
    confirmState.onConfirm = null
    if (fn) {
      try {
        await fn()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '操作失败')
      }
    }
  }

  function handleConfirmCancel() {
    confirmState.visible = false
    confirmState.onConfirm = null
  }

  /* ---------------------------------- 预览逻辑 ---------------------------------- */

  async function openPreview(file: KnowledgeFile) {
    revokeIfObjectUrl(preview.imageUrl)
    preview.visible = true
    preview.loading = true
    preview.file = file
    preview.previewType = inferPreviewType(file.file_name)
    preview.imageUrl = undefined
    preview.textContent = undefined
    preview.htmlContent = undefined
    preview.errorMessage = undefined
    try {
      const blob = await knowledgeApi.getFilePreviewBlob(file.id)
      const built = await buildPreviewFromBlob(file.file_name, blob)
      preview.previewType = built.previewType
      preview.imageUrl = built.imageUrl
      preview.textContent = built.textContent
      preview.htmlContent = built.htmlContent
      preview.errorMessage = built.errorMessage
    } catch {
      preview.errorMessage = '预览加载失败，请稍后重试。'
    } finally {
      preview.loading = false
    }
  }

  function closePreview() {
    revokeIfObjectUrl(preview.imageUrl)
    preview.visible = false
    preview.file = null
    preview.imageUrl = undefined
    preview.textContent = undefined
    preview.htmlContent = undefined
  }

  /* ---------------------------------- 展示辅助 ---------------------------------- */

  /** 表格中「类型」列的可读名称 */
  function displayFileType(file: KnowledgeFile): string {
    if (!file.file_ext.replace('.', '')) return '未知'
    const map: Record<string, string> = {
      md: 'Markdown',
      markdown: 'Markdown',
      txt: '文本',
      csv: 'Excel/CSV',
      xls: 'Excel',
      xlsx: 'Excel',
      png: '图片',
      jpg: '图片',
      jpeg: '图片',
      gif: '图片',
      webp: '图片',
      doc: 'Word',
      docx: 'Word',
    }
    return map[file.file_ext.replace('.', '')] ?? file.file_ext.toUpperCase().replace('.', '')
  }

  async function init() {
    await refreshLibraries()
    await setDefaultSelectedTreeKey()
    await refreshFolders()
    await refreshFiles()
  }

  /**
   * 返回 reactive 壳，便于模板中 `workspace.keyword` 直接 v-model 绑定；
   * 内部 ref 解包为对象属性，函数保持引用稳定。
   */
  return reactive({
    libraries,
    folders,
    files,
    total,
    selectedTreeKey,
    keyword,
    page,
    pageSize,
    listLoading,
    uploadSubmitting,
    createFolderVisible,
    createFolderName,
    createFolderSubmitting,
    uploadVisible,
    uploadFileList,
    confirmState,
    renameState,
    preview,
    selectedkb_id,
    selectedfolder_id,
    breadcrumbLabel,
    treeOptions,
    selectedKeysForTree,
    formatBytes,
    refreshFiles,
    openCreateFolderModal,
    submitCreateFolder,
    openRenameFolder,
    openRenameFile,
    submitRename,
    closeRenameDialog,
    deleteFolderNow,
    deleteFileNow,
    onTreeSelect,
    handleConfirmOk,
    handleConfirmCancel,
    openUploadModal,
    setUploadDraftFiles,
    requestConfirmUpload,
    openPreview,
    closePreview,
    displayFileType,
    init,
  })
}
