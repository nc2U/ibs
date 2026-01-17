<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data
const mockContracts = ref([
  { id: 1, name: '본관 건설 계약', company: '대한건설', status: 'active', amount: 5000000000 },
  { id: 2, name: '전기 설비 계약', company: '삼성전기', status: 'pending', amount: 800000000 },
  { id: 3, name: '인테리어 공사', company: '현대인테리어', status: 'active', amount: 1200000000 },
])

const statusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'pending':
      return 'warning'
    case 'completed':
      return 'info'
    default:
      return 'grey'
  }
}

const statusLabel = (status: string) => {
  switch (status) {
    case 'active':
      return '진행중'
    case 'pending':
      return '대기'
    case 'completed':
      return '완료'
    default:
      return status
  }
}

const formatAmount = (value: number) => {
  return (value / 100000000).toFixed(1) + '억'
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="contract-status-widget">
      <div class="d-flex align-center justify-space-between mb-3">
        <span class="text-h5 font-weight-bold">{{ mockContracts.length }}</span>
        <span class="text-caption text-medium-emphasis">활성 계약</span>
      </div>

      <v-list density="compact" class="pa-0">
        <v-list-item v-for="contract in mockContracts" :key="contract.id" class="px-0" lines="two">
          <v-list-item-title class="text-body-2 font-weight-medium">
            {{ contract.name }}
          </v-list-item-title>
          <v-list-item-subtitle class="text-caption">
            {{ contract.company }} · {{ formatAmount(contract.amount) }}
          </v-list-item-subtitle>
          <template #append>
            <v-chip :color="statusColor(contract.status)" size="x-small" variant="tonal">
              {{ statusLabel(contract.status) }}
            </v-chip>
          </template>
        </v-list-item>
      </v-list>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block>
        전체 계약 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.contract-status-widget {
  height: 100%;
}
</style>
