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
  rank: '',
  director_type: '',
  is_registered: '',
  is_standing: '',
  represent_type: '',
  q: '',
})

const formsCheck = computed(
  () =>
    form.rank === '' &&
    form.director_type === '' &&
    form.is_registered === '' &&
    form.is_standing === '' &&
    form.represent_type === '' &&
    form.q === '',
)

const comStore = useCompany()
const executivesCount = computed(() => comStore.executivesCount)
const getPkExecutiveRanks = computed(() => comStore.getPkExecutiveRanks)

const directorTypes = [
  { value: 'inside', label: '사내이사' },
  { value: 'outside', label: '사외이사' },
  { value: 'non_standing_director', label: '기타비상무이사' },
  { value: 'auditor', label: '감사' },
  { value: 'advisor', label: '고문/자문' },
]

const registeredOptions = [
  { value: 'true', label: '등기' },
  { value: 'false', label: '비등기' },
]

const standingOptions = [
  { value: 'true', label: '상근' },
  { value: 'false', label: '비상근' },
]

const representTypes = [
  { value: 'none', label: '해당없음' },
  { value: 'sole', label: '단독대표' },
  { value: 'joint', label: '공동대표' },
  { value: 'each', label: '각자대표' },
]

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      rank: form.rank || '',
      director_type: form.director_type || '',
      is_registered: form.is_registered !== '' ? form.is_registered : '',
      is_standing: form.is_standing !== '' ? form.is_standing : '',
      represent_type: form.represent_type || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.rank = ''
  form.director_type = ''
  form.is_registered = ''
  form.is_standing = ''
  form.represent_type = ''
  form.q = ''
  listFiltering(1)
}

defineExpose({ listFiltering })
</script>

<template>
  <CCallout color="success" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol lg="12" xl="10">
        <CRow>
          <CCol lg="4" xl="2" class="mb-3">
            <Multiselect
              v-model="form.rank"
              :options="getPkExecutiveRanks"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="임원 직위 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model="form.director_type"
              :options="directorTypes"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="상법상 지위 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model="form.is_registered"
              :options="registeredOptions"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="등기 여부 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="mb-3">
            <Multiselect
              v-model="form.is_standing"
              :options="standingOptions"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="상근 여부 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model="form.represent_type"
              :options="representTypes"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="대표권 구분 전체"
              @change="listFiltering(1)"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="2">
        <CRow class="justify-content-end">
          <CCol md="12" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.q"
                placeholder="성명, 비고 검색"
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
        <strong> 임원 수 조회 결과 : {{ numFormat(executivesCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
