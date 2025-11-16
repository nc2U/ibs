<script lang="ts" setup>
import { ref, reactive, computed, nextTick, onBeforeMount, type PropType, inject, watch } from 'vue'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_project_cash } from '@/utils/pageAuth'
import { getToday, diffDate, numFormat, cutString } from '@/utils/baseMixins'
import { useAccount } from '@/store/pinia/account'
import { useProCash } from '@/store/pinia/proCash'
import { usePayment } from '@/store/pinia/payment'
import { useContract } from '@/store/pinia/contract'
import { type ProBankAcc, type ProjectCashBook, type ProSepItems } from '@/store/types/proCash'
import BankAcc from '../../Manage/components/BankAcc.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  imprest: { type: Object as PropType<ProjectCashBook>, default: null },
})

const transfers = inject<number[]>('transfers')
const cancels = inject<number[]>('cancels')

const emit = defineEmits(['multi-submit', 'on-delete', 'close', 'on-bank-update'])

const refBankAcc = ref()
const refDelModal = ref()
const refAlertModal = ref()

const sepItem = reactive<ProSepItems>({
  pk: null,
  project_account_d2: null,
  project_account_d3: null,
  is_imprest: true,
  contract: null,
  installment_order: null,
  content: '',
  trader: '',
  income: null,
  outlay: null,
  evidence: '',
  note: '',
})

const validated = ref(false)

const form = reactive<
  ProjectCashBook & {
    bank_account_to: null | number
    ba_is_imprest: boolean
    charge: null | number
  }
>({
  pk: null,
  project: null,
  sort: null,
  project_account_d2: null,
  project_account_d3: null,
  sepItems: [],
  is_separate: false,
  separated: null,
  is_imprest: true,
  contract: null,
  installment_order: null,
  content: '',
  trader: '',
  bank_account: null,
  bank_account_to: null,
  ba_is_imprest: true,
  income: null,
  outlay: null,
  charge: null,
  evidence: '',
  note: '',
  deal_date: getToday(),
})

const formsCheck = computed(() => {
  if (props.imprest) {
    const a = form.project === props.imprest.project
    const b = form.sort === props.imprest.sort
    const c = form.project_account_d2 === props.imprest.project_account_d2
    const d = form.project_account_d3 === props.imprest.project_account_d3
    const e = form.contract === props.imprest.contract
    const f = form.installment_order === props.imprest.installment_order
    const g = form.content === props.imprest.content
    const h = form.trader === props.imprest.trader
    const i = form.bank_account === props.imprest.bank_account
    const j = form.income === props.imprest.income
    const k = form.outlay === props.imprest.outlay
    const l = form.evidence === props.imprest.evidence
    const m = form.note === props.imprest.note
    const n = form.deal_date === props.imprest.deal_date
    const o = form.is_separate === props.imprest.is_separate

    return a && b && c && d && e && f && g && h && i && j && k && l && m && n && o
  } else return false
})

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const proCashStore = useProCash()
const formAccD2List = computed(() => proCashStore.formAccD2List)
const formAccD3List = computed(() => proCashStore.formAccD3List)
const getImpBankAccs = computed(() => proCashStore.getImpBankAccs)
const allProBankAccList = computed(() => proCashStore.allProBankAccountList)

const proImpBankAccs = computed(() => {
  const ba = props.imprest ? props.imprest.bank_account : 0
  const ba_desc = props.imprest ? props.imprest.bank_account_desc : ''
  const isExist = !!getImpBankAccs.value.filter(b => b.value === ba).length

  return !ba || isExist
    ? getImpBankAccs.value
    : [...[{ value: ba, label: ba_desc }], ...getImpBankAccs.value]
})

const isImprest = computed(() =>
  form.bank_account_to
    ? allProBankAccList.value.filter(ba => ba.pk === form.bank_account_to)[0].is_imprest
    : true,
)

const fetchProFormAccD2List = (d1: number | null, sort: number | null) =>
  proCashStore.fetchProFormAccD2List(d1, sort)
const fetchProFormAccD3List = (d2: number | null, sort: number | null) =>
  proCashStore.fetchProFormAccD3List(d2, sort)

const requireItem = computed(() => !!form.project_account_d2 && !!form.project_account_d3)

const sepDisabled = computed(() => {
  const disabled = !!form.project_account_d2 || !!form.project_account_d3
  return props.imprest ? disabled || (props.imprest.sepItems?.length ?? 0) : disabled
})

