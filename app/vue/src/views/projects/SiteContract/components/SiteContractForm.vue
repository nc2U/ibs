<script lang="ts" setup>
import { ref, reactive, computed, watch, onBeforeMount } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { isValidate } from '@/utils/helper'
import { type SiteContract } from '@/store/types/project'
import { write_project } from '@/utils/pageAuth'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/index.vue'
import SiteContFiles from './SiteContFiles.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = reactive<SiteContract>({
  pk: null,
  project: null,
  owner: null,
  contract_date: null,
  total_price: null,
  contract_area: null,
  down_pay1: null,
  down_pay1_date: null,
  down_pay1_is_paid: false,
  down_pay2: null,
  down_pay2_date: null,
  down_pay2_is_paid: false,
  inter_pay1: null,
  inter_pay1_date: null as string | null,
  inter_pay1_is_paid: false,
  inter_pay2: null,
  inter_pay2_date: null as string | null,
  inter_pay2_is_paid: false,
  remain_pay: null,
  remain_pay_date: null,
  remain_pay_is_paid: false,
  ownership_completion: false,
  acc_bank: '',
  acc_number: '',
  acc_owner: '',
  note: '',
  site_cont_files: [],
})

const siteStore = useSite()
const getOwners = computed(() => siteStore.getOwners)

const formsCheck = computed(() => {
  if (props.contract) {
    const a = form.owner === props.contract.owner
    const b = form.contract_date === props.contract.contract_date
    const c = form.total_price === props.contract.total_price
    const d = form.contract_area === props.contract.contract_area
    const e = form.down_pay1 === props.contract.down_pay1
    const f = form.down_pay1_date === props.contract.down_pay1_date
    const g = form.down_pay1_is_paid === props.contract.down_pay1_is_paid
    const h = form.down_pay2 === props.contract.down_pay2
    const i = form.down_pay2_date === props.contract.down_pay2_date
    const j = form.down_pay2_is_paid === props.contract.down_pay2_is_paid
    const k = form.inter_pay1 === props.contract.inter_pay1
    const l = form.inter_pay1_date === props.contract.inter_pay1_date
    const m = form.inter_pay1_is_paid === props.contract.inter_pay1_is_paid
    const n = form.inter_pay2 === props.contract.inter_pay2
    const o = form.inter_pay2_date === props.contract.inter_pay2_date
    const p = form.inter_pay2_is_paid === props.contract.inter_pay2_is_paid
    const q = form.remain_pay === props.contract.remain_pay
    const r = form.remain_pay_date === props.contract.remain_pay_date
    const s = form.remain_pay_is_paid === props.contract.remain_pay_is_paid
    const t = form.ownership_completion === props.contract.ownership_completion
    const u = form.acc_bank === props.contract.acc_bank
    const v = form.acc_number === props.contract.acc_number
    const w = form.acc_owner === props.contract.acc_owner
    const x = form.note === props.contract.note

    const y = !newFile.value
    const z = !editFile.value
    const a1 = !cngFile.value
    const b1 = !delFile.value

    const sky = a && b && c && d && e && f && g && h && i
    const sea = j && k && l && m && n && o && p && q && r
    const air = s && t && u && v && w && x && y && z && a1 && b1

    return sky && sea && air
  } else return false
})

const getAreaByOwner = computed(() =>
  !props.contract && siteStore.siteOwner
    ? siteStore.siteOwner.sites.map(s => Number(s.owned_area)).reduce((sum, val) => sum + val, 0)
    : null,
)

watch(form, val => {
  if (!props.contract && val.owner) siteStore.fetchSiteOwner(val.owner)
})

watch(getAreaByOwner, val => (form.contract_area = val))

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_project.value) multiSubmit({ ...form })
    else refAlertModal.value.callModal()
    validated.value = false
  }
}

