<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits(['list-filtering'])

const form = reactive({
  page: 1,
  com: 1,
  staff: '',
  order_type: '',
  department: '',
  q: '',
})

const formsCheck = computed(
  () => form.staff === '' && form.order_type === '' && form.department === '' && form.q === '',
)

const comStore = useCompany()
const personnelOrdersCount = computed(() => comStore.personnelOrdersCount)
const getPkDeparts = computed(() => comStore.getPkDeparts)
const getAllStaffs = computed(() => comStore.getAllStaffs)

const orderTypes = [
  { value: '10', label: '채용/신규입사' },
  { value: '20', label: '승진/승급' },
  { value: '30', label: '부서이동(전보)' },
  { value: '40', label: '보직임면/겸직' },
  { value: '50', label: '휴직' },
  { value: '51', label: '복직' },
  { value: '60', label: '파견/전적' },
  { value: '70', label: '포상/표창' },
  { value: '80', label: '징계/문책' },
  { value: '90', label: '퇴사/면직' },
]

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      staff: form.staff || '',
      order_type: form.order_type || '',
      department: form.department || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.staff = ''
  form.order_type = ''
  form.department = ''
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
          <CCol lg="4" xl="4" class="pb-0 mb-3">
            <Multiselect
              v-model="form.order_type"
              :options="orderTypes"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="발령 구분 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="4" class="pb-0 mb-3">
            <Multiselect
              v-model="form.department"
              :options="getPkDeparts"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="발령 부서 전체"
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
                placeholder="직원명, 발령호수, 사유 검색"
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
        <strong> 발령 이력 조회 결과 : {{ numFormat(personnelOrdersCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