const sepSummary = computed(() => {
  if (!props.imprest?.sepItems?.length) return [0, 0]

  const inc = props.imprest.sepItems
    .map((s: ProSepItems) => s.income || 0)
    .reduce((res: number, el: number) => res + el, 0)
  const out = props.imprest.sepItems
    .map((s: ProSepItems) => s.outlay || 0)
    .reduce((res: number, el: number) => res + el, 0)
  return [inc, out]
})

const sepUpdate = (sep: ProjectCashBook) => {
  sepItem.pk = sep.pk
  sepItem.project_account_d2 = sep.project_account_d2
  sepItem.project_account_d3 = sep.project_account_d3
  sepItem.contract = sep.contract
  sepItem.installment_order = sep.installment_order
  sepItem.content = sep.content
  sepItem.trader = sep.trader
  sepItem.evidence = sep.evidence
  sepItem.outlay = sep.outlay
  sepItem.income = sep.income
  sepItem.note = sep.note
}

const sepRemove = () => {
  sepItem.pk = null
  sepItem.project_account_d2 = null
  sepItem.project_account_d3 = null
  sepItem.contract = null
  sepItem.installment_order = null
  sepItem.content = ''
  sepItem.trader = ''
  sepItem.evidence = ''
  sepItem.outlay = null
  sepItem.income = null
  sepItem.note = ''
}

const isModify = computed(() => {
  if (!form.is_separate) return !!props.imprest
  else return !!sepItem.pk
})

const callAccount = () => {
  nextTick(() => {
    const sort = form.sort === 1 || form.sort === 2 ? form.sort : null
    const d2 = form.project_account_d2
    fetchProFormAccD2List(null, sort)
    fetchProFormAccD3List(d2, sort)
  })
}

const sort_change = (event: Event) => {
  if (!form.is_separate) {
    const el = event.target as HTMLSelectElement
    if (el.value === '1') form.outlay = null
    if (el.value === '2') form.income = null
    if (el.value === '3') {
      form.project_account_d2 = (transfers ?? [17, 73])[0]
      form.project_account_d3 = (transfers ?? [17, 73])[1]
      form.trader = ''
    } else if (el.value === '4') {
      form.project_account_d2 = (cancels ?? [18, 75])[0]
      form.project_account_d3 = (cancels ?? [18, 75])[1]
    } else {
      form.project_account_d2 = null
      form.project_account_d3 = null
    }
  } else {
    const el = event.target as HTMLSelectElement
    sepItem.project_account_d2 = null
    sepItem.project_account_d3 = null
    if (el.value === '1') sepItem.outlay = null
    if (el.value === '2') {
      form.evidence = '0'
      sepItem.income = null
    }
  }
  callAccount()
}

const d1_change = () => {
  form.project_account_d3 = null
  callAccount()
}

const sepD1_change = () => {
  sepItem.project_account_d3 = null
  nextTick(() => {
    const sort = form.sort
    const d2 = sepItem.project_account_d2
    fetchProFormAccD2List(null, sort)
    fetchProFormAccD3List(d2, sort)
  })
}

const isFormContShow = ref(false)
const isRelatedCont = (d3: number) =>
  formAccD3List.value.filter(d => d.pk === d3)[0]?.is_related_contract

watch(form, val => {
  if (val.project_account_d3) {
    if (isRelatedCont(val.project_account_d3)) {
      isFormContShow.value = true
    } else {
      isFormContShow.value = false
      val.contract = null
      val.installment_order = null
    }
  } else {
    isFormContShow.value = false
    val.contract = null
    val.installment_order = null
  }
})

const isSepItemContShow = ref(false)
watch(sepItem, val => {
  if (val.project_account_d3) {
    if (isRelatedCont(val.project_account_d3)) {
      isSepItemContShow.value = true
    } else {
      isSepItemContShow.value = false
      val.contract = null
      val.installment_order = null
    }
  } else {
    isSepItemContShow.value = false
    val.contract = null
    val.installment_order = null
  }
})

const contStore = useContract()
const getContracts = computed(() => contStore.getContracts)

