<script lang="ts" setup>
import { ref, reactive, computed, nextTick, onBeforeMount, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useComCash } from '@/store/pinia/comCash'
import type { CashBook, CompanyBank, SepItems } from '@/store/types/comCash'
import type { Project } from '@/store/types/project'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_company_cash } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { getToday, diffDate, cutString, numFormat } from '@/utils/baseMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import AccDepth from './AccDepth.vue'
import BankAcc from './BankAcc.vue'

const props = defineProps({
  cash: { type: Object as PropType<CashBook>, default: null },
  projects: { type: Array as PropType<Project[]>, default: () => [] },
})

const emit = defineEmits([
  'multi-submit',
  'on-delete',
  'close',
  'patch-d3-hide',
  'on-bank-create',
  'on-bank-update',
])

const refDelModal = ref()
const refAlertModal = ref()
const refAccDepth = ref()
const refBankAcc = ref()

const showProjects = ref(false)
const showSepProjects = ref(false)

const sepItem = reactive<SepItems>({
  pk: null,
  account_d1: null,
  account_d2: null,
  account_d3: null,
  project: null,
  is_return: false,
  content: '',
  trader: '',
  income: null,
  outlay: null,
  evidence: '',
  note: '',
})

const validated = ref(false)

const form = reactive<CashBook & { bank_account_to: null | number; charge: null | number }>({
  pk: null,
  company: null,
  sort: null,
  account_d1: null,
  account_d2: null,
  account_d3: null,
  project: null,
  is_return: false,

  is_separate: false,
  separated: null as null | number,

  content: '',
  trader: '',
  bank_account: null,
  bank_account_to: null,
  income: null,
  outlay: null,
  charge: null,
  evidence: '',
  note: '',
  deal_date: getToday(),
})

const formsCheck = computed(() => {
  if (props.cash) {
    const a = form.company === props.cash.company
    const b = form.sort === props.cash.sort
    const c = form.account_d1 === props.cash.account_d1
    const d = form.account_d2 === props.cash.account_d2
    const e = form.account_d3 === props.cash.account_d3
    const f = form.project === props.cash.project
    const g = form.is_return === props.cash.is_return
    const h = form.content === props.cash.content
    const i = form.trader === props.cash.trader
    const j = form.bank_account === props.cash.bank_account
    const k = form.income === props.cash.income
    const l = form.outlay === props.cash.outlay
    const m = form.evidence === props.cash.evidence
    const n = form.note === props.cash.note
    const o = form.deal_date === props.cash.deal_date

    return a && b && c && d && e && f && g && h && i && j && k && l && m && n && o
  } else return false
})

const comCashStore = useComCash()
const formAccD1List = computed(() => comCashStore.formAccD1List)
const formAccD2List = computed(() => comCashStore.formAccD2List)
const formAccD3List = computed(() => comCashStore.formAccD3List)
const allComBankList = computed(() => comCashStore.allComBankList)
const getComBanks = computed(() => comCashStore.getComBanks)

const comBankAccs = computed(() => {
  const ba = props.cash ? props.cash.bank_account : 0
  const isExist = !!getComBanks.value.filter(b => b.value === ba).length

  return !ba || isExist
    ? getComBanks.value
    : [...getComBanks.value, ...[{ value: ba, label: getAccName(ba) }]].sort(
        (a, b) => (a.value || 0) - (b.value || 0),
      )
})

const getAccName = (pk: number) =>
  allComBankList.value.filter(b => b.pk === pk).map(b => b.alias_name)[0]

const fetchFormAccD1List = (sort: number | null) => comCashStore.fetchFormAccD1List(sort)
const fetchFormAccD2List = (sort: number | null, d1: number | null) =>
  comCashStore.fetchFormAccD2List(sort, d1)
const fetchFormAccD3List = (sort: number | null, d1: number | null, d2: number | null) =>
  comCashStore.fetchFormAccD3List(sort, d1, d2)

const requireItem = computed(() => !!form.account_d1 && !!form.account_d2 && !!form.account_d3)

