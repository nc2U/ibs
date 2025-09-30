<script lang="ts" setup>
import { computed, inject, onBeforeMount, type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { dateFormat } from '@/utils/baseMixins.ts'
import { btnLight } from '@/utils/cssMixins.ts'
import { useContract } from '@/store/pinia/contract.ts'
import type { AddressInContractor, ContractorAddress } from '@/store/types/contract.ts'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address.ts'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  contractor: { type: Number, required: true },
  address: { type: Object as PropType<AddressInContractor>, default: () => ({}) },
})

const refModalPost = ref()
const refConfirmChk = ref()

const isDark = inject('isDark')

const form = ref({
  contractor: null as number,
  id_zipcode: '',
  id_address1: '',
  id_address2: '',
  id_address3: '',
  dm_zipcode: '',
  dm_address1: '',
  dm_address2: '',
  dm_address3: '',
})

const refAddress1 = ref()
const refAddress2 = ref()

const validated = ref(false)

const sameAddr = ref(false)

const contStore = useContract()
const contAddressList = computed<ContractorAddress[]>(() => contStore.contAddressList)

const createContAddress = (data: Omit<AddressInContractor, 'pk'>) =>
  contStore.createContAddress(data)
const patchContAddress = (pk: number, data: Partial<AddressInContractor>) =>
  contStore.patchContAddress(pk, data)

const toSame = () => {
  sameAddr.value = !sameAddr.value
  if (sameAddr.value) {
    form.value.dm_zipcode = form.value.id_zipcode
    form.value.dm_address1 = form.value.id_address1
    form.value.dm_address2 = form.value.id_address2
    form.value.dm_address3 = form.value.id_address3
  } else {
    form.value.dm_zipcode = ''
    form.value.dm_address1 = ''
    form.value.dm_address2 = ''
    form.value.dm_address3 = ''
  }
}

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 1) {
    form.value.id_zipcode = zipcode
    form.value.id_address1 = address1
    form.value.id_address2 = ''
    form.value.id_address3 = address3
    refAddress1.value.$el.nextElementSibling.focus()
  } else if (formNum === 2) {
    form.value.dm_zipcode = zipcode
    form.value.dm_address1 = address1
    form.value.dm_address2 = ''
    form.value.dm_address3 = address3
    refAddress2.value.$el.nextElementSibling.focus()
  }
}

const mode = ref<'create' | 'update'>('create')
const selectedPk = ref<number | null>(null)

const changeToCurrentAddress = async (addressPk: number) => {
  mode.value = 'update'
  selectedPk.value = addressPk
  refConfirmChk.value.callModal()
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    mode.value = 'create'
    refConfirmChk.value.callModal() //createContAddress(form.value)
  }
}

const modalAction = async () => {
  if (mode.value === 'create') alert('create')
  else if (mode.value === 'update') {
    try {
      await patchContAddress(selectedPk.value, { is_current: true } as Partial<AddressInContractor>)
      // 주소 목록 새로고침 (store에서 자동으로 처리됨)
      // 성공 메시지나 추가 처리가 필요하면 여기에 추가
    } catch (error) {
      console.error('주소 변경 중 오류가 발생했습니다:', error)
      // 에러 처리 로직 추가 가능
    }
  }
  refConfirmChk.value.close()
}

onBeforeMount(() => {
  props.contractor && (form.value.contractor = props.contractor)
})
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="text-body">
      <h6>변경할 주소</h6>
      <CRow class="mb-3">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 주민등록</CFormLabel>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CInputGroup>
            <CInputGroupText @click="refModalPost.initiate(1)"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.id_zipcode"
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              required
              @focus="refModalPost.initiate(1)"
            />
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0">
          <CFormInput
            v-model="form.id_address1"
            maxlength="35"
            placeholder="주민등록 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(1)"
          />
        </CCol>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CFormInput
            ref="refAddress1"
            v-model="form.id_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
          />
        </CCol>

        <CCol sm="12" md="6" lg="2">
          <CFormInput
            v-model="form.id_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
          />
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 우편수령</CFormLabel>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CInputGroup>
            <CInputGroupText @click="refModalPost.initiate(2)"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.dm_zipcode"
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              required
              @focus="refModalPost.initiate(2)"
            />
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0">
          <CFormInput
            v-model="form.dm_address1"
            maxlength="50"
            placeholder="우편물 수령 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(2)"
          />
        </CCol>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CFormInput
            ref="refAddress2"
            v-model="form.dm_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
          />
        </CCol>
        <CCol sm="12" md="6" lg="2">
          <CFormInput
            v-model="form.dm_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
          />
        </CCol>
        <CCol sm="12" lg="1" class="pt-1">
          <v-checkbox-btn
            v-model="sameAddr"
            id="to-same-for-modal"
            label="상동"
            density="compact"
            :color="isDark ? '#857DCC' : '#321FDB'"
            :disabled="!form.id_zipcode"
            @click="toSame"
          />
        </CCol>
      </CRow>
      <v-divider />
      <h6>변경전 (현재) 주소</h6>
      <CTable borderless responsive align="middle" class="mb-0" color="warning">
        <CTableBody class="text-center">
          <CTableRow>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ address.id_zipcode }}) {{ address.id_address1 }} {{ address.id_address2 }}
              {{ address.id_address3 }}
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ address.dm_zipcode }}) {{ address.dm_address1 }} {{ address.dm_address2 }}
              {{ address.dm_address3 }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
      <v-divider />
      <h6>과거 주소</h6>
      <CTable v-if="contAddressList.length" bordered responsive align="middle" class="mb-0">
        <CTableBody v-for="(addr, index) in contAddressList" :key="addr.pk" class="text-center">
          <CTableRow>
            <CTableDataCell rowspan="2">{{ contAddressList.length - index }}</CTableDataCell>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ addr.id_zipcode }}) {{ addr.id_address1 }} {{ addr.id_address2 }}
              {{ addr.id_address3 }}
            </CTableDataCell>
            <CTableDataCell rowspan="2">{{ dateFormat(addr.created, '/') }} 등록됨</CTableDataCell>
            <CTableDataCell rowspan="2">
              <v-btn
                size="small"
                color="primary"
                variant="outlined"
                @click="changeToCurrentAddress(addr.pk)"
              >
                이 주소로 변경
              </v-btn>
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ addr.dm_zipcode }}) {{ addr.dm_address1 }} {{ addr.dm_address2 }}
              {{ addr.dm_address3 }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CTable v-else borderless align="middle">
        <CTableBody>
          <CTableRow class="text-center">
            <CTableDataCell style="height: 100px; color: grey">
              현재 주소 이전에 등록 된 데이터가 없습니다.
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CModalBody>
    <CModalFooter>
      <v-btn :color="btnLight" size="small" @click="$emit('close')">닫기</v-btn>
      <v-btn type="submit" color="primary" size="small">확인</v-btn>
    </CModalFooter>
  </CForm>

  <DaumPostcode ref="refModalPost" @address-callback="addressCallback" />

  <ConfirmModal ref="refConfirmChk">
    <template #footer>
      <v-btn size="small" color="primary" @click="modalAction">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
