<script lang="ts" setup>
import {
  computed,
  inject,
  nextTick,
  onBeforeMount,
  onMounted,
  onUpdated,
  type PropType,
  reactive,
  ref,
  watch,
} from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_contract } from '@/utils/pageAuth'
import { useAccount } from '@/store/pinia/account'
import { useProjectData } from '@/store/pinia/project_data'
import { usePayment } from '@/store/pinia/payment'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useContract } from '@/store/pinia/contract'
import { type PayOrder } from '@/store/types/payment'
import type { Contract, ContractFile, Payment, UnitFilter } from '@/store/types/contract'
import { isValidate } from '@/utils/helper'
import { diffDate, numFormat } from '@/utils/baseMixins'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AttatchFile from '@/components/AttatchFile/Index.vue'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AddressForm from '@/views/contracts/List/components/AddressForm.vue'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<Contract>, default: null },
  unitSet: { type: Boolean, default: false },
  isUnion: { type: Boolean, default: false },
  fromPage: { type: [Number, null] as PropType<number | null>, default: null },
})

const emit = defineEmits(['on-submit', 'close', 'subscription-created', 'contract-converted'])

const refPostCode = ref()
const address21 = ref()
const address22 = ref()
const refChangeAddr = ref()
const refAlertModal = ref()
const refConfirmModal = ref()

const sameAddr = ref(false)
const validated = ref(false)
const form = reactive({
  // contract
  pk: null as number | null,
  project: null as null | number,
  order_group_sort: '',
  order_group: null as number | null,
  unit_type: null as number | null,
  serial_number: '',
  activation: true,
  is_sup_cont: false,
  sup_cont_date: null as string | null,

  // key_unit & houseunit
  key_unit: null as number | null, // 4
  key_unit_code: '' as string,
  houseunit: null as number | null, // 5
  houseunit_code: '',
  // cont_key_unit: '', // 디비 계약 유닛
  // cont_houseunit: '', // 디비 동호 유닛
  contract_files: [] as ContractFile[], // scan File

  // contractor
  name: '', // 7
  birth_date: null as string | null, // 8
  gender: '', // 9
  qualification: '2',
  status: '' as '1' | '2' | '3' | '4' | '5' | '', // 1
  reservation_date: null as string | null, // 6-1
  contract_date: null as string | null, // 6-2
  note: '', // 28

  // address
  id_zipcode: '', // 20
  id_address1: '', // 21
  id_address2: '', // 22
  id_address3: '', // 23
  dm_zipcode: '', // 24
  dm_address1: '', // 25
  dm_address2: '', // 26
  dm_address3: '', // 27

  // contact
  cell_phone: '', // 11
  home_phone: '', // 12
  other_phone: '', // 13
  email: '', // 14

  // proLedger
  payment: null as number | null,
  deal_date: null as string | null, // 15
  amount: null as number | null, // 16
  bank_account: null as number | null, // 17
  trader: '', // 18
  installment_order: null as number | null, // 19
})

const matchAddr = computed(() => {
  const zi = form.id_zipcode === form.dm_zipcode
  const a1 = form.id_address1 === form.dm_address1
  const a2 = form.id_address2 === form.dm_address2
  const a3 = form.id_address3 === form.dm_address3
  return zi && a1 && a2 && a3
})

watch(matchAddr, val => sameAddrBtnSet(val))

const isDark = inject('isDark')

const contStore = useContract()
const getOrderGroups = computed(() => contStore.getOrderGroups)
const getKeyUnits = computed(() => contStore.getKeyUnits)
const getHouseUnits = computed(() => contStore.getHouseUnits)

const projectDataStore = useProjectData()
const getTypes = computed(() => projectDataStore.getTypes)

const proLedgerStore = useProLedger()
const allProBankList = computed(() => proLedgerStore.allProBankList)

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const contLabel = computed(() => (form.status !== '1' ? '계약' : '청약'))
const isContract = computed(() => form.status === '2')
const noStatus = computed(() => (form.status === null || form.status === '') && !props.contract)
const downPayOrder = computed(() =>
  payOrderList.value.filter((po: PayOrder) => po.pay_time && po.pay_time <= 1),
)

