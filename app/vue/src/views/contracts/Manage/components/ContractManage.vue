<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useContract } from '@/store/pinia/contract'
import type { Contract, Contractor } from '@/store/types/contract'
import ContractInfo from './manages/ContractInfo.vue'
import PaymentInfo from './manages/PaymentInfo.vue'
import AdditionalInfo from './manages/AdditionalInfo.vue'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<Contract>, default: null },
  contractor: { type: Object as PropType<Contractor>, default: null },
  fromPage: { type: [Number, null] as PropType<number | null>, default: null },
})

const router = useRouter()

const contStore = useContract()
const addressList = computed(() => contStore.contAddressList)
const currentAddress = computed(() => addressList.value.find(addr => addr.is_current) as any)
const pastAddresses = computed(() => addressList.value.filter(addr => !addr.is_current))

// 계약 정보가 있는지 확인
const hasContract = computed(() => !!props.contract && !!props.contractor)

// 탭 표시 상태
const visibleTabs = ref({
  contract: true, // 계약 내역
  payment: true, // 납부 내역
  extra: true, // 기타 정보
})

// v-btn-toggle 선택된 탭들
const selectedTabs = computed({
  get: () => {
    return Object.entries(visibleTabs.value)
      .filter(([_, visible]) => visible)
      .map(([key, _]) => key)
  },
  set: newValue => {
    // 각 탭의 표시 상태를 업데이트 (객체 전체를 교체하여 반응성 보장)
    visibleTabs.value = {
      contract: newValue.includes('contract'),
      payment: newValue.includes('payment'),
      extra: newValue.includes('extra'),
    }
  },
})

// 선택된 탭 개수에 따라 컬럼 크기 계산
const selectedTabsCount = computed(() => {
  return Object.values(visibleTabs.value).filter(Boolean).length
})

const getColSize = computed(() => {
  if (selectedTabsCount.value === 1) return 12
  if (selectedTabsCount.value === 2) return 6
  if (selectedTabsCount.value === 3) return 4
  return 12
})

// 목록으로 돌아가기
const goBack = () => {
  if (props.fromPage) {
    router.push({
      name: '계약 내역 조회',
      query: { page: props.fromPage, highlight_id: props.contract?.pk },
    })
  } else {
    router.push({ name: '계약 내역 조회' })
  }
}
</script>

<template>
  <div v-if="!hasContract" class="text-center py-5">
    <p class="text-muted">계약자를 선택하여 계약 정보를 조회하세요.</p>
  </div>

  <div v-else>
    <!-- 탭 선택 영역 -->
    <CRow class="mb-3">
      <CCol>
        <v-btn-toggle v-model="selectedTabs" multiple density="compact" rounded="0">
          <v-btn value="contract">
            <v-icon icon="mdi-file-document-outline" size="small" class="mr-1" />
            계약관련 내역
          </v-btn>
          <v-btn value="payment">
            <v-icon icon="mdi-cash-multiple" size="small" class="mr-1" />
            납부관련 내역
          </v-btn>
          <v-btn value="extra">
            <v-icon icon="mdi-information-outline" size="small" class="mr-1" />
            기타추가 정보
          </v-btn>
        </v-btn-toggle>
      </CCol>
    </CRow>

    <!-- 탭 컨텐츠 영역 -->
    <CRow>
      <!-- 계약 내역 탭 -->
      <CCol v-if="visibleTabs.contract" :xl="getColSize" :key="`contract-${selectedTabsCount}`">
        <ContractInfo
          :contract="contract"
          :contractor="contractor"
          :current-address="currentAddress"
          :past-addresses="pastAddresses"
        />
      </CCol>

      <!-- 납부 내역 탭 -->
      <CCol v-if="visibleTabs.payment" :xl="getColSize" :key="`payment-${selectedTabsCount}`">
        <PaymentInfo :contract="contract" />
      </CCol>

      <!-- 기타 정보 탭 -->
      <CCol v-if="visibleTabs.extra" :xl="getColSize" :key="`extra-${selectedTabsCount}`">
        <AdditionalInfo :contract="contract" />
      </CCol>
    </CRow>

    <!-- 하단 액션 버튼 -->
    <CRow class="mt-4">
      <CCol>
        <div class="d-flex justify-content-between align-items-center">
          <v-btn color="secondary" size="small" @click="goBack">
            <v-icon icon="mdi-arrow-left" class="mr-1" />
            목록으로
          </v-btn>
        </div>
      </CCol>
    </CRow>
  </div>
</template>
