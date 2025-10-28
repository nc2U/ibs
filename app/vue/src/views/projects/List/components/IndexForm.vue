<script setup lang="ts">
import { computed, onBeforeMount, onUpdated, type PropType, reactive, ref } from 'vue'
import { useStore } from '@/store'
import { type Project } from '@/store/types/project'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import { useProject } from '@/store/pinia/project'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_project } from '@/utils/pageAuth'
import Datepicker from '@vuepic/vue-datepicker'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IssueProjectForm from './IssueProjectForm.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  project: { type: Object as PropType<Project>, default: null },
  getProjects: {
    type: Array as PropType<{ value: number | undefined; label: string }[]>,
    default: () => [],
  },
})

const emit = defineEmits(['to-submit', 'reset-form', 'close', 'get-project'])

const projStore = useProject()
const getAllProjects = async (sort: '1' | '2' | '3') => {
  emit('get-project', sort)
  await projStore.fetchProject(props.project?.pk as number)
  formDataSetup()
}

const refIssueForm = ref()

const form = reactive<Project>({
  pk: undefined,
  company: null,
  issue_project: null,
  name: '',
  order: null,
  kind: '',
  start_year: '',
  is_direct_manage: false,
  is_returned_area: false,
  is_unit_set: false,
  // 사업 일정 필드 (필수)
  monthly_aggr_start_date: '',
  construction_start_date: '',
  construction_period_months: null,
  location: '',
  area_usage: '',
  build_size: '',
  num_unit: null,
  buy_land_extent: null,
  scheme_land_extent: null,
  donation_land_extent: null,
  on_floor_area: null,
  under_floor_area: null,
  total_floor_area: null,
  build_area: null,
  floor_area_ratio: null,
  build_to_land_ratio: null,
  num_legal_parking: null,
  num_planed_parking: null,
})

const sortOptins = [
  { value: '1', label: '공동주택(아파트)' },
  { value: '2', label: '공동주택(타운하우스)' },
  { value: '3', label: '주상복합(아파트)' },
  { value: '4', label: '주상복합(오피스텔)' },
  { value: '5', label: '근린생활시설' },
  { value: '6', label: '생활형숙박시설' },
  { value: '7', label: '지식산업센터' },
  { value: '8', label: '기타' },
]

const validated = ref(false)

const confirmText = computed(() => (props.project ? '변경' : '등록'))
const btnClass = computed(() => (props.project ? 'success' : 'primary'))

const formsCheck = computed(() => {
  if (props.project) {
    const a = form.issue_project === props.project.issue_project
    const b = form.name === props.project.name
    const c = form.order === props.project.order
    const d = form.kind === props.project.kind
    const e = form.start_year === props.project.start_year
    const f = form.is_direct_manage === props.project.is_direct_manage
    const g = form.is_returned_area === props.project.is_returned_area
    const h = form.is_unit_set === props.project.is_unit_set
    const i = form.monthly_aggr_start_date === props.project.monthly_aggr_start_date
    const j = form.construction_start_date === props.project.construction_start_date
    const k = form.construction_period_months === props.project.construction_period_months
    const l = form.location === props.project.location
    const m = form.area_usage === props.project.area_usage
    const n = form.build_size === props.project.build_size
    const o = form.num_unit === props.project.num_unit
    const p = form.buy_land_extent === props.project.buy_land_extent
    const q = form.scheme_land_extent === props.project.scheme_land_extent
    const r = form.donation_land_extent === props.project.donation_land_extent
    const s = form.on_floor_area === props.project.on_floor_area
    const t = form.under_floor_area === props.project.under_floor_area
    const u = form.total_floor_area === props.project.total_floor_area
    const v = form.build_area === props.project.build_area
    const w = form.floor_area_ratio === props.project.floor_area_ratio
    const x = form.build_to_land_ratio === props.project.build_to_land_ratio
    const y = form.num_legal_parking === props.project.num_legal_parking
    const z = form.num_planed_parking === props.project.num_planed_parking

    const group1 = a && b && c && d && e && f && g && h && i
    const group2 = j && k && l && m && n && o && p && q && r
    const group3 = s && t && u && v && w && x && y && z

    return group1 && group2 && group3
  } else return false
})

const refDelModal = ref()
const refAlertModal = ref()
const refConfirmModal = ref()
const refPostCode = ref()

const address2 = ref()

const store = useStore()

