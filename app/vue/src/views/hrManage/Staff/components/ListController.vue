<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useCompany } from '@/store/pinia/company'
import { bgLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits(['list-filtering'])

const form = reactive({
  page: 1,
  com: 1,
  sort: '',
  dep: '',
  gra: '',
  pos: '',
  dut: '',
  sts: '1',
  q: '',
})

const formsCheck = computed(
  () =>
    form.sort === '' &&
    form.dep === '' &&
    form.gra === '' &&
    form.pos === '' &&
    form.dut === '' &&
    form.sts === '1' &&
    form.q === '',
)

const comStore = useCompany()
const staffsCount = computed(() => comStore.staffsCount)
const getPkDeparts = computed(() => comStore.getPkDeparts)
const getPkGrades = computed(() => comStore.getPkGrades)
const getPkPositions = computed(() => comStore.getPkPositions)
const getPkDutys = computed(() => comStore.getPkDutys)

const getSorts = [
  { value: '1', label: '임원' },
  { value: '2', label: '직원' },
]

const getStatus = [
  { value: '1', label: '근무 중' },
  { value: '2', label: '휴직 중' },
  { value: '3', label: '퇴직신청' },
  { value: '4', label: '퇴사처리' },
]

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      sort: form.sort || '',
      dep: form.dep || '',
      gra: form.gra || '',
      pos: form.pos || '',
      dut: form.dut || '',
      sts: form.sts || '',
      q: form.q,
    })
  })
}

const resetForm = () => {
  form.sort = ''
  form.dep = ''
  form.gra = ''
  form.pos = ''
  form.dut = ''
  form.sts = '1'
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
              v-model.number="form.sort"
              :options="getSorts"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="임직원 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model.number="form.dep"
              :options="getPkDeparts"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="부서 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model.number="form.gra"
              :options="getPkGrades"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="직급 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="mb-3">
            <Multiselect
              v-model.number="form.pos"
              :options="getPkPositions"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="직위 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model.number="form.dut"
              :options="getPkDutys"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="직책 전체"
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol lg="4" xl="2" class="pb-0 mb-3">
            <Multiselect
              v-model.number="form.sts"
              :options="getStatus"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="상태 전체"
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
                placeholder="성명, 주민번호, 연락처, 이메일 검색"
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
        <strong> 직원 수 조회 결과 : {{ numFormat(staffsCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
