<script lang="ts" setup>
import { computed, type PropType, reactive, ref, watch } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { usePerms } from '@/composables/usePerms'
import type { CompanyBank } from '@/store/types/comLedger'
import { isValidate } from '@/utils/helper'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  bankAcc: { type: Object as PropType<CompanyBank | null>, default: null },
})

const emit = defineEmits(['created'])

const refAlertModal = ref()
const refConfirmModal = ref()

const { canGlobal, PERM } = usePerms()
const canComLedgerManage = computed(() => canGlobal(PERM.HQ_LEDGER_MANAGE))

const validated = ref(false)
const submitting = ref(false)

const comStore = useCompany()
const company = computed(() => (comStore.company as { pk?: number } | null)?.pk)
const getPkDeparts = computed(() => comStore.getPkDeparts)

const form = reactive<CompanyBank>({
  pk: undefined,
  company: undefined,
  depart: null,
  bankcode: null,
  alias_name: '',
  number: '',
  holder: '',
  open_date: null,
  note: '',
  is_hide: false,
  inactive: false,
})

const formsCheck = computed(() => {
  if (props.bankAcc) {
    const a = (form.depart || null) === (props.bankAcc.depart ?? null)
    const b = (form.bankcode || null) === (props.bankAcc.bankcode ?? null)
    const c = form.alias_name === props.bankAcc.alias_name
    const d = form.number === props.bankAcc.number
    const e = form.holder === props.bankAcc.holder
    const f = (form.open_date || null) === (props.bankAcc.open_date ?? null)
    const g = form.note === props.bankAcc.note
    const h = form.is_hide === props.bankAcc.is_hide
    const i = form.inactive === props.bankAcc.inactive

    return a && b && c && d && e && f && g && h && i
  } else return false
})

const ledgerStore = useComLedger()
const bankCodeList = computed(() => ledgerStore.bankCodeList)
const createComBankAcc = (payload: CompanyBank) => ledgerStore.createComBankAcc(payload)
const updateComBankAcc = (payload: CompanyBank) => ledgerStore.updateComBankAcc(payload)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const targetCompany = form.company ?? company.value
    if (!props.bankAcc && !targetCompany) {
      refAlertModal.value?.callModal('오류', '회사 정보가 선택되지 않았습니다.')
      validated.value = false
      return
    }
    if (canComLedgerManage.value) {
      refConfirmModal.value?.callModal()
    } else refAlertModal.value?.callModal()
    validated.value = false
  }
}

const dataReset = () => {
  form.pk = undefined
  form.company = company.value
  form.depart = null
  form.bankcode = null
  form.alias_name = ''
  form.number = ''
  form.holder = ''
  form.open_date = null
  form.note = ''
  form.is_hide = false
  form.inactive = false
  validated.value = false
}

const dataSetup = () => {
  if (props.bankAcc) {
    form.pk = props.bankAcc.pk
    form.company = props.bankAcc.company
    form.depart = props.bankAcc.depart ?? null
    form.bankcode = props.bankAcc.bankcode ?? null
    form.alias_name = props.bankAcc.alias_name
    form.number = props.bankAcc.number
    form.holder = props.bankAcc.holder
    form.open_date = props.bankAcc.open_date ?? null
    form.note = props.bankAcc.note
    form.is_hide = props.bankAcc.is_hide
    form.inactive = props.bankAcc.inactive
    validated.value = false
  } else {
    dataReset()
  }
}

const onBankAccSubmit = async () => {
  if (submitting.value) return
  const targetCompany = form.company ?? company.value
  if (!targetCompany) {
    refConfirmModal.value?.close()
    refAlertModal.value?.callModal('오류', '회사 정보가 선택되지 않았습니다.')
    return
  }

  submitting.value = true
  try {
    const payload: CompanyBank = {
      ...form,
      company: targetCompany,
      depart: form.depart || null,
      bankcode: form.bankcode || null,
      open_date: form.open_date || null,
    }
    if (props.bankAcc) {
      await updateComBankAcc(payload)
    } else {
      await createComBankAcc(payload)
      dataReset()
      emit('created')
    }
    refConfirmModal.value?.close()
  } catch {
    refConfirmModal.value?.close()
  } finally {
    submitting.value = false
  }
}

watch(() => props.bankAcc, dataSetup, { immediate: true })
watch(company, val => {
  if (!props.bankAcc) form.company = val
})
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">거래은행</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  :model-value="form.bankcode ? String(form.bankcode) : ''"
                  required
                  @update:model-value="val => (form.bankcode = val ? Number(val) : null)"
                >
                  <option value="">---------</option>
                  <option v-for="bank in bankCodeList" :key="bank.pk" :value="bank.pk">
                    {{ bank.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">관리부서</CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  :model-value="form.depart ? String(form.depart) : ''"
                  @update:model-value="val => (form.depart = val ? Number(val) : null)"
                >
                  <option value="">---------</option>
                  <option v-for="dep in getPkDeparts" :key="dep.value" :value="dep.value">
                    {{ dep.label }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계좌별칭</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.alias_name"
                  maxlength="20"
                  placeholder="계좌별칭"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계좌번호</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.number" maxlength="30" placeholder="계좌번호" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 예금주</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.holder" maxlength="20" placeholder="예금주" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">개설일자</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.open_date" maxlength="10" placeholder="개설일자" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.note" maxlength="50" placeholder="비고" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.is_hide"
                  label="입출금 등록시 숨김"
                  color="indigo"
                  hide-details
                />
                <v-tooltip activator="parent" location="end">
                  입출금 등록 시 이 계좌 항목을 숨김.
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.inactive"
                  label="사용종료 계좌"
                  color="danger"
                  hide-details
                />
                <v-tooltip activator="parent" location="start">
                  해지된 계좌로 내역만 확인 가능.
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="12" class="text-end pt-1">
            <v-btn :color="bankAcc ? 'success' : 'primary'" type="submit" :disabled="formsCheck">
              거래계좌 정보 <span v-if="bankAcc">저장</span><span v-else>추가</span>하기
            </v-btn>
          </CCol>
        </CRow>
      </div>
    </CModalBody>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header>
      거래계좌 정보 <span v-if="bankAcc">저장</span><span v-else>추가</span>
    </template>
    <template #default>
      거래계좌 정보를 <span v-if="bankAcc">저장</span><span v-else>추가</span>하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        size="small"
        :color="bankAcc ? 'success' : 'primary'"
        :disabled="submitting"
        @click="onBankAccSubmit"
      >
        저장
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
