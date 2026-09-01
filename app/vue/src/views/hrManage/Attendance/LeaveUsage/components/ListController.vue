<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const emit = defineEmits(['list-filtering'])

const leaveTypeOptions = [
  { value: '', label: '휴가 구분 전체' },
  { value: 'annual', label: '연차 (1일)' },
  { value: 'half_am', label: '오전 반차 (0.5일)' },
  { value: 'half_pm', label: '오후 반차 (0.5일)' },
  { value: 'quarter', label: '반반차 (0.25일)' },
  { value: 'official', label: '공가/예비군' },
  { value: 'sick', label: '병가' },
  { value: 'condolence', label: '경조 휴가' },
  { value: 'reward', label: '포상 휴가' },
  { value: 'substitute', label: '대체 휴가' },
  { value: 'other', label: '기타 휴가' },
]

const cancelOptions = [
  { value: '', label: '상태 전체' },
  { value: 'false', label: '정상 승인/사용' },
  { value: 'true', label: '취소됨' },
]

const form = reactive({
  page: 1,
  com: 1,
  staff: '',
  leave_type: '',
  start_date: '',
  end_date: '',
  is_cancelled: '',
  q: '',
})

const formsCheck = computed(
  () =>
    form.staff === '' &&
    form.leave_type === '' &&
    form.start_date === '' &&
    form.end_date === '' &&
    form.is_cancelled === '' &&
    form.q === '',
)

const comStore = useCompany()
const staffLeaveUsagesCount = computed(() => comStore.staffLeaveUsagesCount)
const getAllStaffs = computed(() => comStore.getAllStaffs)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      staff: form.staff || '',
      leave_type: form.leave_type || '',
      start_date: form.start_date || '',
      end_date: form.end_date || '',
      is_cancelled: form.is_cancelled,
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.staff = ''
  form.leave_type = ''
  form.start_date = ''
  form.end_date = ''
  form.is_cancelled = ''
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
          <CCol lg="3" xl="3" class="mb-3">
            <Multiselect
              v-model="form.leave_type"
              :options="leaveTypeOptions"
              placeholder="휴가 구분 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <DatePicker
              v-model="form.start_date"
              placeholder="시작일 (이후)"
              @update:model-value="listFiltering(1)"
            />
          </CCol>
          <CCol lg="3" xl="3" class="mb-3">
            <DatePicker
              v-model="form.end_date"
              placeholder="종료일 (이전)"
              @update:model-value="listFiltering(1)"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="3">
        <CRow class="justify-content-end">
          <CCol md="6" xl="6" class="mb-3">
            <Multiselect
              v-model="form.is_cancelled"
              :options="cancelOptions"
              placeholder="상태"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol md="6" xl="6" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.q"
                placeholder="사유 검색"
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
        <strong> 휴가 사용 내역 조회 결과 : {{ numFormat(staffLeaveUsagesCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
