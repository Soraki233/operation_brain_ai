<script setup lang="ts">
import { zhCN, dateZhCN, type GlobalThemeOverrides } from 'naive-ui'
import { NConfigProvider, NMessageProvider } from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2196F3',
    primaryColorHover: '#42A5F5',
    primaryColorPressed: '#1976D2',
    primaryColorSuppl: '#4CAF50',
    borderRadius: '8px',
  },
  Button: {
    borderRadiusMedium: '8px',
  },
  Input: {
    borderRadius: '8px',
  },
}
</script>

<template>
  <NConfigProvider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <NMessageProvider>
      <router-view />
    </NMessageProvider>
  </NConfigProvider>
</template>