const downPayments = computed(() =>
  props.contract && props.contract.payments.length > 0
    ? props.contract.payments.filter((p: Payment) => p.installment_order.pay_time === 1)
    : [],
)

const contractor = computed(() => props.contract?.contractor)
const address = computed(() => props.contract?.contractor?.contractoraddress)
const contact = computed(() => props.contract?.contractor?.contractorcontact)

const formsCheck = computed(() => {
  if (props.contract && contractor.value) {
    const a = form.order_group === props.contract.order_group
    const b = form.unit_type === props.contract.unit_type
    const c = form.key_unit === props.contract.key_unit?.pk
    const d = form.houseunit === props.contract.key_unit?.houseunit?.pk
    const e = form.is_sup_cont === props.contract.is_sup_cont
    const f = form.sup_cont_date === props.contract.sup_cont_date
    const g = form.reservation_date === contractor.value.reservation_date
    const h = form.contract_date === contractor.value?.contract_date
    const i = form.name === contractor.value.name
    const j = form.birth_date === contractor.value.birth_date
    const k = form.gender === contractor.value?.gender
    const l = form.qualification === contractor.value?.qualification
    const m = form.cell_phone === contact.value?.cell_phone
    const n = form.home_phone === contact.value?.home_phone
    const o = form.other_phone === contact.value?.other_phone
    const p = form.email === contact.value?.email
    const q = !form.deal_date
    const r = !form.amount
    const s = !form.bank_account
    const t = !form.trader
    const u = !form.installment_order
    const v = form.id_zipcode === address.value?.id_zipcode
    const w = form.id_address1 === address.value?.id_address1
    const x = form.id_address2 === address.value?.id_address2
    const y = form.id_address3 === address.value?.id_address3
    const z = form.dm_zipcode === address.value?.dm_zipcode
    const a1 = form.dm_address1 === address.value?.dm_address1
    const b1 = form.dm_address2 === address.value?.dm_address2
    const c1 = form.dm_address3 === address.value?.dm_address3
    const d1 = form.note === contractor.value?.note

    const e1 = !newFile.value
    const f1 = !editFile.value
    const g1 = !cngFile.value
    const h1 = !delFile.value

    const cond1 = a && b && c && d && e && f && g && h && i && j && u
    const cond2 = k && l && m && n && o && p && q && r && s && t && v
    const cond3 = w && x && y && z && a1 && b1 && c1 && d1 && e1 && f1 && g1 && h1
    return cond1 && cond2 && cond3
  } else return false
})

const allowedPeriod = (paidDate: string) => useAccount().superAuth || diffDate(paidDate) <= 90

const payUpdate = (payment: Payment) => {
  if (allowedPeriod(payment.deal_date)) {
    form.payment = payment.pk
    form.deal_date = payment.deal_date
    form.amount = payment.amount
    form.bank_account = payment.bank_account
    form.trader = payment.trader
    form.installment_order = payment.installment_order.pk
  } else {
    refAlertModal.value.callModal(
      null,
      '거래일로부터 90일이 경과한 입력 데이터는 수정할 수 없습니다. 관리자에게 문의바랍니다.',
    )
  }
}

const payReset = () => {
  form.payment = null
  form.deal_date = null
  form.amount = null
  form.bank_account = null
  form.trader = ''
  form.installment_order = null
}

const getOGSort = (pk: number): string =>
  pk ? getOrderGroups.value.filter(o => o.value == pk)[0].sort : ''

const getKUCode = (pk: number) => getKeyUnits.value.filter(k => k.value === pk).map(k => k.label)[0]

const setOGSort = () =>
  nextTick(() => (form.order_group_sort = getOGSort(Number(form.order_group as number))))

const setKeyCode = () => {
  nextTick(() => {
    form.houseunit = null
    form.key_unit_code = form.key_unit ? getKUCode(Number(form.key_unit)) : ''
    form.serial_number = form.key_unit ? `${form.key_unit_code}-${form.order_group}` : `TEMP-${form.order_group}-${Date.now()}`
  })
}

const unitReset = () => {
  nextTick(() => {
    if (!form.status) formDataReset()
  })
}

