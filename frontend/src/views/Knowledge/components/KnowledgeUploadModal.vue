<script setup lang="ts">
/**
 * 上传弹窗
 * - 仅挑选文件（default-upload 关闭），由「下一步：确认上传」触发二次确认后统一上传
 * - 前端做一次类型白名单校验，不允许的类型会被剔除并提示
 */
import { inject } from 'vue'
import {
  NAlert,
  NButton,
  NIcon,
  NModal,
  NUpload,
  NUploadDragger,
  useMessage,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import {
  KNOWLEDGE_UPLOAD_ACCEPT,
  isAllowedKnowledgeFile,
} from '../utils/fileAccept'
import { KNOWLEDGE_WORKSPACE_KEY } from '../composables/knowledgeWorkspace'

const injected = inject(KNOWLEDGE_WORKSPACE_KEY)
if (!injected) throw new Error('KnowledgeUploadModal 必须在 Knowledge 工作区内使用')
const workspace = injected

const message = useMessage()

function handleUploadChange(data: { fileList: UploadFileInfo[] }) {
  const raw = data.fileList
    .map((f) => f.file)
    .filter((x): x is File => !!x)

  const allowed: File[] = []
  const rejected: string[] = []
  for (const f of raw) {
    if (isAllowedKnowledgeFile(f)) allowed.push(f)
    else rejected.push(f.name)
  }
  if (rejected.length) {
    message.warning(`以下文件类型不受支持，已忽略：${rejected.join('、')}`)
  }
  workspace.setUploadDraftFiles(allowed)
}
</script>

<template>
  <NModal
    v-model:show="workspace.uploadVisible"
    preset="card"
    title="上传文件"
    :style="{ width: '560px' }"
    :mask-closable="false"
    class="upload-modal"
  >
    <div class="upload-body">
      <NAlert type="info" class="upload-tip" :bordered="false" title="上传说明">
        支持 Markdown / Excel / TXT / 图片 / Word；文件将上传到：
        <strong class="target-label">{{ workspace.breadcrumbLabel }}</strong>
      </NAlert>

      <NUpload
        multiple
        directory-dnd
        :max="30"
        :default-upload="false"
        :accept="KNOWLEDGE_UPLOAD_ACCEPT"
        class="upload-area"
        @change="handleUploadChange"
      >
        <NUploadDragger class="dragger">
          <div class="dragger-inner">
            <div class="dragger-icon">
              <NIcon size="28">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z" />
                </svg>
              </NIcon>
            </div>
            <div class="dragger-title">点击或拖拽文件到此处</div>
            <div class="dragger-sub">
              已选择
              <span class="count">{{ workspace.uploadFileList.length }}</span>
              个文件
            </div>
          </div>
        </NUploadDragger>
      </NUpload>
    </div>

    <template #footer>
      <div class="footer-row">
        <NButton quaternary @click="workspace.uploadVisible = false">取消</NButton>
        <NButton
          type="primary"
          class="primary-gradient"
          :loading="workspace.uploadSubmitting"
          @click="workspace.requestConfirmUpload"
        >
          下一步：确认上传
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped lang="less">
.upload-body {
  display: flex;
  flex-direction: column;
}

.upload-tip {
  margin-bottom: 16px;
  border-radius: @border-radius-md;
}

.target-label {
  color: @primary-blue;
  margin-left: 4px;
}

.upload-area {
  display: block;
}

.dragger {
  padding: 28px 16px;
  border-radius: @border-radius-lg;
  transition: background 0.2s, border-color 0.2s;
}

.dragger-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.dragger-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: @primary-blue-light;
  color: @primary-blue;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dragger-title {
  font-weight: 600;
  color: @text-primary;
  font-size: 15px;
}

.dragger-sub {
  font-size: 13px;
  color: @text-secondary;
}

.count {
  color: @primary-blue;
  font-weight: 600;
  margin: 0 2px;
}

.footer-row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.primary-gradient {
  background: @gradient-primary !important;
  border: none !important;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.92;
  }
}
</style>
