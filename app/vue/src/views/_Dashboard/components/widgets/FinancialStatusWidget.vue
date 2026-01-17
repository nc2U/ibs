<script setup lang="ts">
import { ref, computed } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data
const mockData = ref({
  income: 1250000000,
  expense: 890000000,
  balance: 360000000,
  monthlyChange: 12.5,
})

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value)
}

const summaryItems = computed(() => [
  { label: '수입', value: mockData.value.income, color: 'success', icon: 'mdi-arrow-up' },
  { label: '지출', value: mockData.value.expense, color: 'error', icon: 'mdi-arrow-down' },
  { label: '잔액', value: mockData.value.balance, color: 'primary', icon: 'mdi-wallet' },
])
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="financial-status-widget">
      <v-list density="compact" class="pa-0">
        <v-list-item v-for="item in summaryItems" :key="item.label" class="px-0">
          <template #prepend>
            <v-avatar size="32" :color="item.color" variant="tonal">
              <v-icon :icon="item.icon" size="small" />
            </v-avatar>
          </template>
          <v-list-item-title class="text-body-2">{{ item.label }}</v-list-item-title>
          <template #append>
            <span class="text-body-2 font-weight-bold">{{ formatCurrency(item.value) }}</span>
          </template>
        </v-list-item>
      </v-list>

      <v-divider class="my-3" />

      <div class="d-flex align-center justify-space-between">
        <span class="text-caption text-medium-emphasis">전월 대비</span>
        <v-chip
          :color="mockData.monthlyChange >= 0 ? 'success' : 'error'"
          size="small"
          variant="tonal"
        >
          <v-icon :icon="mockData.monthlyChange >= 0 ? 'mdi-trending-up' : 'mdi-trending-down'" />
          {{ Math.abs(mockData.monthlyChange) }}%
        </v-chip>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.financial-status-widget {
  height: 100%;
}
</style>