const onSubmit = (event: Event) => {
  if (write_project.value) {
    const e = event.currentTarget as HTMLSelectElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()
      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  if (!form.order) form.order = 100
  emit('to-submit', { ...form })
  validated.value = false
  refConfirmModal.value.close()
}

const deleteProject = () => {
  if (write_project.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const formDataSetup = () => {
  if (props.project) {
    form.pk = props.project.pk
    form.issue_project = props.project.issue_project
    form.name = props.project.name
    form.order = props.project.order
    form.kind = props.project.kind
    form.start_year = props.project.start_year
    form.is_direct_manage = props.project.is_direct_manage
    form.is_returned_area = props.project.is_returned_area
    form.is_unit_set = props.project.is_unit_set
    // 사업 일정 필드
    form.monthly_aggr_start_date = props.project.monthly_aggr_start_date
    form.construction_start_date = props.project.construction_start_date
    form.construction_period_months = props.project.construction_period_months
    form.location = props.project.location
    form.area_usage = props.project.area_usage
    form.build_size = props.project.build_size
    form.num_unit = props.project.num_unit
    form.buy_land_extent = props.project.buy_land_extent
    form.scheme_land_extent = props.project.scheme_land_extent
    form.donation_land_extent = props.project.donation_land_extent
    form.on_floor_area = props.project.on_floor_area
    form.under_floor_area = props.project.under_floor_area
    form.total_floor_area = props.project.total_floor_area
    form.build_area = props.project.build_area
    form.floor_area_ratio = props.project.floor_area_ratio
    form.build_to_land_ratio = props.project.build_to_land_ratio
    form.num_legal_parking = props.project.num_legal_parking
    form.num_planed_parking = props.project.num_planed_parking
  }
}

onBeforeMount(() => formDataSetup())
onUpdated(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCardBody>
      <CRow>
        <CCol xl="12" class="pt-3">
          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label required">업무 프로젝트</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <MultiSelect
                v-model="form.issue_project"
                mode="single"
                :options="getProjects"
                :attrs="form.issue_project ? {} : { required: true }"
                placeholder="업무 프로젝트를 선택하세요."
              />
              <CFormFeedback invalid>업무 프로젝트를 선택하세요.</CFormFeedback>
            </CCol>
            <CCol md="2" style="padding-top: 7px">
              <div style="width: 20px">
                <v-icon
                  icon="mdi-plus-circle"
                  color="success"
                  class="pointer"
                  @click="refIssueForm.callModal()"
                />
                <v-tooltip activator="parent" location="end">새 업무 프로젝트 생성하기</v-tooltip>
              </div>
            </CCol>
          </CRow>
          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"> 프로젝트명</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model="form.name"
                type="text"
                maxlength="30"
                placeholder="프로젝트명을 입력하세요"
                required
              />
              <CFormFeedback invalid>프로젝트명을 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 정렬순서</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.order"
                type="number"
                min="0"
                placeholder="프로젝트 정력순서를 입력하세요"
              />
              <CFormFeedback invalid>정렬순서를 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"> 프로젝트종류</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormSelect v-model="form.kind" required>
                <option value="">프로젝트 종류</option>
                <option
                  v-for="sort in sortOptins"
                  :key="sort.value"
                  :value="sort.value"
                  :selected="project && sort.value === project.kind"
                >
                  {{ sort.label }}
                </option>
              </CFormSelect>
              <CFormFeedback invalid>프로젝트종류를 선택하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"> 사업개시년도</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <Datepicker
                v-model.number="form.start_year"
                placeholder="사업개시년도를 입력하세요"
                input-class-name="form-control"
                position="left"
                year-picker
                auto-apply
                :dark="store.theme === 'dark'"
                required
              />
              <CFormFeedback invalid> 사업개시년도를 입력하세요</CFormFeedback>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"></CFormLabel>
            <CCol class="mb-md-3">
              <CFormSwitch
                id="is_direct_manage"
                v-model="form.is_direct_manage"
                label="직영운영여부"
                :checked="project && project.is_direct_manage"
              />
              <CFormText class="text-grey">
                본사 직접 운영하는 프로젝트인 경우 체크, 즉 시행대행이나 업무대행이 아닌 경우
              </CFormText>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"></CFormLabel>
            <CCol class="mb-md-3">
              <CFormSwitch
                id="is_returned_area"
                v-model="form.is_returned_area"
                label="토지환지여부"
                :checked="project && project.is_returned_area"
              />
              <CFormText class="text-grey">
                해당 사업부지가 환지방식 도시개발사업구역인 경우 체크
              </CFormText>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"></CFormLabel>
            <CCol class="mb-md-3">
              <CFormSwitch
                id="is_unit_set"
                v-model="form.is_unit_set"
                label="동호지정여부"
                :checked="project && project.is_unit_set"
              />
              <CFormText class="text-grey">
                현재 동호수를 지정하지 않는 경우 체크하지 않음
              </CFormText>
            </CCol>
          </CRow>

          <v-divider />

          <!-- 사업 일정 필드 (필수) -->
          <CRow class="mt-3 mb-3">
            <CCol>
              <h6 class="text-primary">사업 일정 (필수)</h6>
              <p class="text-muted small">
                캐시 플로우 생성에 필요한 필수 항목입니다. 예정일 입력 후 실제 일자로
                업데이트하세요.
              </p>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"
              >월별집계시작일</CFormLabel
            >
            <CCol md="10" lg="2" class="mb-md-3">
              <DatePicker
                v-model="form.monthly_aggr_start_date"
                placeholder="월별집계시작일"
                required
              />
              <CFormText class="text-grey">이 날짜 이전은 누계로 집계됩니다</CFormText>
              <CFormFeedback invalid>월별집계시작일을 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label required">착공(예상)일</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <DatePicker
                v-model="form.construction_start_date"
                placeholder="착공일(예상)"
                required
              />
              <CFormText class="text-grey">이 날짜 포함월부터 공사기간을 계산합니다</CFormText>
              <CFormFeedback invalid>착공일을 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label required">공사기간</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.construction_period_months"
                type="number"
                min="1"
                placeholder="공사기간(개월)"
                required
              />
              <CFormText class="text-grey">착공월부터 공사기간 + 5개월까지 월별 집계</CFormText>
              <CFormFeedback invalid>공사기간을 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <v-divider />

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label">대지위치</CFormLabel>
            <CCol md="3" lg="2" class="mb-3">
              <CFormInput v-model="form.location" maxlength="255" placeholder="대지위치" />
              <CFormFeedback invalid>대지위치를 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"> 용도지역지구</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model="form.area_usage"
                type="text"
                maxlength="50"
                placeholder="용도지역지구를 입력하세요"
                required
              />
              <CFormFeedback invalid>용도지역지구를 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label required"> 건축규모</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model="form.build_size"
                type="text"
                maxlength="50"
                placeholder="건축규모를 입력하세요"
                required
              />
              <CFormFeedback invalid>건축규모를 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 세대(호/실)수</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.num_unit"
                type="number"
                min="0"
                placeholder="세대(호/실)수를 입력하세요"
              />
              <CFormFeedback invalid>세대(호/실)수를 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 대지매입면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.buy_land_extent"
                type="number"
                min="0"
                step="0.0001"
                placeholder="대지매입면적을 입력하세요"
              />
              <CFormFeedback invalid> 대지매입면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 계획대지면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.scheme_land_extent"
                type="number"
                min="0"
                step="0.0001"
                placeholder="계획대지면적을 입력하세요"
              />
              <CFormFeedback invalid> 계획대지면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 기부채납면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.donation_land_extent"
                type="number"
                min="0"
                step="0.0001"
                placeholder="기부채납면적을 입력하세요"
              />
              <CFormFeedback invalid> 기부채납면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 지상연면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.on_floor_area"
                type="number"
                min="0"
                step="0.0001"
                placeholder="지상연면적을 입력하세요"
              />
              <CFormFeedback invalid> 지상연면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 지하연면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.under_floor_area"
                type="number"
                min="0"
                step="0.0001"
                placeholder="지하연면적을 입력하세요"
              />
              <CFormFeedback invalid> 지하연면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 총 연면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.total_floor_area"
                type="number"
                min="0"
                step="0.0001"
                placeholder="총 연면적을 입력하세요"
              />
              <CFormFeedback invalid> 총 연면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 건축면적</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.build_area"
                type="number"
                min="0"
                step="0.0001"
                placeholder="건축면적을 입력하세요"
              />
              <CFormFeedback invalid> 총 연면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 용적율(%)</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.floor_area_ratio"
                type="number"
                min="0"
                step="0.0001"
                placeholder="용적율(%)을 입력하세요"
              />
              <CFormFeedback invalid> 용적율(%)을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 건폐율(%)</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.build_to_land_ratio"
                type="number"
                min="0"
                step="0.0001"
                placeholder="건폐율(%)을 입력하세요"
              />
              <CFormFeedback invalid> 건폐율(%)을 소소점4자리 이하로 입력하세요.</CFormFeedback>
            </CCol>
            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 법정주차대수</CFormLabel>
            <CCol md="10" lg="2" class="mb-md-3">
              <CFormInput
                v-model.number="form.num_legal_parking"
                type="number"
                min="0"
                placeholder="법정주차대수를 입력하세요"
              />
              <CFormFeedback invalid>법정주차대수를 입력하세요.</CFormFeedback>
            </CCol>

            <CFormLabel class="col-md-2 col-lg-1 col-form-label"> 계획주차대수</CFormLabel>
            <CCol md="10" lg="2" class="mb-3">
              <CFormInput
                v-model.number="form.num_planed_parking"
                type="number"
                min="0"
                placeholder="계획주차대수를 입력하세요"
              />
              <CFormFeedback invalid>계획주차대수를 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>
        </CCol>
      </CRow>
    </CCardBody>

    <CCardFooter class="text-right">
      <v-btn type="button" :color="btnLight" @click="emit('reset-form')"> 취소</v-btn>
      <v-btn v-if="project" type="button" color="warning" @click="deleteProject"> 삭제</v-btn>
      <v-btn type="submit" :color="btnClass" :disabled="formsCheck">
        <CIcon name="cil-check-circle" />
        저장
      </v-btn>
    </CCardFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 프로젝트정보 삭제</template>
    <template #default>현재 삭제 기능이 구현되지 않았습니다.</template>
    <template #footer>
      <v-btn size="small" color="warning" disabled>삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 프로젝트정보 {{ confirmText }}</template>
    <template #default> 프로젝트정보 {{ confirmText }}을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn size="small" :color="btnClass" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />

  <IssueProjectForm ref="refIssueForm" @get-project="getAllProjects" />
</template>
