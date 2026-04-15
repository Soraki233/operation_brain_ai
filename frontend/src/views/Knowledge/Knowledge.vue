<script setup lang="ts">
import { ref, h, computed } from 'vue'
import { useMessage } from 'naive-ui'
import {
  NButton,
  NTag,
  NSpace,
} from 'naive-ui'
import type { UploadFileInfo, DataTableColumns } from 'naive-ui'
import type { KnowledgeFile } from '@/api/knowledge'
import type { ExcelSheetHtml } from '@/utils/knowledgePreview.types'
import { getDemoWordHtml, getMockExcelSheetsForDemo } from '@/utils/knowledgePreviewMock'
import type { KnowledgeFolder } from './types'
import KnowledgePageHeader from './components/KnowledgePageHeader.vue'
import KnowledgeFolderSidebar from './components/KnowledgeFolderSidebar.vue'
import KnowledgeFilePanel from './components/KnowledgeFilePanel.vue'
import KnowledgeUploadModal from './components/KnowledgeUploadModal.vue'
import KnowledgePreviewModal from './components/KnowledgePreviewModal.vue'

const message = useMessage()

const FILE_ACCEPT = '.pdf,.doc,.docx,.txt,.md,.xlsx,.xls,.csv'
const MAX_SIZE_MB = 20

const folders = ref<KnowledgeFolder[]>([
  { id: 'all', name: '全部文件', fileCount: 0 },
  { id: 'f1', name: '运维文档', fileCount: 2 },
  { id: 'f2', name: '巡检记录', fileCount: 1 },
  { id: 'f3', name: '系统设计', fileCount: 1 },
])

const activeFolderId = ref('all')
const searchQuery = ref('')
const showNewFolder = ref(false)
const newFolderName = ref('')

const allFiles = ref<(KnowledgeFile & { folderId: string })[]>([
  { id: '1', name: '运维手册v3.2.pdf', type: 'PDF', size: 2_457_600, uploadedAt: '2026-04-10 14:30', status: 'ready', folderId: 'f1' },
  { id: '2', name: '设备巡检记录.xlsx', type: 'Excel', size: 184_320, uploadedAt: '2026-04-12 09:15', status: 'ready', folderId: 'f2' },
  { id: '3', name: '故障排查指南.md', type: 'Markdown', size: 35_840, uploadedAt: '2026-04-13 16:42', status: 'ready', folderId: 'f1' },
  { id: '4', name: '系统架构说明.docx', type: 'Word', size: 512_000, uploadedAt: '2026-04-14 08:20', status: 'processing', folderId: 'f3' },
])

const filteredFiles = computed(() => {
  let list = activeFolderId.value === 'all'
    ? allFiles.value
    : allFiles.value.filter((f) => f.folderId === activeFolderId.value)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter((f) => f.name.toLowerCase().includes(q) || f.type.toLowerCase().includes(q))
  }
  return list
})

function updateFolderCounts() {
  folders.value.forEach((folder) => {
    if (folder.id === 'all') {
      folder.fileCount = allFiles.value.length
    } else {
      folder.fileCount = allFiles.value.filter((f) => f.folderId === folder.id).length
    }
  })
}
updateFolderCounts()

const previewVisible = ref(false)
const previewFile = ref<KnowledgeFile | null>(null)
const previewContent = ref('')
const previewMode = ref<'text' | 'html' | 'excel'>('text')
const previewHtml = ref('')
const previewSheets = ref<ExcelSheetHtml[]>([])
const previewLoading = ref(false)
const uploadVisible = ref(false)

/** 本地上传文件的二进制，用于 Word / Excel 浏览器内预览 */
const fileStore = ref<Record<string, File>>({})

