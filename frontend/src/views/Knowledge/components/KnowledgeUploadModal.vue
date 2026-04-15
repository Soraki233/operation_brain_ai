<script setup lang="ts">
import { NModal, NUpload, NUploadDragger, NIcon, NText } from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'

const props = defineProps<{
  fileAccept: string
  maxSizeMb: number
  beforeUpload: (options: { file: UploadFileInfo }) => boolean | Promise<boolean>
}>()

const show = defineModel<boolean>('show', { required: true })

const emit = defineEmits<{
  finish: [options: { file: UploadFileInfo; event?: ProgressEvent }]
}>()
</script>

<template>
  <NModal v-model:show="show" preset="card" title="上传文件" style="width: 520px; max-width: 90vw;">
    <NUpload
      multiple
      directory-dnd
      :accept="fileAccept"
      :default-upload="false"
      :show-file-list="false"
      @before-upload="props.beforeUpload"
      @finish="(o) => emit('finish', o)"
    >
      <NUploadDragger>
        <div class="upload-dragger-content">
          <NIcon :size="48" class="upload-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.35 10.04A7.49 7.49 0 0 0 12 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 0 0 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
            </svg>
          </NIcon>
          <NText class="upload-text">点击或拖拽文件到此区域上传</NText>
          <NText depth="3" class="upload-hint">
            支持 PDF / Word / TXT / Markdown / Excel / CSV，单文件最大 {{ maxSizeMb }}MB
          </NText>
        </div>
      </NUploadDragger>
    </NUpload>
  </NModal>
</template>

<style scoped lang="less">
.upload-dragger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
}

.upload-icon {
  color: @primary-blue;
  margin-bottom: 12px;
  animation: floatUp 2s ease-in-out infinite;
}

.upload-text {
  font-size: 15px;
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 13px;
}

@keyframes floatUp {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
</style>