const fetchKeyUnitList = (payload: UnitFilter) => contStore.fetchKeyUnitList(payload)
const fetchHouseUnitList = (payload: UnitFilter) => contStore.fetchHouseUnitList(payload)

const typeSelect = () => {
  nextTick(async () => {
    const payload: {
      unit_type?: number
      contract?: number
      available?: 'true' | ''
    } =
      !!props.contract && form.unit_type === props.contract.unit_type
        ? { unit_type: form.unit_type as number, contract: props.contract.pk }
        : { unit_type: form.unit_type as number, available: 'true' }

    form.key_unit = null
    form.houseunit = null

    // unitSet이 true일 때만 KeyUnit과 HouseUnit 목록을 가져옴
    if (props.project && props.unitSet) {
      await fetchKeyUnitList({ project: props.project as number, ...payload })
      await fetchHouseUnitList({ project: props.project as number, ...payload })
    }

    // unitSet이 false일 때는 임시 serial_number 생성
    if (!props.unitSet) {
      form.serial_number = `TEMP-${form.order_group}-${Date.now()}`
    }
  })
}

const remove_sup_cDate = () => (form.is_sup_cont ? (form.sup_cont_date = null) : null)

const formDataReset = () => {
  form.pk = null
  form.project = null
  form.order_group = null
  form.order_group_sort = ''
  form.unit_type = null
  form.serial_number = ''
  form.is_sup_cont = false
  form.sup_cont_date = null
  form.key_unit = null
  form.houseunit = null
  form.key_unit_code = ''
  form.contract_files = []

  // form.contractor = null
  form.name = ''
  form.birth_date = null
  form.gender = ''
  form.qualification = '2'
  form.status = ''
  form.reservation_date = null
  form.contract_date = null
  form.note = ''

  form.payment = null
  form.deal_date = null
  form.amount = null
  form.bank_account = null
  form.trader = ''
  form.installment_order = null

  // form.addressPk = null
  form.id_zipcode = ''
  form.id_address1 = ''
  form.id_address2 = ''
  form.id_address3 = ''
  form.dm_zipcode = ''
  form.dm_address1 = ''
  form.dm_address2 = ''
  form.dm_address3 = ''

  // form.contactPk = null
  form.cell_phone = ''
  form.home_phone = ''
  form.other_phone = ''
  form.email = ''
  contStore.removeContract()
  sameAddr.value = false
}

const formDataSetup = () => {
  if (props.contract) {
    // 기존 contract에 맞는 KeyUnit 목록 불러오기 추가
    if (props.contract.unit_type && props.project) {
      const payload = {
        project: props.project as number,
        unit_type: props.contract.unit_type,
        contract: props.contract.pk,
      }
      fetchKeyUnitList(payload)
      fetchHouseUnitList(payload)
    }
    // contract
    form.pk = props.contract.pk
    form.order_group = props.contract.order_group
    form.order_group_sort = props.contract.order_group_desc.sort
    form.unit_type = props.contract.unit_type
    form.serial_number = props.contract.serial_number
    form.is_sup_cont = form.is_sup_cont || props.contract.is_sup_cont
    form.sup_cont_date = form.sup_cont_date ?? props.contract.sup_cont_date ?? ''
    form.key_unit = props.contract.key_unit?.pk ?? null
    form.key_unit_code = props.contract.key_unit?.unit_code ?? ''
    form.houseunit = props.contract.key_unit?.houseunit?.pk ?? null
    form.contract_files = props.contract.contract_files

    // contractor
    form.name = contractor.value?.name ?? ''
    form.birth_date = contractor.value?.birth_date ?? null
    form.gender = contractor.value?.gender ?? '' // 9
    form.qualification = contractor.value?.qualification ?? '' // 10
    form.status = contractor.value?.status ?? ''
    form.reservation_date = contractor.value?.reservation_date ?? null
    form.contract_date = contractor.value?.contract_date ?? null
    form.note = contractor.value?.note ?? ''

    // address
    if (contractor.value?.status === '2') {
      form.id_zipcode = address.value?.id_zipcode ?? '' // 20
      form.id_address1 = address.value?.id_address1 ?? '' // 21
      form.id_address2 = address.value?.id_address2 ?? '' // 22
      form.id_address3 = address.value?.id_address3 ?? '' // 23
      form.dm_zipcode = address.value?.dm_zipcode ?? '' // 24
      form.dm_address1 = address.value?.dm_address1 ?? ''
      form.dm_address2 = address.value?.dm_address2 ?? '' // 26
      form.dm_address3 = address.value?.dm_address3 ?? '' // 27
    }
    // contact
    form.cell_phone = contact.value?.cell_phone ?? ''
    form.home_phone = contact.value?.home_phone ?? '' // 11 // 12
    form.other_phone = contact.value?.other_phone ?? '' // 13
    form.email = contact.value?.email ?? '' // 14

    sameAddrBtnSet(matchAddr.value)
  }
  form.project = props.project as number
}

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 2) {
    form.id_zipcode = zipcode
    form.id_address1 = address1
    form.id_address2 = ''
    form.id_address3 = address3
    address21.value.$el.nextElementSibling.focus()
  } else if (formNum === 3) {
    form.dm_zipcode = zipcode
    form.dm_address1 = address1
    form.dm_address2 = ''
    form.dm_address3 = address3
    address22.value.$el.nextElementSibling.focus()
  }
}

