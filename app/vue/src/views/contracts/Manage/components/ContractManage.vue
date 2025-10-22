<script lang="ts" setup>
import { computed, inject, nextTick, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
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
const isDark = inject('isDark')

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
const selectedTabs = ref(['contract', 'payment', 'extra'])

// 선택된 탭 개수에 따라 컬럼 크기 계산
const selectedTabsCount = computed(() => {
  return Object.values(visibleTabs.value).filter(Boolean).length
})

const getColSize = computed(() =>
  nextTick(() => {
    if (selectedTabsCount.value === 1) return 12
    if (selectedTabsCount.value === 2) return 6
    if (selectedTabsCount.value === 3) return 4
    return 12
  }),
)

// 목록으로 돌아가기
const goBack = () => {
  if (props.fromPage) {
    router.push({ name: '계약 내역 조회', query: { page: props.fromPage } })
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
          <v-btn value="contract" @click="visibleTabs.contract = !visibleTabs.contract">
            <v-icon icon="mdi-file-document-outline" size="small" class="mr-1" />
            계약관련 내역
          </v-btn>
          <v-btn value="payment" @click="visibleTabs.payment = !visibleTabs.payment">
            <v-icon icon="mdi-cash-multiple" size="small" class="mr-1" />
            납부관련 내역
          </v-btn>
          <v-btn value="extra" @click="visibleTabs.extra = !visibleTabs.extra">
            <v-icon icon="mdi-information-outline" size="small" class="mr-1" />
            기타추가 정보
          </v-btn>
        </v-btn-toggle>
      </CCol>
    </CRow>

    <!-- 탭 컨텐츠 영역 -->
    <CRow>
      <!-- 계약 내역 탭 -->
      <transition name="tab-slide">
        <CCol v-if="visibleTabs.contract" :md="getColSize" key="contract-tab">
          <ContractInfo
            :contract="contract"
            :contractor="contractor"
            :current-address="currentAddress"
            :past-addresses="pastAddresses"
          />
        </CCol>
      </transition>

      <!-- 납부 내역 탭 -->
      <transition name="tab-slide">
        <CCol v-if="visibleTabs.payment" :md="getColSize" key="payment-tab">
          <PaymentInfo :contract="contract" />
        </CCol>
      </transition>

      <!-- 기타 정보 탭 -->
      <transition name="tab-slide">
        <CCol v-if="visibleTabs.extra" :md="getColSize" key="extra-tab">
          <AdditionalInfo :contract="contract" />
        </CCol>
      </transition>
    </CRow>

    <!-- 하단 액션 버튼 -->
    <CRow class="mt-4">
      <CCol>
        <div class="d-flex justify-content-between align-items-center">
          <v-btn color="secondary" size="small" @click="goBack">
            <v-icon icon="mdi-arrow-left" class="mr-1" />
            목록으로
          </v-btn>
          <div v-if="write_contract">
            <v-btn color="success" size="small" class="mr-2">
              <v-icon icon="mdi-pencil" class="mr-1" />
              수정
            </v-btn>
            <!--            <v-btn color="danger" size="small">-->
            <!--              <v-icon icon="mdi-delete" class="mr-1" />-->
            <!--              삭제-->
            <!--            </v-btn>-->
          </div>
        </div>
      </CCol>
    </CRow>
  </div>
</template>

<style scoped>
/* 주소 탭 슬라이드 페이드 트랜지션 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* 메인 탭 컬럼 좌우 슬라이딩 트랜지션 */
.tab-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
}

.tab-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.tab-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* CRow 부드러운 레이아웃 변경 */
.row {
  transition: all 0.3s ease-in-out;
}
</style>
