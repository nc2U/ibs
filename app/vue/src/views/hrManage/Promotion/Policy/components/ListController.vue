<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits(['list-filtering'])

const activeOptions = [
  { value: '', label: '사용 여부 전체' },
  { value: 'true', label: '사용 중' },
  { value: 'false', label: '미사용' },
]

const form = reactive({
  page: 1,
  com: 1,
  current_grade: '',
  target_grade: '',
  is_active: '',
  q: '',
})

const formsCheck = computed(
  () =>
    form.current_grade === '' &&
    form.target_grade === '' &&
    form.is_active === '' &&
    form.q === '',
)

const comStore = useCompany()
const promotionPoliciesCount = computed(() => comStore.promotionPoliciesCount)
const getPkGrades = computed(() => comStore.getPkGrades)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      current_grade: form.current_grade || '',
      target_grade: form.target_grade || '',
      is_active: form.is_active,
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.current_grade = ''
  form.target_grade = ''
  form.is_active = ''
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
          <CCol lg="4" xl="4" class="mb-3">
            <Multiselect
              v-model="form.current_grade"
              :options="getPkGrades"
              placeholder="현재 직급 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="4" class="mb-3">
            <Multiselect
              v-model="form.target_grade"
              :options="getPkGrades"
              placeholder="승급 대상 직급 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="4" class="mb-3">
            <Multiselect
              v-model="form.is_active"
              :options="activeOptions"
              placeholder="사용 여부 전체"
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
                placeholder="필수 역량, 결격 사유, 설명 검색"
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
        <strong> 승급 정책 설정 내역 조회 결과 : {{ numFormat(promotionPoliciesCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
