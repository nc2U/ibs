<script setup lang="ts">
import { computed } from 'vue'
import { useDashboard } from '@/store/pinia/dashboard.ts'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const dashboardStore = useDashboard()

const drawer = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val),
})

const widgets = computed(() => dashboardStore.availableWidgets)

const handleToggle = (widgetId: string) => {
  dashboardStore.toggleWidgetVisibility(widgetId)
}

const handleReset = () => {
  dashboardStore.resetToDefaults()
}
</script>

<template>
  <div class="widget-config-panel">
    <v-navigation-drawer v-model="drawer" location="right" temporary width="320">
      <v-card flat>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-view-dashboard-edit" class="mr-2" />
          <span>위젯 설정</span>
          <v-spacer />
          <v-btn icon variant="text" size="small" @click="drawer = false">
            <v-icon icon="mdi-close" />
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-0">
          <v-list density="compact">
            <v-list-subheader>표시할 위젯 선택</v-list-subheader>

            <v-list-item v-for="widget in widgets" :key="widget.id" @click="handleToggle(widget.id)">
              <template #prepend>
                <v-icon :icon="widget.icon" size="small" />
              </template>
              <v-list-item-title>{{ widget.titleKo }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption">{{ widget.title }}</v-list-item-subtitle>
              <template #append>
                <v-switch
                  :model-value="widget.isVisible"
                  color="primary"
                  hide-details
                  density="compact"
                  @update:model-value="handleToggle(widget.id)"
                  @click.stop
                />
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-btn variant="outlined" color="warning" block @click="handleReset">
            <v-icon icon="mdi-restore" class="mr-2" />
            기본값으로 초기화
          </v-btn>
        </v-card-actions>

        <v-card-text class="text-caption text-medium-emphasis">
          <v-icon icon="mdi-information-outline" size="small" class="mr-1" />
          위젯을 드래그하여 위치를 변경하고, 모서리를 드래그하여 크기를 조절할 수 있습니다.
        </v-card-text>
      </v-card>
    </v-navigation-drawer>
  </div>
</template>

<style scoped>
/* Dark Theme Overrides for WidgetConfigPanel */
body.dark-theme .widget-config-panel :deep(.v-navigation-drawer) {
  background-color: rgb(30 30 40 / 95%); /* Dark, slightly transparent background */
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-left: 1px solid rgb(64 64 79);
}

body.dark-theme .widget-config-panel :deep(.v-card) {
  background-color: transparent;
  color: #d1d1d1;
}

body.dark-theme .widget-config-panel :deep(.v-card-title),
body.dark-theme .widget-config-panel :deep(.v-list-item-title) {
  color: #ffffff;
}

body.dark-theme .widget-config-panel :deep(.v-list-subheader),
body.dark-theme .widget-config-panel :deep(.v-list-item-subtitle),
body.dark-theme .widget-config-panel :deep(.v-card-text.text-caption) {
  color: #a0a0b0;
}

body.dark-theme .widget-config-panel :deep(.v-divider) {
  border-color: rgb(64 64 79);
}

body.dark-theme .widget-config-panel :deep(.v-list-item:hover) {
  background-color: rgba(64, 64, 79, 0.7);
}

body.dark-theme .widget-config-panel :deep(.v-btn) {
  color: #d1d1d1;
}

body.dark-theme .widget-config-panel :deep(.v-btn--variant-outlined) {
  border-color: currentColor;
}
</style>