const sameAddrBtnSet = (chk: boolean) => (sameAddr.value = chk)

const toSame = () => {
  sameAddr.value = !sameAddr.value
  if (sameAddr.value) {
    form.dm_zipcode = form.id_zipcode
    form.dm_address1 = form.id_address1
    form.dm_address2 = form.id_address2
    form.dm_address3 = form.id_address3
  } else {
    form.dm_zipcode = ''
    form.dm_address1 = ''
    form.dm_address2 = ''
    form.dm_address3 = ''
  }
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_contract.value) refConfirmModal.value.callModal()
    else refAlertModal.value.callModal()
  }
}

const RefContFile = ref()
const newFile = ref<File | ''>('')
const editFile = ref<number | ''>('')
const cngFile = ref<File | ''>('')
const delFile = ref<number | undefined>(undefined)

const saveContract = (payload: any) => {
  const { pk, ...getData } = payload as { [key: string]: any }

  const form = new FormData()

  for (const key in getData) form.set(key, getData[key] ?? '')

  if (!pk) contStore.createContractSet(form)
  else contStore.updateContractSet(pk, form)
}

const modalAction = () => {
  // 신규 청약 생성 여부 확인
  const isNewSubscription = !form.pk && form.status === '1'

  // 청약을 계약으로 전환 여부 확인 (기존 계약이 있고, 기존 상태가 '1'(청약)이었는데 현재 form 상태가 '2'(계약)인 경우)
  const isContractConversion =
    props.contract && contractor.value?.status === '1' && form.status === '2'

  saveContract({
    ...form,
    newFile: newFile.value,
    editFile: editFile.value,
    cngFile: cngFile.value,
    delFile: delFile.value,
  })
  validated.value = false
  refConfirmModal.value.close()
  newFile.value = ''
  editFile.value = ''
  cngFile.value = ''
  delFile.value = undefined
  RefContFile.value.doneEdit()

  emit('close')
  // 신규 청약이면 subscription-created 이벤트 (status UI 동기화용)
  if (isNewSubscription) emit('subscription-created')
  // 청약을 계약으로 전환하면 contract-converted 이벤트 (status UI 동기화용)
  if (isContractConversion) emit('contract-converted')
}

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
  else delFile.value = undefined
}

defineExpose({ formDataReset })

// Props 변경 감지를 위한 이전 값 저장
const prevContractPk = ref<number | null>(null)

onBeforeMount(() => paymentStore.fetchPayOrderList(props.project, '1'))
onMounted(() => {
  formDataSetup()
  // 초기 contract pk 저장
  prevContractPk.value = props.contract?.pk ?? null
})

onUpdated(() => {
  // props.contract가 실제로 변경되었을 때만 formDataSetup 호출
  const currentContractPk = props.contract?.pk ?? null
  if (prevContractPk.value !== currentContractPk) {
    formDataSetup()
    prevContractPk.value = currentContractPk
  }
})

