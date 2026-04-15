<script setup lang="ts">
import { NButton, NIcon, NScrollbar, NInput, NEllipsis } from 'naive-ui'
import type { KnowledgeFolder } from '../types'

defineProps<{
  folders: KnowledgeFolder[]
  activeFolderId: string
  showNewFolder: boolean
  newFolderName: string
}>()

const emit = defineEmits<{
  'update:activeFolderId': [id: string]
  'update:showNewFolder': [v: boolean]
  'update:newFolderName': [v: string]
  'create-folder': []
  'delete-folder': [folder: KnowledgeFolder]
}>()

function setActive(id: string) {
  emit('update:activeFolderId', id)
}
</script>

<template>
  <div class="folder-sidebar">
    <div class="folder-header">
      <span class="folder-label">文件夹</span>
      <NButton size="tiny" quaternary type="primary" @click="emit('update:showNewFolder', !showNewFolder)">
        <template #icon>
          <NIcon :size="14"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" /></svg></NIcon>
        </template>
      </NButton>
    </div>

    <Transition name="fold">
      <div v-if="showNewFolder" class="new-folder-input">
        <NInput
          :value="newFolderName"
          size="small"
          placeholder="文件夹名称"
          @update:value="(v) => emit('update:newFolderName', v)"
          @keyup.enter="emit('create-folder')"
        />
        <NButton size="small" type="primary" :disabled="!newFolderName.trim()" @click="emit('create-folder')">
          确定
        </NButton>
      </div>
    </Transition>

    <NScrollbar class="folder-list">
      <TransitionGroup name="folder-item">
        <div
          v-for="folder in folders"
          :key="folder.id"
          :class="['folder-item', { active: folder.id === activeFolderId }]"
          @click="setActive(folder.id)"
        >
          <NIcon :size="18" class="folder-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path v-if="folder.id === 'all'" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z" />
              <path v-else d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
            </svg>
          </NIcon>
          <NEllipsis class="folder-name">{{ folder.name }}</NEllipsis>
          <span class="folder-count">{{ folder.fileCount }}</span>
          <NButton
            v-if="folder.id !== 'all'"
            size="tiny"
            quaternary
            type="error"
            class="folder-delete"
            @click.stop="emit('delete-folder', folder)"
          >
            <template #icon>
              <NIcon :size="12"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" /></svg></NIcon>
            </template>
          </NButton>
        </div>
      </TransitionGroup>
    </NScrollbar>
  </div>
</template>

<style scoped lang="less">
.folder-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: @bg-white;
  border-radius: @border-radius-lg;
  box-shadow: @shadow-sm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.folder-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
}

.folder-label {
  font-size: 13px;
  font-weight: 600;
  color: @text-secondary;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.new-folder-input {
  display: flex;
  gap: 6px;
  padding: 0 12px 10px;
}

.folder-list {
  flex: 1;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: @bg-color;
    .folder-delete { opacity: 1; }
  }

  &.active {
    background: @primary-blue-light;
    .folder-icon { color: @primary-blue; }
    .folder-name { color: @primary-blue; font-weight: 500; }
  }
}

.folder-icon {
  color: @text-placeholder;
  flex-shrink: 0;
  transition: color 0.2s;
}

.folder-name {
  flex: 1;
  font-size: 14px;
  color: @text-primary;
  min-width: 0;
}

.folder-count {
  font-size: 12px;
  color: @text-placeholder;
  background: @bg-color;
  padding: 1px 7px;
  border-radius: 10px;
  flex-shrink: 0;
}

.folder-delete {
  opacity: 0;
  flex-shrink: 0;
  transition: opacity 0.15s;
}

.fold-enter-active, .fold-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.fold-enter-from, .fold-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.fold-enter-to, .fold-leave-from {
  max-height: 50px;
  opacity: 1;
}

.folder-item-enter-active {
  transition: all 0.3s ease;
}
.folder-item-leave-active {
  transition: all 0.2s ease;
}
.folder-item-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}
.folder-item-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
