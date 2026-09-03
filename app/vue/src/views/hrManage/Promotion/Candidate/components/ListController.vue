<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits(['list-filtering'])

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 6 }, (_, i) => ({
  value: currentYear - 3 + i,
  label: `${currentYear - 3 + i}년`,
}))

const statusOptions = [
  { value: '', label: '심사 상태 전체' },
  { value: 'candidate', label: '심사 대상' },
  { value: 'recommended', label: '부서 추천' },
  { value: 'approved', label: '승진 확정' },
  { value: 'rejected', label: '심사 탈락' },
  { value: 'hold', label: '심사 보류' },
]

const form = reactive({
  page: 1,
  com: 1,
  eval_year: currentYear as number | '',
  status: '',
  policy: '',
  staff: '',
  q: '',
})

const formsCheck = computed(
  () =>
    form.eval_year === currentYear &&
    form.status === '' &&
    form.policy === '' &&
    form.staff === '' &&
    form.q === '',
)

const comStore = useCompany()
const promotionCandidatesCount = computed(() => comStore.promotionCandidatesCount)
const allPromotionPolicyList = computed(() => comStore.allPromotionPolicyList)
const getAllStaffs = computed(() => comStore.getAllStaffs)

const policyOptions = computed(() => [
  { value: '', label: '승급 정책 전체' },
  ...allPromotionPolicyList.value.map(p => ({
    value: p.pk as number,
    label: `${p.current_grade_code} → ${p.target_grade_code}`,
  })),
])

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      eval_year: form.eval_year || '',
      status: form.status || '',
      policy: form.policy || '',
      staff: form.staff || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.eval_year = currentYear
  form.status = ''
  form.policy = ''
  form.staff = ''
  form.q = ''
  listFiltering(1)
}

defineExpose({ listFiltering })
</script>

<template>
  <CCallout color="primary" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol lg="12" xl="9">
        <CRow>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.eval_year"
              :options="years"
              placeholder="심사 연도 선택"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.status"
              :options="statusOptions"
              placeholder="심사 상태 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.policy"
              :options="policyOptions"
              placeholder="승급 정책 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.staff"
              :options="getAllStaffs"
              searchable
              placeholder="대상 직원 전체"
              @change="listFiltering(1)"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="3">
        <CRow class="justify-content-end">
          <CCol md="12" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.q"
                placeholder="직원명, 심의 의견 검색"
                aria-label="search"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="p-2 pl-3">
        <strong>
          승급 심사 대상 내역 조회 결과 : {{ numFormat(promotionCandidatesCount) }} 건
        </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
