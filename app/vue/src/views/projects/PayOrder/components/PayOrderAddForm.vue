<script lang="ts" setup>
import { ref, reactive, computed, watch } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import type { PayOrder } from '@/store/types/payment'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ disabled: Boolean })

const emit = defineEmits<{
  (e: 'on-submit', payload: Omit<PayOrder, 'pk' | 'project'>): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive<{
  type_sort: '1' | '2' | '3' | '4' | '5' | '6'
  pay_sort: '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | ''
  calculation_method: 'auto' | 'ratio' | 'downpayment'
  is_except_price: boolean
  pay_code: number | '' | null
  pay_time: number | '' | null
  pay_name: string
  alias_name: string
  pay_amt: number | '' | null
  pay_ratio: number | '' | null
  pay_due_date: string | null
  days_since_prev: number | '' | null
  is_prep_discount: boolean
  prep_discount_ratio: number | '' | null
  prep_ref_date: string | null
  is_late_penalty: boolean
  late_penalty_ratio: number | '' | null
  extra_due_date: string | null
}>({
  type_sort: '1',
  pay_sort: '',
  calculation_method: 'auto',
  is_except_price: false,
  pay_code: null,
  pay_time: null,
  pay_name: '',
  alias_name: '',
  pay_amt: null,
  pay_ratio: null,
  pay_due_date: null,
  days_since_prev: null,
  is_prep_discount: false,
  prep_discount_ratio: null,
  prep_ref_date: null,
  is_late_penalty: false,
  late_penalty_ratio: null,
  extra_due_date: null,
})

const toNullableNumber = (val: number | '' | null) =>
  val !== null && val !== '' ? Number(val) : null

watch(
  () => props.disabled,
  newVal => {
    if (newVal) resetForm()
  },
)

const onPaySortChange = () => {
  if (form.pay_sort !== '1') {
    form.calculation_method = 'auto'
  }
  if (form.pay_sort === '2' || form.pay_sort === '3') {
    form.pay_amt = null
  }
  if (form.pay_sort === '3') {
    form.pay_ratio = null
  }
}

const isFormValid = computed(() => {
  const hasType = Boolean(form.type_sort)
  const hasSort = Boolean(form.pay_sort)
  const hasCode = typeof form.pay_code === 'number' && form.pay_code >= 0
  const hasTime = typeof form.pay_time === 'number' && form.pay_time >= 0
  const hasName = Boolean(form.pay_name.trim())

  const prepValid =
    !form.is_prep_discount || (form.prep_discount_ratio !== null && form.prep_discount_ratio !== '')
  const lateValid =
    !form.is_late_penalty || (form.late_penalty_ratio !== null && form.late_penalty_ratio !== '')

  return hasType && hasSort && hasCode && hasTime && hasName && prepValid && lateValid
})

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
    if (isValidate(event) || !isFormValid.value) {
      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else {
    refAlertModal.value.callModal()
    resetForm()
  }
}

const modalAction = () => {
  emit('on-submit', {
    type_sort: form.type_sort,
    pay_sort: form.pay_sort,
    calculation_method: form.calculation_method,
    is_except_price: form.is_except_price,
    pay_code: toNullableNumber(form.pay_code),
    pay_time: toNullableNumber(form.pay_time),
    pay_name: form.pay_name.trim(),
    alias_name: form.alias_name.trim(),
    pay_amt: toNullableNumber(form.pay_amt),
    pay_ratio: toNullableNumber(form.pay_ratio),
    pay_due_date: form.pay_due_date || null,
    days_since_prev: toNullableNumber(form.days_since_prev),
    is_prep_discount: form.is_prep_discount,
    prep_discount_ratio: form.is_prep_discount ? toNullableNumber(form.prep_discount_ratio) : null,
    prep_ref_date: form.is_prep_discount ? form.prep_ref_date || null : null,
    is_late_penalty: form.is_late_penalty,
    late_penalty_ratio: form.is_late_penalty ? toNullableNumber(form.late_penalty_ratio) : null,
    extra_due_date: form.is_late_penalty ? form.extra_due_date || null : null,
  })
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.type_sort = '1'
  form.pay_sort = ''
  form.calculation_method = 'auto'
  form.is_except_price = false
  form.pay_code = null
  form.pay_time = null
  form.pay_name = ''
  form.alias_name = ''
  form.pay_amt = null
  form.pay_ratio = null
  form.pay_due_date = null
  form.days_since_prev = null
  form.is_prep_discount = false
  form.prep_discount_ratio = null
  form.prep_ref_date = null
  form.is_late_penalty = false
  form.late_penalty_ratio = null
  form.extra_due_date = null
  validated.value = false
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow>
      <CCol xl="7">
        <CRow>
          <CCol lg="2" md="6" class="mb-3">
            <CFormSelect v-model="form.type_sort" :disabled="disabled" required>
              <option value="">타입 종류</option>
              <option value="1">공동주택</option>
              <option value="2">오피스텔</option>
              <option value="3">숙박시설</option>
              <option value="4">지식산업센터</option>
              <option value="5">근린생활시설</option>
              <option value="6">기타</option>
            </CFormSelect>
          </CCol>
          <CCol lg="2" md="6" class="mb-3">
            <CFormSelect
              v-model="form.pay_sort"
              :disabled="disabled"
              required
              @change="onPaySortChange"
            >
              <option value="">회차 종류</option>
              <option value="1">계약금</option>
              <option value="2">중도금</option>
              <option value="3">잔금</option>
              <option value="4">계약금 정산</option>
              <option value="5">미납 연체료</option>
              <option value="6">기타 부담금</option>
              <option value="7">제세 공과금</option>
              <option value="8">후불 이자</option>
              <option value="9">업무 대행비</option>
            </CFormSelect>
          </CCol>
          <CCol lg="2" md="6" class="mb-3">
            <CFormSelect v-model="form.calculation_method" :disabled="form.pay_sort !== '1'">
              <option value="auto">---------</option>
              <option value="downpayment">등록 계약 금액 우선</option>
              <option value="ratio">분양가격 × 납부비율</option>
            </CFormSelect>
          </CCol>

          <CCol lg="2" md="6" class="pt-2 col-form-label mb-3">
            <CFormSwitch
              v-model="form.is_except_price"
              id="add_iep"
              label="공급가 불포함"
              :disabled="disabled"
            />
          </CCol>
          <CCol lg="2" md="6" class="mb-3">
            <CFormInput
              v-model.number="form.pay_code"
              placeholder="납입회차 코드"
              type="number"
              min="0"
              required
              :disabled="disabled"
            />
            <v-tooltip activator="parent" location="start">
              프로젝트 내 납부회차별 코드번호 - 동일 회차 중복(분리) 등록 가능
            </v-tooltip>
          </CCol>
          <CCol lg="2" md="6" class="mb-3">
            <CFormInput
              v-model.number="form.pay_time"
              placeholder="납부순서"
              type="number"
              min="0"
              required
              :disabled="disabled"
            />
            <v-tooltip activator="parent" location="start">
              동일 납부회차에 2가지 항목을 별도로 납부하여야 하는 경우(ex: 분담금 + 업무대행료)
              하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.
            </v-tooltip>
          </CCol>
        </CRow>
      </CCol>

      <CCol xl="5">
        <CRow>
          <CCol lg="3" md="6" class="mb-3">
            <CFormInput
              v-model="form.pay_name"
              maxlength="20"
              placeholder="납부회차 명"
              required
              :disabled="disabled"
            />
          </CCol>
          <CCol lg="3" md="6" class="mb-3">
            <CFormInput
              v-model="form.alias_name"
              maxlength="20"
              placeholder="별칭 이름"
              :disabled="disabled"
            />
          </CCol>
          <CCol lg="3" md="6" class="mb-3">
            <CFormInput
              v-model.number="form.pay_amt"
              maxlength="20"
              type="number"
              min="0"
              placeholder="납부 약정금액"
              :disabled="disabled || form.pay_sort === '2' || form.pay_sort === '3'"
            />
            <v-tooltip activator="parent" location="start">
              약정금이 차수, 타입에 관계 없이 정액인 경우 설정(예: 세대별 업무대행비)
            </v-tooltip>
          </CCol>
          <CCol lg="3" md="6" class="mb-3">
            <CFormInput
              v-model.number="form.pay_ratio"
              maxlength="20"
              type="number"
              min="0"
              placeholder="납부비율(%, 공급가대비)"
              :disabled="disabled || form.pay_sort === '3'"
            />
            <v-tooltip activator="parent" location="start">
              분양가 대비 납부비율, 계약금 항목인 경우 "계약 금액 등록" 데이터 우선, 잔금 항목인
              경우 "공급 가격 등록" 데이터와 비교 차액 데이터 우선
            </v-tooltip>
          </CCol>
        </CRow>
      </CCol>

      <CCol xl="11">
        <CRow>
          <CCol xl="6">
            <CRow>
              <CCol lg="3" md="6" class="mb-3">
                <DatePicker
                  v-model="form.pay_due_date"
                  maxlength="10"
                  placeholder="납부 약정일"
                  :required="false"
                  :disabled="disabled"
                />
              </CCol>
              <CCol lg="3" md="6" class="mb-3">
                <CFormInput
                  v-model.number="form.days_since_prev"
                  type="number"
                  min="0"
                  maxlength="20"
                  placeholder="전회 기준 경과일수"
                  :disabled="disabled"
                />
                <v-tooltip activator="parent" location="start">
                  전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수
                </v-tooltip>
              </CCol>
              <CCol lg="3" md="6" class="mb-3">
                <CRow>
                  <CCol class="pt-2 col-form-label">
                    <CFormSwitch
                      v-model="form.is_prep_discount"
                      id="add_ipd"
                      label="선납할인 적용"
                      :disabled="disabled"
                    />
                  </CCol>
                </CRow>
              </CCol>
              <CCol lg="3" md="6" class="mb-3">
                <CFormInput
                  v-model.number="form.prep_discount_ratio"
                  maxlength="20"
                  type="number"
                  min="0"
                  placeholder="선납할인율(%, 연리)"
                  :disabled="disabled || !form.is_prep_discount"
                  :required="form.is_prep_discount"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol xl="6">
            <CRow>
              <CCol lg="3" md="6" class="mb-3">
                <DatePicker
                  v-model="form.prep_ref_date"
                  maxlength="10"
                  placeholder="선납 기준일"
                  :required="false"
                  :disabled="disabled || !form.is_prep_discount"
                />
                <v-tooltip activator="parent" location="start">
                  선납 할인 기준은 납부 약정일이 원칙이나 이 값이 있는 경우 선납 기준일로 우선
                  적용한다.
                </v-tooltip>
              </CCol>

              <CCol lg="3" md="6" class="mb-3">
                <CRow>
                  <CCol class="pt-2 col-form-label">
                    <CFormSwitch
                      v-model="form.is_late_penalty"
                      id="add_ilp"
                      label="연체가산 적용"
                      :disabled="disabled"
                    />
                  </CCol>
                </CRow>
              </CCol>
              <CCol lg="3" md="6" class="mb-3">
                <CFormInput
                  v-model.number="form.late_penalty_ratio"
                  maxlength="20"
                  type="number"
                  min="0"
                  placeholder="연체가산율(%, 연리)"
                  :disabled="disabled || !form.is_late_penalty"
                  :required="form.is_late_penalty"
                />
              </CCol>
              <CCol lg="3" md="6" class="mb-3">
                <DatePicker
                  v-model="form.extra_due_date"
                  maxlength="10"
                  placeholder="연체 기준일"
                  :required="false"
                  :disabled="disabled || !form.is_late_penalty"
                />
                <v-tooltip activator="parent" location="start">
                  연체료 계산 기준은 납부기한일이 원칙이나 이 값이 있는 경우 연체 기준일로 우선
                  적용한다.
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </CCol>

      <CCol xl="1" class="mb-3 text-end">
        <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid"> 회차추가</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 납부 회차 등록</template>
    <template #default> 프로젝트의 납부 회차 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
