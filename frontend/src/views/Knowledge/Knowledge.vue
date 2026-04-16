<script setup lang="ts">
/**
 * 知识库模块页面壳
 * - 外层统一一张圆角大卡片（与 Chat 页风格保持一致）
 * - 左：KnowledgeSidebar（渐变背景、树形目录）
 * - 右：KnowledgeFilePanel（工具栏 + 文件表格）
 * - 页内弹窗：新建文件夹 / 通用确认 / 上传 / 预览
 *
 * 状态集中在 createKnowledgeWorkspace()，通过 provide 注入给子组件。
 */
import { onMounted, provide } from 'vue'
import { NButton, NInput, NModal } from 'naive-ui'
import KnowledgeFilePanel from './components/KnowledgeFilePanel.vue'
import KnowledgePreviewDrawer from './components/KnowledgePreviewDrawer.vue'
import KnowledgeSidebar from './components/KnowledgeSidebar.vue'
import KnowledgeUploadModal from './components/KnowledgeUploadModal.vue'
import {
  KNOWLEDGE_WORKSPACE_KEY,
  createKnowledgeWorkspace,
} from './composables/knowledgeWorkspace'

const workspace = createKnowledgeWorkspace()
provide(KNOWLEDGE_WORKSPACE_KEY, workspace)

onMounted(() => {
  void workspace.init()
})
</script>

<template>
  <div class="knowledge-page">
    <KnowledgeSidebar />

    <div class="knowledge-main">
      <KnowledgeFilePanel />
    </div>

    <!-- 新建文件夹 -->
    <NModal
      v-model:show="workspace.createFolderVisible"
      preset="card"
      title="新建文件夹"
      :style="{ width: '420px' }"
      :mask-closable="false"
    >
      <NInput
        v-model:value="workspace.createFolderName"
        placeholder="请输入文件夹名称"
        maxlength="40"
        show-count
        autofocus
      />
      <template #footer>
        <div class="modal-footer">
          <NButton quaternary @click="workspace.createFolderVisible = false">
            取消
          </NButton>
          <NButton
            type="primary"
            :loading="workspace.createFolderSubmitting"
            @click="workspace.submitCreateFolder"
          >
            确定
          </NButton>
        </div>
      </template>
    </NModal>

    <!-- 通用确认弹窗：上传前的二次确认等场景 -->
    <NModal
      v-model:show="workspace.confirmState.visible"
      preset="dialog"
      :title="workspace.confirmState.title"
      :content="workspace.confirmState.content"
      positive-text="确定"
      negative-text="取消"
      @positive-click="workspace.handleConfirmOk"
      @negative-click="workspace.handleConfirmCancel"
    />

    <!-- 上传 / 预览 -->
    <KnowledgeUploadModal />
    <KnowledgePreviewDrawer />
  </div>
</template>

<style scoped lang="less">
.knowledge-page {
  display: flex;
  height: calc(100vh - 100px);
  background: @bg-white;
  border-radius: @border-radius-lg;
  overflow: hidden;
  box-shadow: @shadow-sm;
  animation: pageEnter 0.4s ease;
}

.knowledge-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: @bg-color;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