const sepDisabled = computed(() => {
  const disabled = !!form.account_d1 || !!form.account_d2 || !!form.account_d3
  return props.cash?.sepItems ? disabled && (props.cash.sepItems?.length ?? 0) === 0 : disabled
})

const sepSummary = computed(() => {
  if (!props.cash?.sepItems?.length) return [0, 0]

  const inc = props.cash.sepItems
    .map((s: SepItems) => s.income)
    .reduce((prev, curr) => (prev || 0) + (curr || 0))
  const out = props.cash.sepItems
    .map((s: SepItems) => s.outlay)
    .reduce((prev, curr) => (prev || 0) + (curr || 0))
  return [inc, out]
})

// 부모 거래와 자식 거래 합계 일치 여부 검증
const isBalanceMatched = computed(() => {
  if (!props.cash?.is_separate || !props.cash?.sepItems?.length) return true

  const parentIncome = props.cash.income || 0
  const parentOutlay = props.cash.outlay || 0
  const [childrenIncome, childrenOutlay] = sepSummary.value

  return parentIncome === childrenIncome && parentOutlay === childrenOutlay
})

const sepUpdate = (sep: SepItems) => {
  sepItem.pk = sep.pk
  sepItem.account_d1 = sep.account_d1
  sepItem.account_d2 = sep.account_d2
  sepItem.account_d3 = sep.account_d3
  sepItem.project = sep.project
  sepItem.is_return = sep.is_return ?? false // null/undefined면 false로 설정
  sepItem.content = sep.content
  sepItem.trader = sep.trader
  sepItem.evidence = sep.evidence
  sepItem.outlay = sep.outlay
  sepItem.income = sep.income
  sepItem.note = sep.note
}

const sepRemove = () => {
  sepItem.pk = null
  sepItem.account_d1 = null
  sepItem.account_d2 = null
  sepItem.account_d3 = null
  sepItem.project = null
  sepItem.is_return = false
  sepItem.content = ''
  sepItem.trader = ''
  sepItem.evidence = ''
  sepItem.outlay = null
  sepItem.income = null
  sepItem.note = ''
}

const isModify = computed(() => {
  if (!form.is_separate) return !!props.cash
  else return !!sepItem.pk
})

const callAccount = () => {
  nextTick(() => {
    const sort = form.sort === 1 || form.sort === 2 ? form.sort : null
    const d1 = form.account_d1 || null
    const d2 = form.account_d2 || null
    fetchFormAccD1List(sort)
    fetchFormAccD2List(sort, d1)
    fetchFormAccD3List(sort, d1, d2)
  })
}

const sort_change = (event: Event) => {
  const el = event.target as HTMLSelectElement

  if (!form.is_separate) {
    if (el.value === '1') {
      form.account_d1 = 4
      form.account_d2 = null
      form.account_d3 = null
      form.project = null
      form.outlay = null
    } else if (el.value === '2') {
      form.account_d1 = 5
      form.account_d2 = null
      form.account_d3 = null
      form.project = null
      form.income = null
    } else if (el.value === '3') {
      form.account_d1 = 6
      form.account_d2 = 19
      form.account_d3 = 131
      form.project = null
    } else if (el.value === '4') {
      form.account_d1 = 7
      form.account_d2 = 20
      form.account_d3 = 133
      form.project = null
    } else {
      form.account_d1 = null
      form.account_d2 = null
      form.account_d3 = null
      form.project = null
    }
    callAccount()
  } else {
    if (el.value === '1') {
      sepItem.account_d1 = 4
      sepItem.account_d2 = null
      sepItem.account_d3 = null
      form.project = null
      sepItem.outlay = null
      fetchFormAccD2List(1, 4)
    } else if (el.value === '2') {
      form.evidence = '0'
      sepItem.account_d1 = 5
      sepItem.account_d2 = null
      sepItem.account_d3 = null
      form.project = null
      sepItem.income = null
      fetchFormAccD2List(2, 5)
    } else {
      sepItem.account_d1 = null
      sepItem.account_d2 = null
      sepItem.account_d3 = null
      form.project = null
      callAccount()
    }
  }
}

