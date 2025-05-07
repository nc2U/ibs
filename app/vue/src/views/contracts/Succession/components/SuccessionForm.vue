<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, nextTick, type PropType } from 'vue'
import { write_contract } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { useContract } from '@/store/pinia/contract'
import { type BuyerForm, type Succession } from '@/store/types/contract'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  succession: { type: Object as PropType<Succession>, default: null },
  isSuccession: { type: Boolean, default: false },
})

const emit = defineEmits(['on-submit', 'close'])

const postCode = ref()
const refAlertModal = ref()
const refConfirmModal = ref()

const address21 = ref()
const address22 = ref()
const sameAddr = ref(false)
const validated = ref(false)

const form = reactive({
  pk: undefined as undefined | number,
  contract: null as number | null,
  seller: null as number | null,
  buyer: null as number | null,
  apply_date: '',
  trading_date: '',
  is_approval: false,
  approval_date: null as string | null,
  note: '',
})

const buyer_data = reactive<BuyerForm>({
  name: '',
  birth_date: '',
  gender: 'M',
  id_zipcode: '',
  id_address1: '',
  id_address2: '',
  id_address3: '',
  dm_zipcode: '',
  dm_address1: '',
  dm_address2: '',
  dm_address3: '',
  cell_phone: '',
  home_phone: '',
  other_phone: '',
  email: '',
})

const formsCheck = computed(() => {
  if (props.isSuccession) {
    const a = form.seller === props.succession.seller.pk
    const b = form.buyer === props.succession.buyer.pk
    const c = form.apply_date === props.succession.apply_date
    const d = form.trading_date === props.succession.trading_date
    const e = form.is_approval === props.succession.is_approval
    const f = form.approval_date === props.succession.approval_date
    const g = form.note === props.succession.note
    const h = buyer_data.name === props.succession.buyer.name
    const i = buyer_data.birth_date === props.succession.buyer.birth_date
    const j = buyer_data.gender === props.succession.buyer.gender

    const addr = props.succession.buyer.contractoraddress
    const k = buyer_data.id_zipcode === addr.id_zipcode
    const l = buyer_data.id_address1 === addr.id_address1
    const m = buyer_data.id_address2 === addr.id_address2
    const n = buyer_data.id_address3 === addr.id_address3
    const o = buyer_data.dm_zipcode === addr.dm_zipcode
    const p = buyer_data.dm_address1 === addr.dm_address1
    const q = buyer_data.dm_address2 === addr.dm_address2
    const r = buyer_data.dm_address3 === addr.dm_address3

    const cont = props.succession.buyer.contractorcontact
    const s = buyer_data.cell_phone === cont.cell_phone
    const t = buyer_data.home_phone === cont.home_phone
    const u = buyer_data.other_phone === cont.other_phone
    const v = buyer_data.email === cont.email
    const fc = a && b && c && d && e && f && g && h && i && j && k
    const bc = l && m && n && o && p && q && r && s && t && u && v
    return fc && bc
  } else return false
})

const contStore = useContract()
const contractor = computed(() => contStore.contractor)

const seller = computed(() => ({
  pk: props.isSuccession ? props.succession.seller.pk : contractor.value?.pk,
  name: props.isSuccession ? props.succession.seller.name : contractor.value?.name,
}))

const onSubmit = (event: Event) => {
  if (write_contract.value) {
    if (isValidate(event)) {
      validated.value = true
    } else {
      const s_data = { ...form }
      const b_data = { ...buyer_data }
      emit('on-submit', { ...{ s_data }, ...{ b_data } })
    }
  } else refAlertModal.value.callModal()
}

const deleteConfirm = () => {
  if (write_contract.value) refConfirmModal.value.callModal()
  else refAlertModal.value.callModal()
}

const modalAction = () => alert('this is ready!')

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 2) {
    buyer_data.id_zipcode = zipcode
    buyer_data.id_address1 = address1
    buyer_data.id_address2 = ''
    buyer_data.id_address3 = address3
    address21.value.$el.nextElementSibling.focus()
  } else if (formNum === 3) {
    buyer_data.dm_zipcode = zipcode
    buyer_data.dm_address1 = address1
    buyer_data.dm_address2 = ''
    buyer_data.dm_address3 = address3
    address22.value.$el.nextElementSibling.focus()
  }
}

