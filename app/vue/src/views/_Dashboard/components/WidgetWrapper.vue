<script setup lang="ts">
import { ref } from 'vue'
import { useDashboard } from '@/store/pinia/dashboard.ts'

const props = defineProps<{
  widgetId: string
  title: string
  icon?: string
  refreshable?: boolean
  configurable?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  configure: []
}>()

const dashboardStore = useDashboard()

const loading = ref(false)

const handleRefresh = async () => {
  loading.value = true
  emit('refresh')
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleClose = () => {
  dashboardStore.removeWidget(props.widgetId)
}
</script>

<template>
  <v-card class="widget-card h-100 d-flex flex-column" elevation="2">
    <v-card-title class="widget-header d-flex align-center py-2 px-3 drag-handle">
      <v-icon v-if="icon" :icon="icon" size="small" class="mr-2" />
      <span class="text-body-2 font-weight-medium">{{ title }}</span>
      <v-spacer />
      <div class="widget-actions">
        <v-btn
          v-if="refreshable"
          icon
          size="x-small"
          variant="text"
          :loading="loading"
          @click.stop="handleRefresh"
        >
          <v-icon icon="mdi-refresh" size="16" />
        </v-btn>
        <v-btn
          v-if="configurable"
          icon
          size="x-small"
          variant="text"
          @click.stop="emit('configure')"
        >
          <v-icon icon="mdi-cog" size="16" />
        </v-btn>
        <v-btn icon size="x-small" variant="text" @click.stop="handleClose">
          <v-icon icon="mdi-close" size="16" />
        </v-btn>
      </div>
    </v-card-title>
    <v-divider />
    <v-card-text class="widget-content flex-grow-1 pa-3 overflow-auto">
      <slot />
    </v-card-text>
  </v-card>
</template>

<style scoped>
.widget-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
}

.widget-header {
  cursor: move;
  background: rgba(var(--v-theme-primary), 0.08);
  min-height: 40px;
  color: rgb(var(--v-theme-on-surface));
}

.widget-header:hover {
  background: rgba(var(--v-theme-primary), 0.12);
}

.widget-header :deep(.v-icon) {
  color: rgb(var(--v-theme-primary));
}

.widget-actions {
  display: flex;
  gap: 2px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.widget-actions :deep(.v-icon) {
  color: rgb(var(--v-theme-on-surface-variant));
}

.widget-card:hover .widget-actions {
  opacity: 1;
}

.widget-content {
  min-height: 0;
}

.drag-handle {
  user-select: none;
}
</style>
