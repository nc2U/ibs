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

const form = reactive({
  page: 1,
  com: 1,
  staff: '',
  year: currentYear as number | '',
  q: '',
})

const formsCheck = computed(() => form.staff === '' && form.year === currentYear && form.q === '')

const comStore = useCompany()
const staffLeaveQuotasCount = computed(() => comStore.staffLeaveQuotasCount)
const getAllStaffs = computed(() => comStore.getAllStaffs)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      staff: form.staff || '',
      year: form.year || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.staff = ''
  form.year = currentYear
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
          <CCol lg="6" xl="6" class="mb-3">
            <Multiselect
              v-model="form.year"
              :options="years"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              placeholder="대상 연도 선택"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="6" xl="6" class="pb-0 mb-3">
            <Multiselect
              v-model="form.staff"
              :options="getAllStaffs"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
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
                placeholder="직원명, 비고 검색"
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
        <strong> 연차 부여 현황 조회 결과 : {{ numFormat(staffLeaveQuotasCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