onBeforeRouteLeave(() => formDataReset())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCardBody class="text-body">
      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label"> 구분</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <Multiselect
            v-model="form.status"
            placeholder="---------"
            :options="[
              { value: '1', label: '청약' },
              { value: '2', label: '계약' },
            ]"
            required
            autocomplete="label"
            :classes="{
              search: 'form-control multiselect-search',
            }"
            :add-option-on="['enter', 'tab']"
            searchable
            :disabled="!project"
            @change="unitReset"
          />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required"> 차수</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <CFormSelect
            v-model.number="form.order_group"
            required
            :disabled="noStatus"
            @change="setOGSort"
          >
            <option value="">---------</option>
            <option v-for="og in getOrderGroups" :key="og.value" :value="og.value">
              {{ og.label }}
            </option>
          </CFormSelect>
          <CFormFeedback invalid>차수그룹을 선택하세요.</CFormFeedback>
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required"> 타입</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <CFormSelect
            v-model.number="form.unit_type"
            required
            :disabled="form.order_group === null && !contract"
            @change="typeSelect"
          >
            <option value="">---------</option>
            <option v-for="ut in getTypes" :key="ut.value" :value="ut.value">
              {{ ut.label }}
            </option>
          </CFormSelect>
          <CFormFeedback invalid>유니트 타입을 선택하세요.</CFormFeedback>
        </CCol>

        <CFormLabel v-if="unitSet" class="col-sm-2 col-lg-1 col-form-label required">
          {{ contLabel }}코드
        </CFormLabel>
        <CCol v-if="unitSet" sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <CFormSelect
            v-model.number="form.key_unit"
            required
            :disabled="form.unit_type === null && !contract"
            @change="setKeyCode"
          >
            <option value="">---------</option>
            <option v-for="ku in getKeyUnits.slice(0, 1)" :key="ku.value" :value="ku.value">
              {{ ku.label }}
            </option>
          </CFormSelect>
          <CFormFeedback invalid> {{ contLabel }}코드를 선택하세요.</CFormFeedback>
        </CCol>

        <CFormLabel v-if="unitSet" class="col-sm-2 col-lg-1 col-form-label"> 동호수</CFormLabel>
        <CCol v-if="unitSet" sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <Multiselect
            v-model.number="form.houseunit"
            :options="getHouseUnits"
            placeholder="---------"
            autocomplete="label"
            :classes="{
              search: 'form-control multiselect-search',
            }"
            :add-option-on="['enter', 'tab']"
            searchable
            :disabled="form.key_unit === null && !contract"
          />
          <CFormFeedback invalid>동호수를 선택하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow>
        <CAlert
          :color="isDark ? 'default' : form.is_sup_cont ? 'success' : 'warning'"
          class="py-3 mb-0"
        >
          <CRow>
            <CFormLabel class="col-sm-2 col-lg-1 col-form-label">공급계약</CFormLabel>
            <CCol sm="10" lg="2" class="pt-1">
              <v-checkbox-btn
                v-model="form.is_sup_cont"
                label="체결 여부"
                :color="isDark ? '#857DCC' : '#321FDB'"
                density="compact"
                :disabled="!isContract"
                @click="remove_sup_cDate"
              />
            </CCol>
            <CFormLabel class="col-sm-2 col-lg-1 col-form-label">체결일자</CFormLabel>
            <CCol sm="10" lg="2">
              <DatePicker
                v-model="form.sup_cont_date"
                maxlength="10"
                placeholder="공급계약 체결일"
                :required="form.is_sup_cont"
                :disabled="!form.is_sup_cont"
              />
              <CFormFeedback invalid>공급계약 체결일을 입력하세요.</CFormFeedback>
            </CCol>
            <CCol class="form-text">
              공급계약이란 조합원 가입계약이 아닌
              <b>
                사업계획승인 후 조합원이 시공사와 체결하는 주택공급계약 체결 또는 일반(임의)분양
                계약
              </b>
              을 지칭하는 것으로 이에 해당되는 경우 이 항목을 체크.
            </CCol>
          </CRow>
        </CAlert>
      </CRow>

      <v-divider />

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required">
          {{ contLabel }}일자
        </CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <DatePicker
            v-show="form.status === '1'"
            v-model="form.reservation_date"
            placeholder="청약일자"
            :required="form.status === '1'"
            :disabled="noStatus"
          />
          <DatePicker
            v-show="form.status !== '1'"
            v-model="form.contract_date"
            placeholder="계약일자"
            :required="isContract"
            :disabled="noStatus"
          />
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required">
          {{ contLabel }}자명
        </CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <CFormInput
            v-model="form.name"
            maxlength="20"
            :placeholder="`${contLabel}자명을 입력하세요`"
            required
            :disabled="noStatus"
          />
          <CFormFeedback invalid> {{ contLabel }}자명을 입력하세요.</CFormFeedback>
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required"> 생년월일</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <DatePicker
            v-model="form.birth_date"
            maxlength="10"
            placeholder="생년월일"
            :required="isContract"
            :disabled="noStatus"
          />
          <CFormFeedback invalid>생년월일 입력하세요.</CFormFeedback>
        </CCol>

        <CCol v-show="isContract" xs="6" lg="2" class="pt-2 p-0 text-center">
          <div class="form-check form-check-inline">
            <input
              id="male"
              v-model="form.gender"
              class="form-check-input"
              type="radio"
              value="M"
              name="gender"
              :required="isContract"
              :disabled="!isContract"
            />
            <label class="form-check-label" for="male">남</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              id="female"
              v-model="form.gender"
              class="form-check-input"
              type="radio"
              value="F"
              name="gender"
              :disabled="!isContract"
            />
            <label class="form-check-label" for="female">여</label>
          </div>
          <CFormFeedback invalid>성별을 선택하세요.</CFormFeedback>
        </CCol>

        <CCol v-if="contract && isUnion && form.order_group_sort === '1'" xs="6" lg="2">
          <CFormSelect v-model="form.qualification" required :disabled="!isContract">
            <option value="">---------</option>
            <option value="2">미인가</option>
            <option value="3">인가</option>
            <option value="4">부적격</option>
          </CFormSelect>
          <CFormFeedback invalid> 등록상태를 선택하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label required"> 휴대전화</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <input
            v-model="form.cell_phone"
            v-maska
            data-maska="['###-###-####', '###-####-####']"
            class="form-control"
            maxlength="13"
            placeholder="휴대전화번호를 선택하세요"
            required
            :disabled="noStatus"
          />
          <CFormFeedback invalid>휴대전화번호를 입력하세요.</CFormFeedback>
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label"> 이메일</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <CFormInput
            v-model="form.email"
            type="email"
            maxlength="30"
            placeholder="이메일 주소를 입력하세요."
            :disabled="noStatus"
          />
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label"> 집전화</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <input
            v-model="form.home_phone"
            v-maska
            data-maska="['###-###-####', '###-####-####']"
            class="form-control"
            maxlength="13"
            placeholder="집전화번호를 선택하세요"
            :disabled="noStatus"
          />
        </CCol>

        <CFormLabel class="col-sm-2 col-lg-1 col-form-label"> 기타 연락처</CFormLabel>
        <CCol sm="10" lg="2" class="mb-sm-3 mb-lg-0">
          <input
            v-model="form.other_phone"
            v-maska
            data-maska="['###-###-####', '###-####-####']"
            class="form-control"
            maxlength="13"
            placeholder="기타 연락처를 입력하세요."
            :disabled="noStatus"
          />
        </CCol>
      </CRow>

      <CRow>
        <CAlert :color="isDark ? 'default' : 'secondary'" class="pt-3 pb-sm-3 pb-lg-0">
          <CRow v-if="downPayments.length" class="mb-3">
            <CCol>
              <CTable borderless hover small color="light" responsive>
                <CTableBody>
                  <CTableRow
                    v-for="(payment, i) in downPayments as Payment[]"
                    :key="payment.pk"
                    class="text-center mb-1"
                    :color="form.payment === payment.pk ? 'primary' : ''"
                  >
                    <CTableDataCell>
                      계약금
                      <router-link
                        v-c-tooltip="'건별 납부 관리'"
                        :to="{
                          name: '건별 납부 관리 - 상세',
                          params: { contractId: contract.pk },
                        }"
                      >
                        납부내역
                      </router-link>
                      [{{ i + 1 }}]
                    </CTableDataCell>
                    <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
                    <CTableDataCell class="text-right">
                      <router-link
                        v-c-tooltip="'건별 납부 관리'"
                        :to="{
                          name: '건별 납부 관리 - 상세',
                          params: { contractId: contract.pk },
                        }"
                      >
                        {{ numFormat(payment.amount) }}
                      </router-link>
                    </CTableDataCell>
                    <CTableDataCell>
                      {{
                        allProBankList
                          .filter(b => b.pk === payment.bank_account)
                          .map(b => b.alias_name)[0]
                      }}
                    </CTableDataCell>
                    <CTableDataCell>{{ payment.trader }}</CTableDataCell>
                    <CTableDataCell>{{ payment.installment_order.__str__ }}</CTableDataCell>
                    <CTableDataCell>
                      <v-btn
                        type="button"
                        color="success"
                        size="x-small"
                        @click="payUpdate(payment)"
                      >
                        수정
                      </v-btn>
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCol>
          </CRow>

          <CRow>
            <CFormLabel sm="2" class="col-lg-1 col-form-label">
              {{ contLabel }}금 {{ !form.payment ? '등록' : '수정' }}
            </CFormLabel>
            <CCol sm="12" lg="2" class="mb-3">
              <DatePicker
                v-model="form.deal_date"
                placeholder="입금일자"
                maxlength="10"
                :disabled="noStatus"
              />
            </CCol>
            <CCol sm="12" md="6" lg="2" class="mb-3">
              <CFormInput
                v-model.number="form.amount"
                type="number"
                min="0"
                placeholder="입금액"
                :required="form.deal_date"
                :disabled="noStatus"
              />
              <CFormFeedback invalid>입금액을 입력하세요.</CFormFeedback>
            </CCol>
            <CCol sm="12" md="6" lg="2" class="mb-3">
              <CFormSelect
                v-model="form.bank_account"
                :required="form.deal_date"
                :disabled="noStatus"
              >
                <option value="">납부계좌 선택</option>
                <option v-for="pb in allProBankList" :key="pb.pk as number" :value="pb.pk">
                  {{ pb.alias_name }}
                </option>
              </CFormSelect>
              <CFormFeedback invalid>납부계좌를 선택하세요.</CFormFeedback>
            </CCol>
            <CCol sm="12" md="6" lg="2" class="mb-3">
              <CFormInput
                v-model="form.trader"
                maxlength="20"
                placeholder="입금자명을 입력하세요"
                :required="form.deal_date"
                :disabled="noStatus"
              />
              <CFormFeedback invalid>입금자명을 입력하세요.</CFormFeedback>
            </CCol>
            <CCol sm="12" md="6" lg="2" class="mb-3">
              <CFormSelect
                v-model="form.installment_order"
                :required="form.deal_date"
                :disabled="noStatus"
              >
                <option value="">납부회차 선택</option>
                <option v-for="po in downPayOrder" :key="po.pk as number" :value="po.pk">
                  {{ po.__str__ }}
                </option>
              </CFormSelect>
              <CFormFeedback invalid>납부회차를 선택하세요.</CFormFeedback>
            </CCol>
            <CCol v-if="form.payment" xs="3" md="2" lg="1" class="pt-1 mb-3">
              <a href="javascript:void(0)" @click="payReset">Reset</a>
            </CCol>
          </CRow>
        </CAlert>
      </CRow>

      <CRow v-show="isContract">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 주민등록 주소</CFormLabel>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0 mb-3">
          <CInputGroup>
            <CInputGroupText @click="refPostCode.initiate(2)"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.id_zipcode"
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              :required="isContract"
              :disabled="!isContract || !!address?.id_zipcode"
              @focus="refPostCode.initiate(2)"
            />
            <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0 mb-3">
          <CFormInput
            v-model="form.id_address1"
            maxlength="35"
            placeholder="주민등록 주소를 입력하세요"
            :required="isContract"
            :disabled="!isContract || !!address?.id_zipcode"
            @focus="refPostCode.initiate(2)"
          />
          <CFormFeedback invalid>주민등록 주소를 입력하세요.</CFormFeedback>
        </CCol>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0 mb-3">
          <CFormInput
            ref="address21"
            v-model="form.id_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
            :disabled="!isContract || !!address?.id_zipcode"
          />
          <CFormFeedback invalid>상세주소를 입력하세요.</CFormFeedback>
        </CCol>

        <CCol sm="12" md="6" lg="2">
          <CFormInput
            v-model="form.id_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
            :disabled="!isContract || !!address?.id_zipcode"
          />
        </CCol>
      </CRow>

      <CRow v-show="isContract">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 우편수령 주소</CFormLabel>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0 mb-3">
          <CInputGroup>
            <CInputGroupText @click="refPostCode.initiate(3)"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.dm_zipcode"
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              :required="isContract"
              :disabled="!isContract || !!address?.dm_zipcode"
              @focus="refPostCode.initiate(3)"
            />
            <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0 mb-3">
          <CFormInput
            v-model="form.dm_address1"
            maxlength="50"
            placeholder="우편물 수령 주소를 입력하세요"
            :required="isContract"
            :disabled="!isContract || !!address?.dm_zipcode"
            @focus="refPostCode.initiate(3)"
          />
          <CFormFeedback invalid> 우편물 수령 주소를 입력하세요.</CFormFeedback>
        </CCol>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0 mb-3">
          <CFormInput
            ref="address22"
            v-model="form.dm_address2"
            maxlength="50"
            placeholder="상세주소를 입력하세요"
            :disabled="!isContract || !!address?.dm_zipcode"
          />
          <CFormFeedback invalid>상세주소를 입력하세요.</CFormFeedback>
        </CCol>
        <CCol sm="12" md="6" lg="2" class="mb-3">
          <CFormInput
            v-model="form.dm_address3"
            maxlength="30"
            placeholder="참고항목을 입력하세요"
            :disabled="!isContract || !!address?.dm_zipcode"
          />
        </CCol>
        <CCol sm="12" lg="1" class="mb-3 pl-0">
          <v-checkbox-btn
            v-if="!address?.id_zipcode || !address?.dm_zipcode"
            id="to-same"
            v-model="sameAddr"
            label="상동"
            :color="isDark ? '#857DCC' : '#321FDB'"
            :disabled="!isContract || !form.id_zipcode"
            @click="toSame"
          />
          <v-btn
            v-else
            color="primary"
            size="small"
            class="mt-1"
            :disabled="!write_contract"
            @click="refChangeAddr.callModal()"
          >
            주소변경
          </v-btn>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label"> 비고</CFormLabel>
        <CCol sm="10" lg="11" class="mb-md-3 mb-lg-0">
          <CFormTextarea v-model="form.note" placeholder="기타 특이사항" :disabled="noStatus" />
        </CCol>
      </CRow>

      <AttatchFile
        ref="RefContFile"
        v-show="isContract"
        label-class="col-sm-2 col-lg-1"
        label-name="계약서 파일"
        :disabled="!form.status"
        :attatch-files="form.contract_files"
        :deleted="delFile"
        @file-control="fileControl"
      />
    </CCardBody>

    <CCardFooter class="text-right">
      <v-btn type="button" :color="btnLight" @click="$emit('close')">닫기</v-btn>
      <!--      <v-btn-->
      <!--        v-if="write_contract && contract"-->
      <!--        type="button"-->
      <!--        color="warning"-->
      <!--        @click="deleteContract"-->
      <!--      >-->
      <!--        삭제-->
      <!--      </v-btn>-->
      <v-btn
        v-if="write_contract"
        type="submit"
        :color="contract ? 'success' : 'primary'"
        :disabled="!form.status || formsCheck"
      >
        <v-icon icon="mdi-check-circle-outline" class="mr-2" />
        저장
      </v-btn>
    </CCardFooter>
  </CForm>

  <DaumPostcode ref="refPostCode" @address-callback="addressCallback" />

  <FormModal ref="refChangeAddr" size="xl">
    <template #header>주소변경 등록</template>
    <template #default>
      <AddressForm
        :contractor="contractor?.pk as number"
        :address="address"
        @close="refChangeAddr.close()"
      />
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> {{ contLabel }} 정보 등록</template>
    <template #default>
      {{ contLabel }} 정보 {{ contract ? '수정등록' : '신규등록' }}을 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn :color="contract ? 'success' : 'primary'" size="small" @click="modalAction">
        저장
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
