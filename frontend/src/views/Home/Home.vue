<script setup lang="ts">
import { h, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useMessage } from 'naive-ui'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NAvatar,
  NDropdown,
  NIcon,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const message = useMessage()
const collapsed = ref(false)

const activeKey = computed(() => route.name as string)

const menuOptions: MenuOption[] = [
  {
    label: '工作台',
    key: 'Dashboard',
    icon: renderIcon('dashboard'),
  },
  {
    label: '知识库',
    key: 'Knowledge',
    icon: renderIcon('knowledge'),
  },
  {
    label: 'AI 对话',
    key: 'Chat',
    icon: renderIcon('chat'),
  },
]

const userDropdownOptions = [
  { label: '个人设置', key: 'profile' },
  { type: 'divider', key: 'd1' },
  { label: '退出登录', key: 'logout' },
]

function renderIcon(name: string) {
  const icons: Record<string, string> = {
    dashboard: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z',
    knowledge: 'M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z',
    chat: 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z',
  }
  return () =>
    h(NIcon, null, {
      default: () =>
        h(
          'svg',
          { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' },
          [h('path', { d: icons[name] || icons.dashboard })],
        ),
    })
}

function handleMenuUpdate(key: string) {
  router.push({ name: key })
}

function handleUserAction(key: string) {
  if (key === 'logout') {
    userStore.logout()
    message.success('已退出登录')
    router.push('/login')
  }
}
</script>

<template>
  <NLayout has-sider class="home-layout">
    <NLayoutSider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      :native-scrollbar="false"
      class="home-sider"
    >
      <div class="sider-logo">
        <img src="@/assets/logo.png" alt="logo" :class="['sider-logo-img', { collapsed }]" />
      </div>
      <NMenu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuUpdate"
      />
    </NLayoutSider>

    <NLayout>
      <NLayoutHeader bordered class="home-header">
        <div class="header-left"></div>
        <div class="header-right">
          <NDropdown :options="userDropdownOptions" @select="handleUserAction">
            <div class="user-info">
              <NAvatar round :size="32" class="user-avatar">
                {{ userStore.username?.charAt(0)?.toUpperCase() || 'U' }}
              </NAvatar>
              <span class="user-name">{{ userStore.username || '用户' }}</span>
            </div>
          </NDropdown>
        </div>
      </NLayoutHeader>
      <NLayoutContent class="home-content" :native-scrollbar="false">
        <router-view />
      </NLayoutContent>
    </NLayout>
  </NLayout>
</template>

<style scoped lang="less">
.home-layout {
  height: 100vh;
}

.home-sider {
  :deep(.n-layout-sider-scroll-container) {
    display: flex;
    flex-direction: column;
  }
}

.sider-logo {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid @border-color;
  flex-shrink: 0;
}

.sider-logo-img {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
  transition: all 0.3s ease;

  &.collapsed {
    width: 40px;
    height: 40px;
  }
}

.home-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: @border-radius-md;
  transition: background 0.2s;

  &:hover {
    background: @bg-color;
  }
}

.user-avatar {
  background: @gradient-primary;
  color: #fff;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: @text-primary;
}

.home-content {
  padding: 20px;
  background: @bg-color;
}
</style>
