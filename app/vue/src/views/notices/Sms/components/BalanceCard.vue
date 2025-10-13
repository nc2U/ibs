<script lang="ts" setup>
import { ref, computed } from 'vue'
import { CAlert } from '@coreui/vue'

// Props
interface Props {
  balance?: number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  balance: 0,
  loading: false,
})

// Emits
const emit = defineEmits<{
  refresh: []
}>()

// 열림/닫힘 상태
const visible = ref(false)

// 잔액 새로고침
const handleRefresh = () => {
  emit('refresh')
}

// 토글
const toggle = () => {
  visible.value = !visible.value
  // 열릴 때 자동으로 잔액 조회
  if (visible.value && !props.loading) {
    handleRefresh()
  }
}

// 잔액 포맷팅
const formatBalance = (amount: number) => {
  return amount.toLocaleString('ko-KR')
}

// 잔액 부족 여부 (10,000원 미만)
const isLowBalance = computed(() => props.balance < 10000)
</script>

<template>
  <CCard class="mb-3">
    <CCardHeader
      class="d-flex justify-content-between align-items-center"
      style="cursor: pointer; height: 48px"
      @click="toggle"
    >
      <CCol class="d-flex align-items-center">
        <CIcon name="cilWallet" class="me-2" />
        <strong>잔액 확인</strong>
        <CBadge v-if="visible && isLowBalance" color="danger" class="ms-2"> 잔액 부족 </CBadge>
      </CCol>
      <v-icon :icon="visible ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
    </CCardHeader>
    <CCollapse :visible="visible">
      <CCardBody>
        <CRow class="align-items-center">
          <CCol xl="4" class="mb-2">
            <div class="d-flex align-items-center">
              <div class="me-3">
                <CIcon name="cilWallet" size="xl" />
              </div>
              <div>
                <div class="text-medium-emphasis small">현재 잔액</div>
                <div class="fs-5 fw-semibold">
                  <span :class="{ 'text-danger': isLowBalance }">
                    {{ formatBalance(balance) }}원
                  </span>
                  <CSpinner v-if="loading" size="sm" class="ms-2" />
                </div>
                <div v-if="isLowBalance" class="text-danger small mt-1">
                  <CIcon name="cilWarning" size="sm" class="me-1" />
                  잔액이 부족합니다. 충전이 필요합니다.
                </div>
              </div>
            </div>
          </CCol>
          <CCol xl="2" class="text-end">
            <v-btn
              color="primary"
              variant="outlined"
              size="small"
              @click.stop="handleRefresh"
              :disabled="loading"
            >
              새로고침
            </v-btn>
          </CCol>
          <CCol xl="6" class="d-none d-xl-block">
            <v-alert color="secondary" variant="tonal">
              ■ 요금 충전 및 관련 정보:<br />https://console.iwinv.kr/msg/plan<br />
              ※ 자동 충전 카드 등록 중
            </v-alert>
          </CCol>
        </CRow>
      </CCardBody>
    </CCollapse>
  </CCard>
</template>
