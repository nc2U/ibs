<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'
import { elapsedTime } from '@/utils/baseMixins'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const loading = ref(false)
const contractLogs = ref<any[]>([])

const fetchContractLogs = async () => {
  loading.value = true
  try {
    const res = await api.get('/contract-set/?ordering=-created')
    // 응답이 없는 경우 방어
    if (!res || !res.data) {
      contractLogs.value = []
      return
    }
    
    // 페이지네이션 결과 검사 및 배열 여부 체크
    let data = []
    if (res.data.results && Array.isArray(res.data.results)) {
      data = res.data.results
    } else if (Array.isArray(res.data)) {
      data = res.data
    }
    
    contractLogs.value = data.slice(0, 5)
  } catch (error) {
    console.error('Failed to fetch contract logs:', error)
    contractLogs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchContractLogs)

// 분양 계약 상태별 뱃지 테마 설정
const getStatusTheme = (status: string) => {
  const themes: Record<string, { color: string; text: string }> = {
    '1': { color: 'amber', text: '청약' },
    '2': { color: 'success', text: '계약체결' },
    '3': { color: 'blue-grey', text: '청약해지' },
    '4': { color: 'error', text: '계약해지' },
    '5': { color: 'info', text: '양도승계' },
  }
  return themes[status] || { color: 'grey', text: '미정' }
}

// 금액 천단위 포맷
const formatPrice = (val: any) => {
  if (val === undefined || val === null) return '₩ 0'
  return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' })
    .format(Number(val))
    .replace('₩', '₩ ')
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchContractLogs">
    <div class="contract-log-widget">
      <div v-if="loading && contractLogs.length === 0" class="d-flex align-center justify-center py-8">
        <v-progress-circular indeterminate color="primary" size="24" />
      </div>

      <div v-else-if="contractLogs.length === 0" class="d-flex align-center justify-center py-8 text-grey text-caption">
        최근 계약 변동 내역이 없습니다.
      </div>

      <!-- 계약 변동 로그 리스트 -->
      <v-list v-else density="compact" class="pa-0 bg-transparent">
        <v-list-item
          v-for="log in contractLogs"
          :key="log?.pk"
          class="mb-2 rounded-lg list-item pa-3"
          variant="flat"
        >
          <div class="d-flex justify-space-between align-center mb-1">
            <!-- 동호수 & 계약자명 -->
            <div class="d-flex align-center">
              <v-chip
                v-if="log?.contractor?.status"
                size="x-small"
                :color="getStatusTheme(log.contractor.status).color"
                class="mr-2 font-weight-bold"
                variant="flat"
              >
                {{ getStatusTheme(log.contractor.status).text }}
              </v-chip>
              <span class="text-body-2 font-weight-bold text-slate-800">
                <span v-if="log?.key_unit?.houseunit?.__str__">
                  {{ log.key_unit.houseunit.__str__ }}
                </span>
                <span v-else class="text-grey-darken-1">동호수 미정</span>
                <span v-if="log?.contractor?.name"> · {{ log.contractor.name }}</span>
              </span>
            </div>
            <!-- 시간 경과 -->
            <span class="text-caption text-grey-darken-1">{{ log?.created ? elapsedTime(log.created) : '' }}</span>
          </div>

          <!-- 상세 계약 사양 -->
          <div class="d-flex justify-space-between align-center text-caption mt-2">
            <div class="text-medium-emphasis">
              <span v-if="log?.unit_type_desc?.name" class="font-weight-medium">{{ log.unit_type_desc.name }} 타입</span>
              <span class="mx-1">|</span>
              <span>일련번호: {{ log?.serial_number || '-' }}</span>
            </div>
            <div class="font-weight-bold text-teal-darken-2">
              {{ formatPrice(log?.contractprice?.price) }}
            </div>
          </div>
        </v-list-item>
      </v-list>
    </div>
  </WidgetWrapper>
</template>

<style scoped lang="scss">
.contract-log-widget {
  height: 100%;
  overflow-y: auto;
}

.list-item {
  background-color: #ffffff;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;

  &:hover {
    background-color: rgba(var(--v-theme-on-surface), 0.02);
    border-color: rgba(var(--v-theme-on-surface), 0.1);
  }
}

body.dark-theme .list-item {
  background-color: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);

  &:hover {
    background-color: rgba(255, 255, 255, 0.06);
  }
}
</style>