const d1_change = () => {
  form.account_d2 = null
  form.account_d3 = null
  callAccount()
}

const sepD1_change = () => {
  sepItem.account_d2 = null
  sepItem.account_d3 = null
  nextTick(() => {
    const sort = form.sort
    const d1 = sepItem.account_d1
    fetchFormAccD1List(sort)
    fetchFormAccD2List(sort, d1)
  })
}

const d2_change = () => {
  form.account_d3 = null
  callAccount()
}

const sepD2_change = () => {
  sepItem.account_d3 = null
  nextTick(() => {
    const sort = form.sort
    const d1 = sepItem.account_d1
    const d2 = sepItem.account_d2
    fetchFormAccD3List(sort, d1, d2)
  })
}

const d3_change = (event: Event) => {
  const el = event.target as HTMLSelectElement
  showProjects.value = el.value === '6'
}

const sepD3_change = (event: Event) => {
  const el = event.target as HTMLSelectElement
  showSepProjects.value = el.value === '6'
}

const accountStore = useAccount()
const allowedPeriod = computed(
  () => accountStore.superAuth || (props.cash?.deal_date && diffDate(props.cash.deal_date) <= 30),
)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    // 자식 레코드(separated가 있는 경우)는 sepData를 전송하지 않음
    const isChildRecord = props.cash?.separated
    const payload =
      !form.is_separate || isChildRecord
        ? { formData: form, sepData: null }
        : { formData: form, sepData: sepItem }

    if (write_company_cash.value) {
      if (props.cash) {
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
  }
}

const deleteConfirm = () => {
  if (write_company_cash.value)
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
    company: props.cash?.company,
    pk: props.cash?.pk,
  })
  refDelModal.value.close()
  emit('close')
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

const dataSetup = () => {
  if (props.cash) {
    form.pk = props.cash.pk
    form.company = props.cash.company
    form.sort = props.cash.sort
    form.account_d1 = props.cash.account_d1
    form.account_d2 = props.cash.account_d2
    form.account_d3 = props.cash.account_d3
    form.project = props.cash.project
    form.is_return = props.cash.is_return
    form.is_separate = props.cash.is_separate
    form.separated = props.cash.separated
    form.content = props.cash.content
    form.trader = props.cash.trader
    form.bank_account = props.cash.bank_account
    form.income = props.cash.income
    form.outlay = props.cash.outlay
    form.evidence = props.cash.evidence
    form.note = props.cash.note
    form.deal_date = props.cash.deal_date
  }
  callAccount()
}