const toSame = () => {
  if (!sameAddr.value) {
    buyer_data.dm_zipcode = buyer_data.id_zipcode
    buyer_data.dm_address1 = buyer_data.id_address1
    buyer_data.dm_address2 = buyer_data.id_address2
    buyer_data.dm_address3 = buyer_data.id_address3
  } else {
    buyer_data.dm_zipcode = ''
    buyer_data.dm_address1 = ''
    buyer_data.dm_address2 = ''
    buyer_data.dm_address3 = ''
  }
}

const chkApproval = () => {
  nextTick(() => {
    if (!form.is_approval) form.approval_date = null
  })
}

const formDataSet = () => {
  if (props.isSuccession) {
    const buyer = props.succession.buyer
    form.pk = props.succession.pk
    form.contract = props.succession.contract.pk
    form.seller = props.succession.seller.pk
    form.buyer = buyer.pk as number
    form.apply_date = props.succession.apply_date
    form.trading_date = props.succession.trading_date
    form.is_approval = props.succession.is_approval
    form.approval_date = props.succession.approval_date
    form.note = props.succession.note

    buyer_data.name = buyer.name
    buyer_data.birth_date = buyer.birth_date
    buyer_data.gender = buyer.gender

    const addr = buyer.contractoraddress
    buyer_data.id_zipcode = addr.id_zipcode
    buyer_data.id_address1 = addr.id_address1
    buyer_data.id_address2 = addr.id_address2
    buyer_data.id_address3 = addr.id_address3
    buyer_data.dm_zipcode = addr.dm_zipcode
    buyer_data.dm_address1 = addr.dm_address1
    buyer_data.dm_address2 = addr.dm_address2
    buyer_data.dm_address3 = addr.dm_address3

    const cont = buyer.contractorcontact
    buyer_data.cell_phone = cont.cell_phone
    buyer_data.home_phone = cont.home_phone
    buyer_data.other_phone = cont.other_phone
    buyer_data.email = cont.email
  } else {
    form.contract = contractor.value?.contract || null
    form.seller = contractor.value?.pk || null
  }
}

