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
  sort: '',
  q: '',
})

const formsCheck = computed(() => form.staff === '' && form.sort === '' && form.q === '')

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
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.staff = ''
  form.sort = ''
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
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol v-if="!formsCheck" class="text-right mb-2">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