const multiSubmit = (payload: SiteContract) => {
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
  emit('on-delete', { pk: props.contract.pk, project: props.contract.project })
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (write_project.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const dataSetup = () => {
  if (props.contract) {
    form.pk = props.contract.pk
    form.project = props.contract.project
    form.owner = props.contract.owner
    form.contract_date = props.contract.contract_date
    form.total_price = props.contract.total_price
    form.contract_area = props.contract.contract_area
    form.down_pay1 = props.contract.down_pay1
    form.down_pay1_date = props.contract.down_pay1_date
    form.down_pay1_is_paid = props.contract.down_pay1_is_paid
    form.down_pay2 = props.contract.down_pay2
    form.down_pay2_date = props.contract.down_pay2_date
    form.down_pay2_is_paid = props.contract.down_pay2_is_paid
    form.inter_pay1 = props.contract.inter_pay1
    form.inter_pay1_date = props.contract.inter_pay1_date
    form.inter_pay1_is_paid = props.contract.inter_pay1_is_paid
    form.inter_pay2 = props.contract.inter_pay2
    form.inter_pay2_date = props.contract.inter_pay2_date
    form.inter_pay2_is_paid = props.contract.inter_pay2_is_paid
    form.remain_pay = props.contract.remain_pay
    form.remain_pay_date = props.contract.remain_pay_date
    form.remain_pay_is_paid = props.contract.remain_pay_is_paid
    form.ownership_completion = props.contract.ownership_completion
    form.acc_bank = props.contract.acc_bank
    form.acc_number = props.contract.acc_number
    form.acc_owner = props.contract.acc_owner
    form.note = props.contract.note
    form.site_cont_files = props.contract.site_cont_files
  } else form.project = props.project as number
}

const RefSiteContFile = ref()
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

onBeforeMount(() => dataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">소유자</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model.number="form.owner"
                  :options="getOwners"
                  placeholder="소유자"
                  autocomplete="label"
                  :attrs="form.owner ? {} : { required: true }"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 총 계약면적(㎡)</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.contract_area"
                  type="number"
                  min="0"
                  step="0.0000001"
                  placeholder="총 계약면적(㎡)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 총 매매가격</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.total_price"
                  min="0"
                  type="number"
                  required
                  placeholder="총 매매가격"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 계약 체결일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.contract_date"
                  maxlength="10"
                  placeholder="계약 체결일"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 계약금 (1차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.down_pay1"
                    type="number"
                    min="0"
                    required
                    placeholder="계약금 - 1차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="down_pay1_is_paid"
                      v-model="form.down_pay1_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.down_pay1_date"
                  maxlength="10"
                  placeholder="계약금 1차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계약금 (2차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.down_pay2"
                    type="number"
                    min="0"
                    placeholder="계약금 - 2차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="down_pay2_is_paid"
                      v-model="form.down_pay2_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.down_pay2_date"
                  maxlength="10"
                  placeholder="계약금 2차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 중도금 (1차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.inter_pay1"
                    type="number"
                    min="0"
                    placeholder="중도금 - 1차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="inter_pay1_is_paid"
                      v-model="form.inter_pay1_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.inter_pay1_date"
                  maxlength="10"
                  placeholder="중도금 1차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 중도금 (2차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.inter_pay2"
                    type="number"
                    min="0"
                    placeholder="중도금 - 2차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="inter_pay2_is_paid"
                      v-model="form.inter_pay2_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.inter_pay2_date"
                  maxlength="10"
                  placeholder="중도금 2차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">잔금</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.remain_pay"
                    type="number"
                    min="0"
                    required
                    placeholder="계약 잔금"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="remain_pay_is_paid"
                      v-model="form.remain_pay_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.remain_pay_date"
                  maxlength="10"
                  placeholder="잔금 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required"> 입금 은행</CFormLabel>
              <CCol sm="3">
                <CFormInput
                  v-model="form.acc_bank"
                  maxlength="20"
                  required
                  placeholder="입금 은행"
                />
              </CCol>
              <CCol sm="3">
                <CFormInput
                  v-model="form.acc_number"
                  maxlength="25"
                  required
                  placeholder="계좌번호"
                />
              </CCol>
              <CCol sm="2">
                <CFormInput v-model="form.acc_owner" maxlength="20" required placeholder="예금주" />
              </CCol>
              <CCol sm="2" class="pt-2">
                <CFormSwitch
                  id="ownership_completion"
                  v-model="form.ownership_completion"
                  label="소유권 확보"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 특이사항</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.note" rows="3" placeholder="특이사항" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <SiteContFiles
          ref="RefSiteContFile"
          :contract-files="form.site_cont_files"
          :deleted="delFile || undefined"
          @file-control="fileControl"
        />
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" color="light" @click="emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="contract ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="contract" size="small" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 부지 매입 계약 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 부지 매입 계약 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