onBeforeMount(() => formDataSet())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 양도계약자</CFormLabel>
            <CCol sm="8">
              <CFormSelect v-model="form.seller" required readonly>
                <option :value="seller.pk">
                  {{ seller.name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CCol>

        <!--        <CCol xs="6">-->
        <!--          <CRow>-->
        <!--            <CFormLabel class="col-sm-4 col-form-label">계약건</CFormLabel>-->
        <!--            <CCol sm="8" class="text-left">-->
        <!--              <CFormSelect-->
        <!--                v-if="contractor"-->
        <!--                v-model="form.contract"-->
        <!--                required-->
        <!--                readonly-->
        <!--              >-->
        <!--                <option :value="contractor.contract">-->
        <!--                  {{ contractor.__str__ }}-->
        <!--                </option>-->
        <!--              </CFormSelect>-->
        <!--            </CCol>-->
        <!--          </CRow>-->
        <!--        </CCol>-->
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">승계신청일</CFormLabel>
            <CCol sm="8">
              <DatePicker v-model="form.apply_date" required placeholder="승계신청일" />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required"> 매매계약일</CFormLabel>
            <CCol sm="8">
              <DatePicker v-model="form.trading_date" required placeholder="매매계약일" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <v-divider />

      <h6 class="pb-2">◼︎ 양수계약자 인적사항</h6>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">양수계약자</CFormLabel>
            <CCol sm="8">
              <CFormInput v-model="buyer_data.name" required placeholder="양수계약자 성명" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">생년월일</CFormLabel>
            <CCol sm="8">
              <DatePicker v-model="buyer_data.birth_date" required placeholder="생년월일" />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">성별</CFormLabel>
            <CCol sm="8" class="pt-2">
              <div class="form-check form-check-inline">
                <input
                  id="male"
                  v-model="buyer_data.gender"
                  class="form-check-input"
                  type="radio"
                  value="M"
                  name="gender"
                />
                <label class="form-check-label" for="male">남성</label>
              </div>
              <div class="form-check form-check-inline">
                <input
                  id="female"
                  v-model="buyer_data.gender"
                  class="form-check-input"
                  type="radio"
                  value="F"
                  name="gender"
                />
                <label class="form-check-label" for="female">여성</label>
              </div>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">휴대전화</CFormLabel>
            <CCol sm="8">
              <input
                v-model="buyer_data.cell_phone"
                v-maska
                data-maska="['###-###-####', '###-####-####']"
                class="form-control"
                maxlength="13"
                required
                placeholder="휴대전화"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">집전화</CFormLabel>
            <CCol sm="8">
              <input
                v-model="buyer_data.home_phone"
                v-maska
                data-maska="['###-###-####', '###-####-####']"
                class="form-control"
                maxlength="13"
                placeholder="집전화"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">기타연락처</CFormLabel>
            <CCol sm="8">
              <input
                v-model="buyer_data.other_phone"
                v-maska
                data-maska="['###-###-####', '###-####-####']"
                class="form-control"
                maxlength="13"
                placeholder="기타연락처"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">이메일</CFormLabel>
            <CCol sm="8">
              <CFormInput v-model="buyer_data.email" type="email" placeholder="이메일" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol>
          <CRow class="mb-2">
            <CFormLabel class="col-sm-2 col-form-label required"> 주민등록주소</CFormLabel>
            <CCol xs="4">
              <CInputGroup>
                <CInputGroupText @click="postCode.initiate(2)"> 우편번호</CInputGroupText>
                <CFormInput
                  v-model="buyer_data.id_zipcode"
                  v-maska
                  data-maska="#####"
                  maxlength="5"
                  placeholder="우편번호"
                  required
                  @focus="postCode.initiate(2)"
                />
              </CInputGroup>
            </CCol>
            <CCol xs="6">
              <CFormInput
                v-model="buyer_data.id_address1"
                maxlength="35"
                placeholder="주민등록 메인 주소"
                required
                @focus="postCode.initiate(2)"
              />
            </CCol>
          </CRow>
          <CRow>
            <CCol xs="2" />
            <CCol xs="4">
              <CFormInput
                ref="address21"
                v-model="buyer_data.id_address2"
                maxlength="20"
                placeholder="상세주소(지번, 동호수)"
              />
            </CCol>
            <CCol xs="6">
              <CFormInput
                v-model="buyer_data.id_address3"
                maxlength="20"
                placeholder="참고항목(동, 건물)"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol>
          <CRow class="mb-2">
            <CFormLabel class="col-sm-2 col-form-label required"> 우편송달주소</CFormLabel>
            <CCol xs="4">
              <CInputGroup>
                <CInputGroupText @click="postCode.initiate(3)"> 우편번호</CInputGroupText>
                <CFormInput
                  v-model="buyer_data.dm_zipcode"
                  v-maska
                  data-maska="#####"
                  maxlength="5"
                  placeholder="우편번호"
                  required
                  @focus="postCode.initiate(3)"
                />
              </CInputGroup>
            </CCol>
            <CCol xs="6">
              <CFormInput
                v-model="buyer_data.dm_address1"
                maxlength="35"
                placeholder="우편송달 메인 주소"
                required
                @focus="postCode.initiate(3)"
              />
            </CCol>
          </CRow>
          <CRow>
            <CCol xs="2" />
            <CCol xs="4">
              <CFormInput
                ref="address22"
                v-model="buyer_data.dm_address2"
                maxlength="20"
                placeholder="상세주소(지번, 동호수)"
              />
            </CCol>
            <CCol xs="6">
              <CInputGroup>
                <CFormInput
                  v-model="buyer_data.dm_address3"
                  maxlength="20"
                  placeholder="참고항목(동, 건물)"
                />
                <CInputGroupText>
                  <CFormCheck id="toSame" v-model="sameAddr" label="상동" @click="toSame" />
                </CInputGroupText>
              </CInputGroup>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <v-divider />

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 변경인가여부</CFormLabel>
            <CCol sm="8" class="pt-2">
              <CFormSwitch
                id="isApproval"
                v-model="form.is_approval"
                :disabled="!succession"
                label="변경인가완료"
                @change="chkApproval"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 변경인가일</CFormLabel>
            <CCol sm="8">
              <DatePicker
                v-model="form.approval_date"
                :required="form.is_approval"
                :disabled="!form.is_approval"
                placeholder="변경인가일"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol>
          <CRow>
            <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
            <CCol sm="10">
              <CFormTextarea v-model="form.note" placeholder="기타 특이사항" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" color="light" @click="emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn type="submit" :color="isSuccession ? 'success' : 'primary'" :disabled="formsCheck">
          저장
        </v-btn>
        <v-btn v-if="isSuccession" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <DaumPostcode ref="postCode" @address-callback="addressCallback" />

  <ConfirmModal ref="refConfirmModal">
    <template #header> 권리 의무 승계 정보 - [삭제]</template>
    <template #default>
      삭제 후 복구할 수 없습니다. 해당 권리 의무 승계 정보 삭제를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
