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
const limitCount = ref<number>(5)

const fetchContractLogs = async () => {
  loading.value = true
  try {
    const res = await api.get('/contract/recent-logs/')
    // 응답이 없는 경우 방어
    if (!res || !res.data) {
      contractLogs.value = []
      return
    }

    // 결과 검사 및 배열 여부 체크
    let data: any[] = []
    if (res.data.results && Array.isArray(res.data.results)) {
      data = res.data.results
    } else if (Array.isArray(res.data)) {
      data = res.data
    }

    contractLogs.value = data
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
    '1': { color: '#d4f940', text: '청약' },
    '2': { color: 'success', text: '계약' },
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
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="fetchContractLogs"
  >
    <div class="contract-log-widget">
      <!-- 5개 / 10개 목록 갯수 토글 -->
      <div class="d-flex align-center justify-space-between mb-3">
        <span class="text-medium-emphasis">실시간 분양 계약 등록 현황</span>
        <v-btn-toggle
          v-model="limitCount"
          mandatory
          density="compact"
          color="primary"
          class="activity-toggle rounded-lg"
          variant="outlined"
        >
          <v-btn :value="5" size="small" class="font-weight-medium px-2"> 5개 보기 </v-btn>
          <v-btn :value="10" size="small" class="font-weight-medium px-2"> 10개 보기 </v-btn>
        </v-btn-toggle>
      </div>

      <div
        v-if="loading && contractLogs.length === 0"
        class="d-flex align-center justify-center py-8"
      >
        <v-progress-circular indeterminate color="primary" size="24" />
      </div>

      <div
        v-else-if="contractLogs.length === 0"
        class="d-flex align-center justify-center py-8 text-grey text-caption"
      >
        최근 계약 변동 내역이 없습니다.
      </div>

      <!-- 계약 변동 로그 리스트 -->
      <v-list v-else density="compact" class="pa-0 bg-transparent">
        <v-list-item
          v-for="log in contractLogs.slice(0, limitCount)"
          :key="log?.pk"
          class="mb-2 rounded-lg list-item pa-3"
          variant="flat"
        >
          <!-- 소속 프로젝트 정보 -->
          <div class="d-flex justify-space-between align-center">
            <span class="mt-0 strong text-muted text-caption">
              <v-icon icon="mdi-office-building-marker-outline" size="12" class="mr-1" />
              {{ log?.project_name || '프로젝트 미지정' }}
            </span>
            <!-- 시간 경과 -->
            <span class="text-caption text-grey-darken-1">
              {{ log?.created ? elapsedTime(log.created) : '' }}
            </span>
          </div>
          <div class="d-flex justify-space-between align-center mt-1">
            <!-- 동호수 & 계약자명 -->
            <div class="d-flex align-center text-body">
              <v-chip
                v-if="log?.contractor_status"
                size="x-small"
                :color="getStatusTheme(log.contractor_status).color"
                class="mr-2 font-weight-bold"
                variant="flat"
              >
                {{ getStatusTheme(log.contractor_status).text }}
              </v-chip>
              <span class="text-body-2 font-weight-bold text-slate-800">
                <span>
                  <router-link
                    :to="{ name: '계약 상세 보기', params: { contractorId: log.contractor_id } }"
                  >
                    <span v-if="log?.house_unit_name">{{ log.house_unit_name }}</span>
                    <span v-else>동호수 미정</span>
                  </router-link>
                </span>
                <span v-if="log?.contractor_name"> · {{ log.contractor_name }}</span>
              </span>

              <span class="text-medium-emphasis text-caption ml-2">
                <span v-if="log?.unit_type_name" class="font-weight-medium">
                  {{ log.unit_type_name }} 타입
                </span>
                <span class="mx-1">|</span>
                <span>일련번호: {{ log?.serial_number || '-' }}</span>
              </span>
            </div>

            <div v-if="log?.price" class="font-weight-bold text-teal-darken-2">
              {{ formatPrice(log?.price) }}
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

.activity-toggle {
  height: 24px !important;
  background-color: rgba(var(--v-theme-on-surface), 0.02);

  :deep(.v-btn) {
    height: 24px !important;
    min-width: unset;
  }
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

body.dark-theme {
  .list-item {
    background-color: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.08);

    &:hover {
      background-color: rgba(255, 255, 255, 0.06);
    }
  }

  .activity-toggle {
    :deep(.v-btn) {
      color: rgba(255, 255, 255, 0.8) !important;
      &.v-btn--selected {
        color: rgb(var(--v-theme-primary)) !important;
      }
    }
  }
}
</style>
