<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, type PropType } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useSite } from '@/store/pinia/project_site'
import { isValidate } from '@/utils/helper'
import { type Project, type Site } from '@/store/types/project'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_project } from '@/utils/pageAuth'
import SiteInfoFiles from './SiteInfoFiles.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ site: { type: Object as PropType<Site>, default: null } })

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = reactive({
  pk: null as number | null,
  project: null as number | null,
  order: null as number | null,
  district: '',
  lot_number: '',
  site_purpose: '',
  official_area: '',
  returned_area: null as number | null,
  notice_price: null as number | null,
  rights_a: '',
  rights_b: '',
  dup_issue_date: null as null | string,
  note: '',
  site_info_files: [] as any[],
})

const projectStore = useProject()
const initProjId = computed(() => projectStore.initProjId)
const project = computed(() => (projectStore.project as Project)?.pk || initProjId.value)
const isReturned = computed(() => (projectStore.project as Project)?.is_returned_area)
const siteStore = useSite()

const formsCheck = computed(() => {
  if (props.site) {
    const a = form.project === props.site.project
    const b = form.order === props.site.order
    const c = form.district === props.site.district
    const d = form.lot_number === props.site.lot_number
    const e = form.site_purpose === props.site.site_purpose
    const f = form.official_area === props.site.official_area
    const g = form.returned_area === props.site.returned_area
    const h = form.notice_price === props.site.notice_price
    const i = form.rights_a === props.site.rights_a
    const j = form.rights_b === props.site.rights_b
    const k = form.dup_issue_date === props.site.dup_issue_date
    const l = form.note === props.site.note

    const m = !newFile.value
    const n = !editFile.value
    const o = !cngFile.value
    const p = !delFile.value

    return a && b && c && d && e && f && g && h && i && j && k && l && m && n && o && p
  } else return false
})

const RefSiteInfoFile = ref()
const newFile = ref<File | ''>('')
const editFile = ref<number | ''>('')
const cngFile = ref<File | ''>('')
const delFile = ref<number | ''>('')

const fileControl = (payload: any) => {
  if (payload.newFile) newFile.value = payload.newFile
  else newFile.value = ''

  if (payload.editFile) {
    editFile.value = payload.editFile
    cngFile.value = payload.cngFile
  } else {
    editFile.value = ''
    cngFile.value = ''
  }

  if (payload.delFile) delFile.value = payload.delFile
  else delFile.value = ''
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_project.value) multiSubmit({ ...form })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Site) => {
  emit('multi-submit', {
    ...payload,
    newFile: newFile.value,
    editFile: editFile.value,
    cngFile: cngFile.value,
    delFile: delFile.value,
  })
  emit('close')
}

const deleteObject = () => {
  emit('on-delete', { pk: props.site?.pk, project: props.site?.project })
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (write_project.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const dataSetup = () => {
  if (props.site) {
    form.pk = props.site.pk
    form.project = props.site.project
    form.order = props.site.order
    form.district = props.site.district
    form.lot_number = props.site.lot_number
    form.site_purpose = props.site.site_purpose
    form.official_area = props.site.official_area
    form.returned_area = props.site.returned_area
    form.notice_price = props.site.notice_price
    form.rights_a = props.site.rights_a
    form.rights_b = props.site.rights_b
    form.dup_issue_date = props.site.dup_issue_date
    form.note = props.site.note
    form.site_info_files = props.site.site_info_files
  } else {
    form.project = project.value
    form.order = siteStore.siteCount + 1
  }
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <h6 class="mb-3">■ 필수 정보</h6>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">등록 번호</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.order"
                  required
                  min="0"
                  type="number"
                  placeholder="등록 번호"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">행정 동</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.district" required maxlength="10" placeholder="행정 동" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">지번</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.lot_number" required maxlength="10" placeholder="지번" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">지목</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.site_purpose"
                  required
                  maxlength="10"
                  placeholder="지목"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 공부상 면적(㎡)</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.official_area"
                  type="number"
                  required
                  min="0"
                  step="0.0000001"
                  placeholder="공부상 면적(㎡)"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow v-if="isReturned">
              <CFormLabel class="col-sm-4 col-form-label"> 환지 면적(㎡)</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.returned_area"
                  type="number"
                  min="0"
                  step="0.0000001"
                  placeholder="환지 면적(㎡)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <v-divider />

        <h6 class="mb-3">■ 선택 정보</h6>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 등기부 발급일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.dup_issue_date"
                  :required="false"
                  maxlength="10"
                  placeholder="등기부 발급일"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 공시지가</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.notice_price"
                  type="number"
                  :required="false"
                  placeholder="공시지가"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 갑구 권리 제한 사항</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.rights_a" rows="4" placeholder="갑구 권리 제한 사항" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 을구 권리 제한 사항</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.rights_b" rows="4" placeholder="을구 권리 제한 사항" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <v-divider />

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 비고</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.note"
                  rows="4"
                  placeholder="지상 건축물 등 기타 관련 참고 사항"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <SiteInfoFiles
          ref="RefSiteInfoFile"
          :info-files="form.site_info_files"
          :deleted="delFile || undefined"
          @file-control="fileControl"
        />
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" :color="btnLight" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="site ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="site" size="small" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 사업 부지 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 사업 부지 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