onBeforeMount(async () => {
  await dataSetup()
  if (form.account_d3 === 6) showProjects.value = true
})
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
                  maxlength="10"
                  required
                  placeholder="거래일자"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">구분</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.sort"
                  required
                  :disabled="cash && !!cash.sort"
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
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                계정[대분류]
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.account_d1"
                  :required="!form.is_separate"
                  :disabled="!form.sort || form.is_separate || form.sort === 3 || form.sort === 4"
                  @change="d1_change"
                >
                  <option value="">---------</option>
                  <option v-for="d1 in formAccD1List" :key="d1.pk" :value="d1.pk">
                    {{ d1.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                계정[중분류]
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.account_d2"
                  :required="!form.is_separate"
                  :disabled="!form.account_d1 || form.is_separate"
                  @change="d2_change"
                >
                  <option value="">---------</option>
                  <option v-for="d2 in formAccD2List" :key="d2.pk" :value="d2.pk">
                    {{ d2.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                계정[소분류]
                <a href="javascript:void(0)">
                  <CIcon name="cilCog" @click="refAccDepth.callModal()" />
                </a>
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.account_d3"
                  :required="!form.is_separate"
                  :disabled="!form.account_d2 || form.is_separate"
                  @change="d3_change"
                >
                  <option value="">---------</option>
                  <option v-for="d3 in formAccD3List" :key="d3.pk" :value="d3.pk">
                    {{ d3.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3" v-show="showProjects">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 투입 프로젝트</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model.number="form.project"
                  :disabled="!form.account_d2 || form.is_separate"
                >
                  <option value="">---------</option>
                  <option v-for="proj in projects" :key="proj.pk" :value="proj.pk">
                    {{ proj.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow v-show="cash && cash.project">
              <CFormLabel class="col-sm-4 col-form-label"> 반환 정산 여부</CFormLabel>
              <CCol sm="8" class="pt-2">
                <CFormSwitch
                  v-model="form.is_return"
                  label="프로젝트 대여금 반환 정산 여부"
                  id="form-is-return"
                />
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
                  required
                  :disabled="!form.sort"
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
                  maxlength="25"
                  placeholder="거래처"
                  :disabled="!form.sort"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">
                {{ !cash && form.sort === 3 ? '출금' : '거래' }}계좌
                <a href="javascript:void(0)">
                  <CIcon name="cilCog" @click="refBankAcc.callModal()" />
                </a>
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model.number="form.bank_account" required :disabled="!form.sort">
                  <option value="">---------</option>
                  <option v-for="ba in comBankAccs" :key="ba.value" :value="ba.value">
                    {{ ba.label }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow v-if="form.sort === 2">
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: !form.is_separate }">
                지출증빙
              </CFormLabel>
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

            <CRow v-if="!cash && form.sort === 3">
              <CFormLabel class="col-sm-4 col-form-label required">입금계좌</CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model="form.bank_account_to" required :disabled="form.sort !== 3">
                  <option value="">---------</option>
                  <option v-for="ba in comBankAccs" :key="ba.value" :value="ba.value">
                    {{ ba.label }}
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
                  :disabled="form.sort === 1 || !form.sort || (cash && !cash.outlay)"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow v-if="form.sort === 1 || cash">
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
                  :disabled="form.sort === 2 || !form.sort || (cash && !cash.income)"
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
                <CFormTextarea
                  v-model.number="form.note"
                  placeholder="특이사항"
                  :disabled="!form.sort"
                />
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
        <hr v-if="cash?.sepItems && cash.sepItems.length" />
        <CRow v-if="cash?.sepItems && cash.sepItems.length" class="mb-3">
          <CCol>
            <strong>
              <CIcon name="cilDescription" class="mr-2" />
              {{ sepSummary[0] ? `입금액 합계 : ${numFormat(sepSummary[0] || 0)}` : '' }}
              {{ sepSummary[1] ? `출금액 합계 : ${numFormat(sepSummary[1] || 0)}` : '' }}
            </strong>

            <!-- 부모 거래와 자식 거래 합계 일치 여부 표시 -->
            <v-alert
              v-if="!isBalanceMatched"
              type="warning"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              <template #prepend>
                <v-icon icon="mdi-alert-circle" />
              </template>
              <div class="d-flex flex-column">
                <strong>부모 거래와 자식 거래 합계가 일치하지 않습니다!</strong>
                <div class="mt-1">
                  <span class="text-caption">
                    부모 입금: {{ numFormat(cash?.income || 0) }} /
                    자식 합계: {{ numFormat(sepSummary[0] || 0) }}
                    <span v-if="(cash?.income || 0) !== (sepSummary[0] || 0)" class="text-error ml-1">
                      (차액: {{ numFormat(Math.abs((cash?.income ?? 0) - (sepSummary[0] || 0))) }})
                    </span>
                  </span>
                </div>
                <div>
                  <span class="text-caption">
                    부모 출금: {{ numFormat(cash?.outlay || 0) }} /
                    자식 합계: {{ numFormat(sepSummary[1] || 0) }}
                    <span v-if="(cash?.outlay || 0) !== (sepSummary[1] || 0)" class="text-error ml-1">
                      (차액: {{ numFormat(Math.abs((cash?.outlay ?? 0) - (sepSummary[1] || 0))) }})
                    </span>
                  </span>
                </div>
              </div>
            </v-alert>

            <!-- 일치하는 경우 성공 표시 -->
            <v-alert
              v-else
              type="success"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              <template #prepend>
                <v-icon icon="mdi-check-circle" />
              </template>
              <strong>부모 거래와 자식 거래 합계가 일치합니다.</strong>
            </v-alert>
          </CCol>
        </CRow>

        <div v-if="cash">
          <CRow
            v-for="(sep, i) in cash.sepItems"
            :key="sep.pk"
            class="mb-1"
            :class="sep.pk === sepItem.pk ? 'text-success text-decoration-underline' : ''"
          >
            <CCol sm="1">{{ i + 1 }}</CCol>
            <CCol sm="2">{{ sep.trader }}</CCol>
            <CCol sm="5">{{ cutString(sep.content, 20) }}</CCol>
            <CCol sm="2" class="text-right">
              {{ sep.income ? numFormat(sep.income) : numFormat(sep.outlay || 0) }}
            </CCol>
            <CCol sm="2" class="text-right">
              <v-btn type="button" color="success" size="small" @click="sepUpdate(sep)">
                수정
              </v-btn>
            </CCol>
          </CRow>
        </div>

        <v-divider />

        <CRow class="mb-3">
          <CCol sm="1" />
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required">구분</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="form.sort" disabled>
                      <option value="">---------</option>
                      <option value="1">입금</option>
                      <option value="2">출금</option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>

              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 계정[대분류]</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.account_d1"
                      required
                      :disabled="!form.sort"
                      @change="sepD1_change"
                    >
                      <option value="">---------</option>
                      <option v-for="d1 in formAccD1List" :key="d1.pk" :value="d1.pk">
                        {{ d1.name }}
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
                  <CFormLabel class="col-sm-4 col-form-label required"> 계정[중분류]</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.account_d2"
                      required
                      :disabled="!sepItem.account_d1"
                      @change="sepD2_change"
                    >
                      <option value="">---------</option>
                      <option v-for="d2 in formAccD2List" :key="d2.pk" :value="d2.pk">
                        {{ d2.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label required"> 계정[소분류]</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect
                      v-model.number="sepItem.account_d3"
                      :disabled="!sepItem.account_d2"
                      @change="sepD3_change"
                      required
                    >
                      <option value="">---------</option>
                      <option v-for="d3 in formAccD3List" :key="d3.pk" :value="d3.pk">
                        {{ d3.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3" v-show="showSepProjects">
          <CCol sm="1"></CCol>
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label"> 투입 프로젝트</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="sepItem.project" :disabled="!sepItem.account_d2">
                      <option value="">---------</option>
                      <option v-for="proj in projects" :key="proj.pk" :value="proj.pk">
                        {{ proj.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>
              </CCol>

              <CCol sm="6">
                <CRow v-show="sepItem.project">
                  <CFormLabel class="col-sm-4 col-form-label"> 반환 정산 여부</CFormLabel>
                  <CCol sm="8" class="pt-2">
                    <CFormSwitch
                      v-model="sepItem.is_return"
                      label="프로젝트 대여금 반환 정산 여부"
                      id="sepItem-is-return"
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
                      maxlength="25"
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
          <CCol sm="1" />
          <CCol sm="11">
            <CRow>
              <CCol sm="6">
                <CRow>
                  <CFormLabel class="col-sm-4 col-form-label"> 거래계좌</CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="form.bank_account" disabled>
                      <option value="">---------</option>
                      <option v-for="ba in comBankAccs" :key="ba.value" :value="ba.value">
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
          <CCol sm="1" />
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
      <v-btn type="button" :color="btnLight" size="small" @click="emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          v-if="sepItem.pk"
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
        <v-btn v-if="isModify" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 프로젝트 입출금 거래 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />

  <AccDepth ref="refAccDepth" @patch-d3-hide="patchD3Hide" />

  <BankAcc ref="refBankAcc" @on-bank-create="onBankCreate" @on-bank-update="onBankUpdate" />
</template>
