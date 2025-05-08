<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useSite } from '@/store/pinia/project_site'
import { type SimpleSite, type SiteOwner } from '@/store/types/project'
import { write_project } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import Multiselect from '@/components/MultiSelect/index.vue'

const props = defineProps({ owner: { type: Object, default: null } })

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const refDelModal = ref()
const refAlertModal = ref()
const refPostCode = ref()

const address2 = ref()

const validated = ref(false)

const form = reactive<SiteOwner>({
  pk: null,
  project: null,
  own_sort: '1',
  owner: '',
  use_consent: false,
  date_of_birth: null,
  sites: [],
  phone1: '',
  phone2: '',
  zipcode: '',
  address1: '',
  address2: '',
  address3: '',
  own_sort_desc: '',
  counsel_record: '',
})

const own_sort_select = [
  { val: '1', text: '개인' },
  { val: '2', text: '법인' },
  { val: '3', text: '국공유지' },
]

const projectStore = useProject()
const initProjId = computed(() => projectStore.initProjId)
const project = computed(() => projectStore.project?.pk || initProjId.value)

const siteStore = useSite()
const getSites = computed(() => siteStore.getSites)

const formsCheck = computed(() => {
  if (props.owner) {
    const a = form.own_sort === props.owner.own_sort
    const b = form.owner === props.owner.owner
    const c = form.use_consent === props.owner.use_consent
    const d = form.date_of_birth === props.owner.date_of_birth
    const e =
      JSON.stringify(form.sites) ===
      JSON.stringify(props.owner.sites.map((s: SimpleSite) => s.site))
    const f = form.phone1 === props.owner.phone1
    const g = form.phone2 === props.owner.phone2
    const h = form.zipcode === props.owner.zipcode
    const i = form.address1 === props.owner.address1
    const j = form.address2 === props.owner.address2
    const k = form.address3 === props.owner.address3
    const l = form.counsel_record === props.owner.counsel_record

    return a && b && c && d && e && f && g && h && i && j && k && l
  } else return false
})

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 1) {
    // 입력할 데이터와 focus 폼 지정
    form.zipcode = zipcode
    form.address1 = address1
    form.address2 = ''
    form.address3 = address3
    address2.value.$el.nextElementSibling.focus()
  }
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_project.value) multiSubmit(form)
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (multiPayload: SiteOwner) => {
  emit('multi-submit', multiPayload)
  emit('close')
}

const deleteObject = () => {
  emit('on-delete', { pk: props.owner.pk, project: props.owner.project })
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (write_project.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const dataSetup = () => {
  if (props.owner) {
    form.pk = props.owner.pk
    form.project = props.owner.project
    form.own_sort = props.owner.own_sort
    form.owner = props.owner.owner
    form.use_consent = props.owner.use_consent
    form.date_of_birth = props.owner.date_of_birth
    form.sites = props.owner.sites.map((s: SimpleSite) => s.site)
    form.phone1 = props.owner.phone1
    form.phone2 = props.owner.phone2
    form.zipcode = props.owner.zipcode
    form.address1 = props.owner.address1
    form.address2 = props.owner.address2
    form.address3 = props.owner.address3
    form.own_sort_desc = props.owner.own_sort_desc
    form.counsel_record = props.owner.counsel_record
  } else form.project = project.value
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
              <CFormLabel class="col-sm-4 col-form-label">소유구분</CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model="form.own_sort">
                  <option v-for="sort in own_sort_select" :key="sort.val" :value="sort.val">
                    {{ sort.text }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">사용동의</CFormLabel>
              <CCol sm="8" class="pt-2">
                <CFormSwitch
                  v-model="form.use_consent"
                  label="토지사용 동의(승낙) 여부"
                  id="use-consent"
                  :disabled="!owner"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">소유자</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.owner" maxlength="20" required placeholder="소유자" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">생년월일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.date_of_birth"
                  maxlength="10"
                  :required="false"
                  placeholder="생년월일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required"> 소유부지</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.sites"
                  :options="getSites"
                  placeholder="소유부지 :: 필수 입력"
                  :attrs="form.sites.length ? {} : { required: true }"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">주 연락처</CFormLabel>
              <CCol sm="8">
                <input
                  v-model="form.phone1"
                  v-maska
                  data-maska="['###-###-####', '###-####-####']"
                  class="form-control"
                  maxlength="13"
                  placeholder="주 연락처"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 보조 연락처</CFormLabel>
              <CCol sm="8">
                <input
                  v-model="form.phone2"
                  v-maska
                  data-maska="['###-###-####', '###-####-####']"
                  class="form-control"
                  maxlength="13"
                  placeholder="보조 연락처"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">주소</CFormLabel>
              <CCol sm="3">
                <CInputGroup>
                  <CInputGroupText @click="refPostCode.initiate()"> 우편번호</CInputGroupText>
                  <CFormInput
                    v-model="form.zipcode"
                    v-maska
                    data-maska="#####"
                    placeholder="우편번호"
                    maxlength="5"
                    @focus="refPostCode.initiate()"
                  />
                  <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>
                </CInputGroup>
              </CCol>
              <CCol sm="7">
                <CFormInput
                  v-model="form.address1"
                  maxlength="35"
                  placeholder="메인 주소"
                  @click="refPostCode.initiate()"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"></CFormLabel>
              <CCol sm="5">
                <CFormInput
                  ref="address2"
                  v-model="form.address2"
                  maxlength="20"
                  placeholder="상세 주소"
                />
              </CCol>
              <CCol sm="5">
                <CFormInput v-model="form.address3" maxlength="20" placeholder="나머지 주소" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 주요 상담 기록</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.counsel_record"
                  rows="4"
                  placeholder="주요 상담 기록"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" color="light" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="owner ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="owner" size="small" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>

    <DaumPostcode ref="refPostCode" @address-callback="addressCallback" />
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
