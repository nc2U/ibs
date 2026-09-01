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

const periodOptions = [
  { value: '', label: '평가 주기 전체' },
  { value: 'yearly', label: '연간' },
  { value: '1H', label: '상반기' },
  { value: '2H', label: '하반기' },
]

const gradeOptions = [
  { value: '', label: '평가 등급 전체' },
  { value: 'S', label: 'S (탁월)' },
  { value: 'A', label: 'A (우수)' },
  { value: 'B', label: 'B (보통)' },
  { value: 'C', label: 'C (미흡)' },
  { value: 'D', label: 'D (불량)' },
]

const form = reactive({
  page: 1,
  com: 1,
  eval_year: currentYear as number | '',
  eval_period: '',
  grade: '',
  staff: '',
  q: '',
})

const formsCheck = computed(
  () =>
    form.eval_year === currentYear &&
    form.eval_period === '' &&
    form.grade === '' &&
    form.staff === '' &&
    form.q === '',
)

const comStore = useCompany()
const staffEvaluationsCount = computed(() => comStore.staffEvaluationsCount)
const getAllStaffs = computed(() => comStore.getAllStaffs)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      eval_year: form.eval_year || '',
      eval_period: form.eval_period || '',
      grade: form.grade || '',
      staff: form.staff || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.eval_year = currentYear
  form.eval_period = ''
  form.grade = ''
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
              placeholder="평가 연도 선택"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.eval_period"
              :options="periodOptions"
              placeholder="평가 주기 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.grade"
              :options="gradeOptions"
              placeholder="평가 등급 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.staff"
              :options="getAllStaffs"
              searchable
              placeholder="피평가자 전체"
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
                placeholder="직원명, 업적 요약, 의견 검색"
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
        <strong> 인사/업적 평가 내역 조회 결과 : {{ numFormat(staffEvaluationsCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