const mockPreviewContents: Record<string, string> = {
  '1': '# 运维手册 v3.2\n\n## 1. 系统概述\n\n本手册适用于 OpsBrain AI 智能运维管理平台的日常运维工作...\n\n## 2. 巡检流程\n\n### 2.1 日常巡检\n- 检查服务器CPU、内存使用率\n- 检查磁盘空间\n- 检查网络连接状态\n- 查看系统日志异常\n\n### 2.2 周巡检\n- 数据库性能分析\n- 安全漏洞扫描\n- 备份验证',
  '3': '# 故障排查指南\n\n## 常见故障\n\n### 1. 服务无法启动\n\n**现象**：服务启动后立即退出\n\n**排查步骤**：\n1. 检查端口是否被占用\n2. 查看日志文件 `/var/log/app.log`\n3. 确认配置文件格式正确\n\n### 2. 数据库连接超时\n\n**现象**：请求响应慢或报 timeout\n\n**排查步骤**：\n1. 检查数据库服务状态\n2. 查看连接池使用情况\n3. 分析慢查询日志',
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getTypeTag(type: string) {
  const map: Record<string, 'success' | 'info' | 'warning' | 'error'> = {
    PDF: 'error', Word: 'info', Excel: 'success', Markdown: 'warning', TXT: 'default' as any, CSV: 'success',
  }
  return map[type] || 'default'
}

const columns: DataTableColumns<KnowledgeFile & { folderId: string }> = [
  {
    title: '文件名',
    key: 'name',
    ellipsis: { tooltip: true },
    render(row) {
      const iconPath = getFileIconPath(row.type)
      return h('div', { class: 'file-name-cell' }, [
        h('svg', {
          xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor',
          class: `file-icon file-icon-${row.type.toLowerCase()}`,
          width: 18, height: 18,
        }, [h('path', { d: iconPath })]),
        h('span', {}, row.name),
      ])
    },
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
    render(row) {
      return h(NTag, { size: 'small', type: getTypeTag(row.type), bordered: false, round: true }, { default: () => row.type })
    },
  },
  {
    title: '大小',
    key: 'size',
    width: 100,
    render(row) { return formatFileSize(row.size) },
  },
  { title: '上传时间', key: 'uploadedAt', width: 170 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      if (row.status === 'processing')
        return h(NTag, { size: 'small', type: 'warning', bordered: false, round: true }, { default: () => '处理中' })
      if (row.status === 'failed')
        return h(NTag, { size: 'small', type: 'error', bordered: false, round: true }, { default: () => '失败' })
      return h(NTag, { size: 'small', type: 'success', bordered: false, round: true }, { default: () => '就绪' })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', quaternary: true, type: 'info', onClick: () => handlePreview(row) }, { default: () => '预览' }),
          h(NButton, { size: 'small', quaternary: true, type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' }),
        ],
      })
    },
  },
]

function getFileIconPath(type: string) {
  const map: Record<string, string> = {
    PDF: 'M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z',
    Word: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z',
    Excel: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z',
    Markdown: 'M20.56 18H3.44C2.65 18 2 17.37 2 16.59V7.41C2 6.63 2.65 6 3.44 6h17.12c.79 0 1.44.63 1.44 1.41v9.18c0 .78-.65 1.41-1.44 1.41zM6 15.5v-3l1.5 2 1.5-2v3h1.5V8.5H9L7.5 10.75 6 8.5H4.5v7H6zm7-3.5h1.5v3.5H16V12h1.5V8.5h-1.5V11H13V8.5h-1.5V15H13v-3z',
    TXT: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z',
    CSV: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z',
  }
  return map[type] || map.TXT
}

async function handlePreview(file: KnowledgeFile & { folderId: string }) {
  previewFile.value = file
  previewVisible.value = true
  previewLoading.value = true
  previewMode.value = 'text'
  previewContent.value = ''
  previewHtml.value = ''
  previewSheets.value = []

  const ext = file.name.split('.').pop()?.toLowerCase() || ''

  try {
    if (file.type === 'Word' || ext === 'doc' || ext === 'docx') {
      if (ext === 'doc') {
        previewContent.value =
          '旧版 Word .doc 格式暂不支持在浏览器中预览，请将文件另存为 .docx 后重新上传。'
        return
      }

      const local = fileStore.value[file.id]
      let buffer: ArrayBuffer | null = local ? await local.arrayBuffer() : null

      if (!buffer) {
        const demo = getDemoWordHtml(file.id)
        if (demo) {
          previewMode.value = 'html'
          previewHtml.value = demo
          return
        }
        previewContent.value =
          mockPreviewContents[file.id] ||
          `[${file.name}] 暂无本地文件数据，请上传 .docx 后预览。`
        return
      }

      previewMode.value = 'html'
      const { docxArrayBufferToHtml } = await import('@/utils/knowledgePreview')
      previewHtml.value = await docxArrayBufferToHtml(buffer)
      return
    }

    if (file.type === 'Excel' || file.type === 'CSV' || ['xlsx', 'xls', 'csv'].includes(ext)) {
      let buffer: ArrayBuffer | null = null
      const local = fileStore.value[file.id]
      if (local) buffer = await local.arrayBuffer()

      if (!buffer && file.id === '2') {
        previewMode.value = 'excel'
        previewSheets.value = getMockExcelSheetsForDemo()
        return
      }

      if (!buffer) {
        previewContent.value =
          mockPreviewContents[file.id] ||
          `[${file.name}] 暂无本地文件数据，请上传表格文件后预览。`
        return
      }

      previewMode.value = 'excel'
      const { excelArrayBufferToSheetHtmlList } = await import('@/utils/knowledgePreview')
      previewSheets.value = excelArrayBufferToSheetHtmlList(buffer)
      return
    }

    previewContent.value =
      mockPreviewContents[file.id] || `[${file.name}] 暂不支持在线预览此文件类型，请下载后查看。`
  } catch (e) {
    console.error(e)
    message.error('预览解析失败，请确认文件未损坏')
    previewContent.value = '预览失败，请下载文件到本地查看。'
  } finally {
    previewLoading.value = false
  }
}

