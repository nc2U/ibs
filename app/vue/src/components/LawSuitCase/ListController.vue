<script lang="ts" setup>
import { computed, inject, nextTick, onBeforeMount, type PropType, ref } from 'vue'
import { type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
import { courtChoices } from './components/court'
import Multiselect from '@vueform/multiselect'

const props = defineProps({
  comFrom: { type: Boolean, default: false },
  company: { type: Number, default: null },
  project: { type: Number, default: null },
  projects: { type: Array as PropType<{ label: string; value: number }[]>, default: () => [] },
  caseFilter: { type: Object, required: true },
})
const emit = defineEmits(['list-filter'])

const disabled = computed(() => (props.comFrom ? !props.company : !props.project))

const form = ref<SuitCaseFilter>({
  limit: '',
  issue_project: '',
  is_real_dev: '',
  court: '',
  related_case: '',
  sort: '',
  level: '',
  in_progress: '',
  search: '',
  page: 1,
})

const formsCheck = computed(() => {
  const a = form.value.limit === ''
  const b = props.comFrom ? form.value.issue_project === '' : true
  const c = !form.value.court
  const d = !form.value.related_case
  const e = form.value.sort === ''
  const f = form.value.level === ''
  const g = form.value.in_progress === ''
  const h = form.value.search === ''
  return a && b && c && d && e && f && g && h
})

const docStore = useDocs()
const suitcaseCount = computed(() => docStore.suitcaseCount)
const getSuitCase = computed(() => docStore.getSuitCase)

const listFiltering = (page = 1) => {
  nextTick(() => {
    form.value.page = page
    emit('list-filter', { ...form.value })
  })
}

const firstSorting = (event: { target: { value: number | null } }) => {
  const val = event.target.value
  if (!val) form.value.is_real_dev = 'false'
  else {
    form.value.issue_project = val
    form.value.is_real_dev = 'true'
  }
  listFiltering(1)
}

const courtChange = (court: string) => (form.value.court = court)
const searchChange = (search: string) => (form.value.search = search)
const relatedChange = (related: number) => (form.value.related_case = related)
const projectChange = (project: number | null) => (form.value.project = project ?? '')
const sortChange = () => {
  form.value.level = ''
  listFiltering(1)
}

const resetForm = (is_filter = true) => {
  form.value.limit = ''
  form.value.issue_project = ''
  form.value.is_real_dev = ''
  form.value.court = ''
  form.value.related_case = ''
  form.value.sort = ''
  form.value.level = ''
  form.value.in_progress = ''
  form.value.search = ''
  if (is_filter) listFiltering(1)
}

defineExpose({
  listFiltering,
  courtChange,
  searchChange,
  relatedChange,
  projectChange,
  resetForm,
})

onBeforeMount(() => {
  if (props.caseFilter) {
    form.value.limit = props.caseFilter.limit
    form.value.issue_project = props.caseFilter.issue_project
    form.value.is_real_dev = props.caseFilter.is_real_dev
    form.value.court = props.caseFilter.court
    form.value.related_case = props.caseFilter.related_case
    form.value.sort = props.caseFilter.sort
    form.value.level = props.caseFilter.level
    form.value.in_progress = props.caseFilter.in_progress
    form.value.search = props.caseFilter.search
    form.value.page = props.caseFilter.page
  }
})
</script>

<template>
  <CCallout :color="comFrom ? 'primary' : 'success'" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol :lg="comFrom ? 6 : 5">
        <CRow>
          <CCol :md="comFrom ? 3 : 4" class="mb-3">
            <CFormSelect
              v-model.number="form.limit"
              @change="listFiltering(1)"
              :disabled="disabled"
            >
              <option value="">표시 개수</option>
              <option :value="10" :disabled="form.limit === '' || form.limit === 10">10 개</option>
              <option :value="30" :disabled="form.limit === 30">30 개</option>
              <option :value="50" :disabled="form.limit === 50">50 개</option>
            </CFormSelect>
          </CCol>
          <CCol v-if="comFrom" :md="comFrom ? 3 : 4" class="mb-3">
            <CFormSelect v-model="form.issue_project" @change="firstSorting" :disabled="disabled">
              <option value="">본사</option>
              <option v-for="proj in projects" :key="proj.value" :value="proj.value">
                {{ proj.label }}
              </option>
            </CFormSelect>
          </CCol>
          <CCol :md="comFrom ? 3 : 4" class="mb-3">
            <Multiselect
              v-model="form.court"
              :options="courtChoices"
              placeholder="관할법원"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              @change="listFiltering(1)"
              :disabled="disabled"
            />
          </CCol>

          <CCol :md="comFrom ? 3 : 4" class="mb-3">
            <Multiselect
              v-model="form.related_case"
              :options="getSuitCase"
              placeholder="관련사건"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              @change="listFiltering(1)"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol :lg="comFrom ? 6 : 7">
        <CRow>
          <CCol md="4" lg="3" class="mb-3">
            <CFormSelect v-model="form.sort" @change="sortChange" :disabled="disabled">
              <option value="">사건유형 선택</option>
              <option value="1">민사</option>
              <option value="2">형사</option>
              <option value="3">행정</option>
              <option value="4">신청</option>
              <option value="5">집행</option>
            </CFormSelect>
          </CCol>
          <CCol md="4" lg="3" class="mb-3">
            <CFormSelect v-model="form.level" @change="listFiltering(1)" :disabled="disabled">
              <option value="">사건심급 선택</option>
              <option v-if="!form.sort || form.sort <= '3'" value="1">1심</option>
              <option v-if="!form.sort || form.sort <= '3'" value="2">2심</option>
              <option v-if="!form.sort || form.sort <= '3'" value="3">3심</option>
              <option v-if="!form.sort || form.sort === '2'" value="4">고소/수사</option>
              <option v-if="!form.sort || form.sort === '4'" value="5">신청</option>
              <option v-if="!form.sort || form.sort === '4'" value="6">항고/이의</option>
              <option v-if="!form.sort || form.sort === '5'" value="7">압류/추심</option>
              <option v-if="!form.sort || form.sort === '5'" value="8">정지/이의</option>
            </CFormSelect>
          </CCol>
          <CCol md="4" lg="3" class="mb-3">
            <CFormSelect v-model="form.in_progress" @change="listFiltering(1)" :disabled="disabled">
              <option value="">전체 사건</option>
              <option :value="true">진행 사건</option>
              <option :value="false">종결 사건</option>
            </CFormSelect>
          </CCol>

          <CCol md="12" lg="3" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="Search"
                @keydown.enter="listFiltering(1)"
                :disabled="disabled"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol color="warning" class="p-2 pl-3">
        <strong> 사건 수 조회 결과 : {{ numFormat(suitcaseCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
