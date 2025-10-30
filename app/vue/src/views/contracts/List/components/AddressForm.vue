<script lang="ts" setup>
import { computed, inject, onBeforeMount, onBeforeUnmount, type PropType, ref } from 'vue'
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
  contractor: null as number | null,
  id_zipcode: '',
  id_address1: '',
  id_address2: '',
  id_address3: '',
  dm_zipcode: '',
  dm_address1: '',
  dm_address2: '',
  dm_address3: '',
})

const resetForm = () => {
  form.value.contractor = null
  form.value.id_zipcode = ''
  form.value.id_address1 = ''
  form.value.id_address2 = ''
  form.value.id_address3 = ''
  form.value.dm_zipcode = ''
  form.value.dm_address1 = ''
  form.value.dm_address2 = ''
  form.value.dm_address3 = ''
}

const refAddress1 = ref()
const refAddress2 = ref()

const validated = ref(false)

const sameAddr = ref(false)

// 테이블 색상 상태 관리
const currentTableColor = ref<'info' | 'warning'>('info')
const colorTimeout = ref<NodeJS.Timeout | null>(null)

const contStore = useContract()
const contAddressList = computed<ContractorAddress[]>(() => contStore.contAddressList)

// 테이블 색상을 일시적으로 변경하는 함수
const highlightTableChange = () => {
  // 기존 타이머가 있으면 클리어
  if (colorTimeout.value) {
    clearTimeout(colorTimeout.value)
  }

  // 색상을 warning으로 변경
  currentTableColor.value = 'warning'

  // 5초 후에 info로 되돌리기
  colorTimeout.value = setTimeout(() => {
    currentTableColor.value = 'info'
    colorTimeout.value = null
  }, 5000)
}

const createContAddress = async (payload: Omit<AddressInContractor, 'pk'>) => {
  await contStore.createContAddress(payload)
  highlightTableChange()
}

const patchContAddress = async (pk: number, payload: Partial<AddressInContractor>) => {
  await contStore.patchContAddress(pk, payload)
  highlightTableChange()
}

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
  refConfirmChk.value.callModal(
    '주소변경 등록',
    '이 종전 주소를 현재 주소로 다시 변경하시겠습니까?',
    'mdi-office-building-marker',
    'warning',
  )
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    mode.value = 'create'
    refConfirmChk.value.callModal(
      '주소변경 등록',
      '입력하신 주소를 새로운 현재 주소로 등록하시겠습니까?',
      'mdi-office-building-marker',
      'primary',
    )
  }
}

const modalAction = async () => {
  if (mode.value === 'create') {
    await createContAddress(form.value)
    resetForm()
  } else if (mode.value === 'update' && selectedPk.value !== null)
    await patchContAddress(selectedPk.value, { is_current: true } as Partial<AddressInContractor>)
  refConfirmChk.value.close()
}

onBeforeMount(() => {
  props.contractor && (form.value.contractor = props.contractor)
})

onBeforeUnmount(() => {
  // 컴포넌트 언마운트 시 타이머 정리
  if (colorTimeout.value) {
    clearTimeout(colorTimeout.value)
  }
})
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="text-body">
      <h6 class="mb-2">
        <v-icon icon="mdi-office-building-marker" size="small" color="primary" class="mr-1" />
        변경할 주소
      </h6>
      <CRow>
        <CFormLabel sm="2" class="col-lg-2 col-xl-1 col-form-label required"> 주민등록</CFormLabel>

        <CCol sm="12" lg="4" xl="2" class="mb-lg-0 mb-3">
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
        <CCol sm="12" lg="6" xl="4" class="mb-lg-0 mb-3">
          <CFormInput
            v-model="form.id_address1"
            maxlength="35"
            placeholder="주민등록 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(1)"
          />
        </CCol>

        <CCol sm="12" lg="6" xl="2" class="mb-lg-0 mb-3">
          <CFormInput
            ref="refAddress1"
            v-model="form.id_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
          />
        </CCol>

        <CCol sm="12" lg="6" xl="2" class="mb-3">
          <CFormInput
            v-model="form.id_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
          />
        </CCol>
      </CRow>
      <CRow>
        <CFormLabel sm="2" class="col-lg-2 col-xl-1 col-form-label required"> 우편수령</CFormLabel>
        <CCol sm="12" lg="4" xl="2" class="mb-lg-0 mb-3">
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
        <CCol sm="12" lg="6" xl="4" class="mb-lg-0 mb-3">
          <CFormInput
            v-model="form.dm_address1"
            maxlength="50"
            placeholder="우편물 수령 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(2)"
          />
        </CCol>
        <CCol sm="12" lg="6" xl="2" class="mb-lg-0 mb-3">
          <CFormInput
            ref="refAddress2"
            v-model="form.dm_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
          />
        </CCol>
        <CCol sm="12" lg="6" xl="2" class="mb-3">
          <CFormInput
            v-model="form.dm_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
          />
        </CCol>
        <CCol sm="12" lg="2" xl="1" class="pt-1 mb-3">
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
      <h6 class="mb-2">
        <v-icon icon="mdi-office-building-marker" size="small" color="info" class="mr-1" />
        변경전 (현재) 주소
      </h6>
      <CTable
        borderless
        responsive
        align="middle"
        class="mb-0 address-table-transition"
        :color="currentTableColor"
      >
        <CTableBody class="text-center">
          <CTableRow>
            <CTableHeaderCell class="pt-3">주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pt-3 pl-2 text-left">
              ({{ address.id_zipcode }}) {{ address.id_address1 }} {{ address.id_address2 }}
              {{ address.id_address3 }}
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell class="pb-3">우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pb-3 pl-2 text-left">
              ({{ address.dm_zipcode }}) {{ address.dm_address1 }} {{ address.dm_address2 }}
              {{ address.dm_address3 }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
      <v-divider />
      <h6 class="mb-2">
        <v-icon icon="mdi-office-building-marker" size="small" color="warning" class="mr-1" />
        과거 주소 이력
      </h6>
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

<style scoped>
.address-table-transition {
  transition: all 1.5s ease-in-out;
}

.address-table-transition tbody tr {
  transition:
    background-color 1.5s ease-in-out,
    border-color 1.5s ease-in-out;
}

.address-table-transition tbody tr th,
.address-table-transition tbody tr td {
  transition:
    background-color 1.5s ease-in-out,
    border-color 1.5s ease-in-out;
}
</style>