function handleDelete(file: KnowledgeFile) {
  allFiles.value = allFiles.value.filter((f) => f.id !== file.id)
  delete fileStore.value[file.id]
  updateFolderCounts()
  message.success(`已删除 ${file.name}`)
}

function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) { message.warning('请输入文件夹名称'); return }
  if (folders.value.some((f) => f.name === name)) { message.warning('文件夹已存在'); return }
  folders.value.push({ id: `f-${Date.now()}`, name, fileCount: 0 })
  newFolderName.value = ''
  showNewFolder.value = false
  message.success(`已创建文件夹「${name}」`)
}

function deleteFolder(folder: KnowledgeFolder) {
  if (folder.id === 'all') return
  allFiles.value = allFiles.value.filter((f) => f.folderId !== folder.id)
  folders.value = folders.value.filter((f) => f.id !== folder.id)
  if (activeFolderId.value === folder.id) activeFolderId.value = 'all'
  updateFolderCounts()
  message.success(`已删除文件夹「${folder.name}」`)
}

function getFileType(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  const map: Record<string, string> = {
    pdf: 'PDF', doc: 'Word', docx: 'Word', txt: 'TXT', md: 'Markdown',
    xlsx: 'Excel', xls: 'Excel', csv: 'CSV',
  }
  return map[ext] || ext.toUpperCase()
}

function handleBeforeUpload({ file }: { file: UploadFileInfo }) {
  const sizeMB = (file.file?.size || 0) / (1024 * 1024)
  if (sizeMB > MAX_SIZE_MB) { message.error(`文件大小不能超过 ${MAX_SIZE_MB}MB`); return false }
  return true
}

function handleUploadFinish({ file }: { file: UploadFileInfo }) {
  const folderId = activeFolderId.value === 'all' ? (folders.value[1]?.id || 'all') : activeFolderId.value
  const newFile = {
    id: Date.now().toString(),
    name: file.name,
    type: getFileType(file.name),
    size: file.file?.size || 0,
    uploadedAt: new Date().toLocaleString('zh-CN'),
    status: 'processing' as const,
    folderId,
  }
  allFiles.value.unshift(newFile)
  if (file.file) fileStore.value[newFile.id] = file.file
  updateFolderCounts()
  message.success(`${file.name} 上传成功`)
  setTimeout(() => {
    const f = allFiles.value.find((item) => item.id === newFile.id)
    if (f) f.status = 'ready'
  }, 2000)
}
</script>

<template>
  <div class="knowledge-page">
    <KnowledgePageHeader @upload="uploadVisible = true" />

    <div class="knowledge-body">
      <KnowledgeFolderSidebar
        v-model:active-folder-id="activeFolderId"
        v-model:show-new-folder="showNewFolder"
        v-model:new-folder-name="newFolderName"
        :folders="folders"
        @create-folder="createFolder"
        @delete-folder="deleteFolder"
      />

      <KnowledgeFilePanel v-model:search-query="searchQuery" :columns="columns" :data="filteredFiles" />
    </div>

    <KnowledgeUploadModal
      v-model:show="uploadVisible"
      :file-accept="FILE_ACCEPT"
      :max-size-mb="MAX_SIZE_MB"
      :before-upload="handleBeforeUpload"
      @finish="handleUploadFinish"
    />

    <KnowledgePreviewModal
      v-model:show="previewVisible"
      :title="previewFile?.name || '文件预览'"
      :loading="previewLoading"
      :mode="previewMode"
      :content="previewContent"
      :html="previewHtml"
      :sheets="previewSheets"
    />
  </div>
</template>

<style scoped lang="less">
.knowledge-page {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.knowledge-body {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  animation: fadeSlideUp 0.45s ease;
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
