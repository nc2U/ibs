<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import { type StaffRecordFilter } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits<{
  (e: 'list-filtering', filter: StaffRecordFilter): void
}>()

const form = reactive({
  page: 1,
  com: 1,
  staff: '',
  sort: '',
  q: '',
})

const formsCheck = computed(
  () => !form.staff && !form.sort && form.q.trim() === '',
)

const comStore = useCompany()
const getAllStaffs = computed(() => comStore.getAllStaffs)

const sorts = [
  { value: 'reward', label: '포상/표창' },
  { value: 'punish', label: '징계/문책' },
]

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      staff: form.staff || '',
      sort: form.sort || '',
      q: form.q.trim(),
    })
  })
}

const clearFilter = () => {
  form.staff = ''
  form.sort = ''
  form.q = ''
}

const resetForm = () => {
  clearFilter()
  listFiltering(1)
}

defineExpose({ listFiltering, resetForm, clearFilter })
</script>

<template>
  <CCallout color="primary" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol lg="12" xl="9">
        <CRow>
          <CCol lg="6" xl="6" class="mb-3">
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
          <CCol lg="6" xl="6" class="pb-0 mb-3">
            <Multiselect
              v-model="form.sort"
              :options="sorts"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="상벌 구분 (상벌 탭 전용)"
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
                placeholder="직원명, 기관명, 자격명, 사유 등 검색"
                aria-label="search"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText
                role="button"
                style="cursor: pointer"
                @click="listFiltering(1)"
              >
                검색
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol v-if="!formsCheck" class="text-end mb-2">
        <v-btn color="info" size="small" variant="flat" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