const accountStore = useAccount()
const allowedPeriod = computed(() =>
  props.imprest?.deal_date ? accountStore.superAuth || diffDate(props.imprest.deal_date) <= 30 : 0,
)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    form.ba_is_imprest = isImprest.value
    const payload = !form.is_separate
      ? { formData: form, sepData: null }
      : { formData: form, sepData: sepItem }

    if (write_project_cash.value) {
      if (props.imprest) {
        if (allowedPeriod.value) {
          emit('multi-submit', payload)
          emit('close')
        } else
          refAlertModal.value.callModal(
            null,
            '거래일로부터 30일이 경과한 건은 수정할 수 없습니다. 관리자에게 문의바랍니다.',
          )
      } else {
        emit('multi-submit', payload)
        emit('close')
      }
    } else refAlertModal.value.callModal()
    validated.value = false
  }
}

const deleteConfirm = () => {
  if (write_project_cash.value)
    if (allowedPeriod.value) refDelModal.value.callModal()
    else
      refAlertModal.value.callModal(
        null,
        '거래일로부터 30일이 경과한 건은 삭제할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  else refAlertModal.value.callModal()
}

const deleteObject = () => {
  emit('on-delete', {
    project: props.imprest?.project,
    pk: props.imprest?.pk,
  })
  refDelModal.value.close()
  emit('close')
}

const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)

const formDataSetup = () => {
  if (props.imprest) {
    form.pk = props.imprest.pk
    form.project = props.imprest.project
    form.sort = props.imprest.sort
    form.project_account_d2 = props.imprest.project_account_d2
    form.project_account_d3 = props.imprest.project_account_d3
    form.contract = props.imprest.contract
    form.installment_order = props.imprest.installment_order
    form.content = props.imprest.content
    form.trader = props.imprest.trader
    form.bank_account = props.imprest.bank_account
    form.income = props.imprest.income
    form.outlay = props.imprest.outlay
    form.evidence = props.imprest.evidence
    form.note = props.imprest.note
    form.deal_date = props.imprest.deal_date
    form.is_separate = props.imprest.is_separate
    form.separated = props.imprest.separated
  }
  callAccount()
}

onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">거래일자</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.deal_date"
                  required
                  maxlength="10"
                  placeholder="거래일자"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">구분</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.sort"
                  required
                  :disabled="imprest && !!imprest.sort"
                  @change="sort_change"
                >
                  <option value="">---------</option>
                  <option value="1">입금</option>
                  <option value="2">출금</option>
                  <option v-if="!form.is_separate" value="3">대체</option>
                  <option v-if="!form.is_separate" value="4">취소</option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                계정[상위분류]
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.project_account_d2"
                  :required="!form.is_separate"
                  :disabled="!form.sort || form.is_separate || form.sort === 3 || form.sort === 4"
                  @change="d1_change"
                >
                  <option value="">---------</option>
                  <option v-for="d1 in formAccD2List" :key="d1.pk" :value="d1.pk">
                    {{ d1.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                계정[하위분류]
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.project_account_d3"
                  :required="!form.is_separate"
                  :disabled="
                    !form.project_account_d2 ||
                    form.is_separate ||
                    form.sort === 3 ||
                    form.sort === 4
                  "
                >
                  <option value="">---------</option>
                  <option v-for="d2 in formAccD3List" :key="d2.pk" :value="d2.pk">
                    <template v-if="form.sort === 3">대체</template>
                    <template v-else-if="form.sort === 4">취소</template>
                    <template v-else>{{ d2.name }}</template>
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow v-show="isFormContShow" class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계약(자)정보</CFormLabel>
              <CCol sm="8">
                <MultiSelect
                  v-model.number="form.contract"
                  mode="single"
                  :options="getContracts"
                  :disabled="!form.sort || form.is_separate"
                  placeholder="계약 정보 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">납부회차정보</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.installment_order"
                  :disabled="
                    !form.project_account_d2 ||
                    form.project_account_d2 > 2 ||
                    form.is_separate ||
                    form.sort === 2 ||
                    !form.contract
                  "
                >
                  <option value="">---------</option>
                  <option v-for="order in payOrderList" :value="order.pk" :key="order?.pk ?? 0">
                    <template>{{ order.pay_name }}</template>
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">적요</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.content"
                  maxlength="50"
                  placeholder="거래 내용"
                  :disabled="!form.sort"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">거래처</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.trader"
                  v-c-tooltip="{
                    content:
                      '분양대금(분담금) 수납 건인 경우 반드시 해당 계좌에 기재된 입금자를 기재',
                    placement: 'top',
                  }"
                  maxlength="20"
                  placeholder="거래처 (수납자)"
                  :required="form.sort && form.sort !== 3"
                  :disabled="!form.sort || form.sort === 3"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">
                {{ !imprest && form.sort === 3 ? '출금' : '거래' }}계좌
                <a href="javascript:void(0)">
                  <CIcon name="cilCog" @click="refBankAcc.callModal()" />
                </a>
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model.number="form.bank_account" required :disabled="!form.sort">
                  <option value="">---------</option>
                  <option v-for="ba in proImpBankAccs" :key="ba.value as number" :value="ba.value">
                    {{ ba.label }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow v-if="form.sort === 2">
              <CFormLabel class="col-sm-4 col-form-label required">지출증빙</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model="form.evidence"
                  :required="!form.is_separate"
                  :disabled="form.is_separate"
                >
                  <option value="">---------</option>
                  <option value="0">증빙 없음</option>
                  <option value="1">세금계산서</option>
                  <option value="2">계산서(면세)</option>
                  <option value="3">카드전표/현금영수증</option>
                  <option value="4">간이영수증</option>
                  <option value="5">거래명세서</option>
                  <option value="6">입금표</option>
                  <option value="7">지출결의서</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <CRow v-if="!imprest && form.sort === 3">
              <CFormLabel class="col-sm-4 col-form-label required"> 입금계좌</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.bank_account_to"
                  required
                  :disabled="form.sort !== 3"
                  @change="isImprest"
                >
                  <option value="">---------</option>
                  <option v-for="ba in allProBankAccList" :key="ba.pk as number" :value="ba.pk">
                    {{ ba.alias_name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: form.sort !== 1 }">
                출금액
              </CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.outlay"
                  type="number"
                  min="0"
                  placeholder="출금 금액"
                  :required="form.sort !== 1"
                  :disabled="form.sort === 1 || !form.sort || (imprest && !imprest.outlay)"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow v-if="form.sort === 1 || imprest">
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: form.sort === 1 }">
                입금액
              </CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.income"
                  type="number"
                  min="0"
                  placeholder="입금 금액"
                  :required="form.sort === 1"
                  :disabled="form.sort !== 1 || !form.sort || (imprest && !imprest.income)"
                />
              </CCol>
            </CRow>
            <CRow v-else>
              <CFormLabel class="col-sm-4 col-form-label"> 출금 수수료</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.charge"
                  type="number"
                  min="0"
                  placeholder="출금 수수료"
                  :disabled="!form.sort || form.sort === 4 || form.is_separate"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.note" placeholder="특이사항" :disabled="!form.sort" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol class="text-medium-emphasis">
            <CFormCheck
              id="is_separate"
              v-model="form.is_separate"
              label="별도 분리기록 거래 건 - 여러 계정 항목이 1회에 입·출금되어 별도 분리 기록이 필요한 거래인 경우."
              :disabled="sepDisabled"
            />
          </CCol>
        </CRow>
      </div>

      <div v-if="form.is_separate">
        <hr v-if="imprest && imprest.sepItems && imprest.sepItems.length > 0" />
        <CRow v-if="imprest && imprest.sepItems && imprest.sepItems.length > 0" class="mb-3">
          <CCol>
            <strong>
              <CIcon name="cilDescription" class="mr-2" />
              {{ sepSummary[0] ? `입금액 합계 : ${numFormat(sepSummary[0])}` : '' }}
              {{ sepSummary[1] ? `출금액 합계 : ${numFormat(sepSummary[1])}` : '' }}
            </strong>
          </CCol>
        </CRow>

        <div v-if="imprest">
          <CRow
            v-for="(sep, i) in imprest.sepItems"
            :key="sep.pk"
            class="mb-1"
            :class="sep.pk === sepItem.pk ? 'text-success text-decoration-underline' : ''"
          >
            <CCol sm="1">{{ i + 1 }}</CCol>
            <CCol sm="2">{{ sep.trader }}</CCol>
            <CCol sm="5">{{ cutString(sep.content, 20) }}</CCol>
            <CCol sm="2" class="text-right">
              {{ sep.income ? numFormat(sep.income) : numFormat(sep.outlay as number) }}
            </CCol>
            <CCol sm="2" class="text-right">
              <v-btn
                type="button"
                color="success"
                size="x-small"
                @click="sepUpdate(sep as ProjectCashBook)"
              >
                수정
              </v-btn>
            </CCol>
          </CRow>
        </div>

        <v-divider />

        <CRow class="mb-3">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 계정[상위분류]</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.project_account_d2"
                      required
                      :disabled="!form.sort"
                      @change="sepD1_change"
                    >
                      <option value="">---------</option>
                      <option v-for="d1 in formAccD2List" :key="d1.pk" :value="d1.pk">
                        {{ d1.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 계정[하위분류]</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.project_account_d3"
                      :disabled="!sepItem.project_account_d2"
                      required
                    >
                      <option value="">---------</option>
                      <option v-for="d2 in formAccD3List" :key="d2.pk" :value="d2.pk">
                        {{ d2.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>

            <CRow v-show="isSepItemContShow" class="mt-3">
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label"> 계약(자)정보</CFormLabel>
                  <CCol sm="8">
                    <MultiSelect
                      v-model.number="sepItem.contract"
                      mode="single"
                      :options="getContracts"
                      :disabled="!sepItem.project_account_d3"
                      placeholder="계약 정보 선택"
                    />
                  </CCol>
                </CRow>
              </CCol>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label">납부회차정보</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.installment_order"
                      :disabled="
                        !sepItem.project_account_d2 ||
                        sepItem.project_account_d2 > 2 ||
                        form.sort === 2 ||
                        !sepItem.contract
                      "
                    >
                      <option value="">---------</option>
                      <option v-for="order in payOrderList" :value="order.pk" :key="order?.pk ?? 0">
                        <template>{{ order.pay_name }}</template>
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 적요</CFormLabel>
                  <CCol sm="8">
                    <CFormInput
                      v-model="sepItem.content"
                      maxlength="50"
                      placeholder="거래 내용"
                      required
                    />
                  </CCol>
                </CRow>
              </CCol>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 거래처</CFormLabel>
                  <CCol sm="8">
                    <CFormInput
                      v-model="sepItem.trader"
                      v-c-tooltip="{
                        content:
                          '분양대금(분담금) 수납 건인 경우 반드시 해당 계좌에 기재된 입금자를 기재',
                        placement: 'top',
                      }"
                      maxlength="20"
                      placeholder="거래처 (수납자)"
                      required
                    />
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label"> 거래계좌</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="form.bank_account" disabled>
                      <option value="">---------</option>
                      <option
                        v-for="ba in proImpBankAccs"
                        :key="ba.value as number"
                        :value="ba.value"
                      >
                        {{ ba.label }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>

              <CCol sm="6">
                <CRow v-if="form.sort === 2">
                  <CFormLabel class="col-sm-4 col-form-label required"> 지출증빙</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model="sepItem.evidence" required>
                      <option value="">---------</option>
                      <option value="0">증빙 없음</option>
                      <option value="1">세금계산서</option>
                      <option value="2">계산서(면세)</option>
                      <option value="3">카드전표/현금영수증</option>
                      <option value="4">간이영수증</option>
                      <option value="5">거래명세서</option>
                      <option value="6">입금표</option>
                      <option value="7">지출결의서</option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel
                    class="col-sm-4 col-form-label"
                    :class="{ required: form.sort === 2 }"
                  >
                    출금액
                  </CFormLabel>
                  <CCol sm="8">
                    <CFormInput
                      v-model.number="sepItem.outlay"
                      type="number"
                      min="0"
                      placeholder="출금 금액"
                      :required="form.sort === 2"
                      :disabled="form.sort !== 2"
                    />
                  </CCol>
                </CRow>
              </CCol>

              <CCol sm="6">
                <CRow>
                  <CFormLabel
                    class="col-sm-4 col-form-label"
                    :class="{ required: form.sort === 1 }"
                  >
                    입금액
                  </CFormLabel>
                  <CCol sm="8">
                    <CFormInput
                      v-model.number="sepItem.income"
                      type="number"
                      min="0"
                      placeholder="입금 금액"
                      :required="form.sort === 1"
                      :disabled="form.sort !== 1"
                    />
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="sepItem.note" placeholder="특이사항" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" :color="btnLight" @click="emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          v-if="sepItem.pk"
          size="small"
          type="button"
          :color="btnLight"
          variant="outlined"
          @click="sepRemove"
        >
          취소
        </v-btn>
        <v-btn
          type="submit"
          size="small"
          :color="isModify ? 'success' : 'primary'"
          :disabled="formsCheck && requireItem"
        >
          저장
        </v-btn>
        <v-btn v-if="isModify" size="small" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 운영비(전도금) 거래 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />

  <BankAcc ref="refBankAcc" @on-bank-update="onBankUpdate" />
</template>
