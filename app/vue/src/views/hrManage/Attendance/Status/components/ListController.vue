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
  year: currentYear as number,
  department: '',
  status: '1',
  search: '',
})

const formsCheck = computed(
  () =>
    form.year === currentYear &&
    form.department === '' &&
    form.status === '1' &&
    form.search === '',
)

const comStore = useCompany()
const getPkDeparts = computed(() => comStore.getPkDeparts)

const statusOptions = [
  { value: '', label: '재직 상태 전체' },
  { value: '1', label: '근무 중 (재직)' },
  { value: '2', label: '휴직 중' },
  { value: '3', label: '퇴직신청' },
  { value: '4', label: '퇴사처리' },
]

const listFiltering = () => {
  nextTick(() => {
    emit('list-filtering', {
      year: form.year,
      department: form.department || '',
      status: form.status || '',
      search: form.search,
    })
  })
}

const resetForm = () => {
  form.year = currentYear
  form.department = ''
  form.status = '1'
  form.search = ''
  listFiltering()
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
              v-model="form.year"
              :options="years"
              placeholder="대상 연도 선택"
              @change="listFiltering"
            />
          </CCol>
          <CCol lg="4" xl="4" class="mb-3">
            <Multiselect
              v-model="form.department"
              :options="getPkDeparts"
              searchable
              placeholder="부서 전체"
              @change="listFiltering"
            />
          </CCol>
          <CCol lg="4" xl="4" class="mb-3">
            <Multiselect
              v-model="form.status"
              :options="statusOptions"
              placeholder="재직 상태 전체"
              @change="listFiltering"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="3">
        <CRow class="justify-content-end">
          <CCol md="12" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.search"
                placeholder="직원명 검색"
                aria-label="search"
                @keydown.enter="listFiltering"
              />
              <CInputGroupText @click="listFiltering">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow v-if="!formsCheck">
      <CCol class="text-right mb-2">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
