<script lang="ts" setup>
import { ref } from 'vue'

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

// 잔액 새로고침
const handleRefresh = () => {
  emit('refresh')
}

// 잔액 포맷팅
const formatBalance = (amount: number) => {
  return amount.toLocaleString('ko-KR')
}

// 잔액 부족 여부 (10,000원 미만)
const isLowBalance = ref(props.balance < 10000)
</script>

<template>
  <CCard class="mb-3">
    <CCardBody class="py-3">
      <CRow class="align-items-center">
        <CCol :md="8">
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
        <CCol :md="4" class="text-end">
          <CButton
            color="primary"
            variant="outline"
            size="sm"
            @click="handleRefresh"
            :disabled="loading"
          >
            <CIcon name="cilReload" class="me-1" />
            새로고침
          </CButton>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>
</template>
