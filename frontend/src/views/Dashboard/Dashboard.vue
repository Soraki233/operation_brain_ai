<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { NCard, NGrid, NGridItem, NStatistic } from 'naive-ui'

const userStore = useUserStore()
</script>

<template>
  <div class="dashboard">
    <h2 class="welcome-title">欢迎回来，{{ userStore.username || '用户' }}</h2>
    <p class="welcome-subtitle">这是您的运维管理工作台</p>

    <NGrid :x-gap="16" :y-gap="16" :cols="4" class="stat-grid">
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="监控设备" value="--" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="今日告警" value="--" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="运行任务" value="--" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="系统状态" value="正常" />
        </NCard>
      </NGridItem>
    </NGrid>
  </div>
</template>

<style scoped lang="less">
.dashboard {
  max-width: 1200px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: @text-primary;
  margin-bottom: 4px;
}

.welcome-subtitle {
  font-size: 14px;
  color: @text-secondary;
  margin-bottom: 24px;
}

.stat-grid {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: @border-radius-lg;
}
</style>
