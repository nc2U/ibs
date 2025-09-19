<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { write_project } from '@/utils/pageAuth'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ disabled: Boolean })

const emit = defineEmits(['on-submit'])

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  type_sort: '1',
  pay_sort: '',
  is_except_price: false,
  pay_code: null as string | null,
  pay_time: null as string | null,
  pay_name: '',
  alias_name: '',
  pay_amt: null,
  pay_ratio: null,
  pay_due_date: null as string | null,
  days_since_prev: null as number | null,
  is_prep_discount: false,
  prep_discount_ratio: null,
  prep_ref_date: null as string | null,
  is_late_penalty: false,
  late_penalty_ratio: null,
  extra_due_date: null as string | null,
})

const onSubmit = (event: Event) => {
  if (write_project.value) {
    const el = event.currentTarget as HTMLSelectElement
    if (!el.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

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
  emit('on-submit', form)
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.type_sort = '1'
  form.pay_sort = ''
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
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow>
      <CCol xl="12">
        <CRow>
          <CCol xl="11">
            <CRow>
              <CCol xl="6">
                <CRow>
                  <CCol lg="6" xl="3" class="mb-3">
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
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormSelect v-model="form.pay_sort" :disabled="disabled" required>
                      <option value="">회차 종류</option>
                      <option value="1">계약금</option>
                      <option value="2">중도금</option>
                      <option value="3">잔 금</option>
                      <option value="4">기타 부담금</option>
                      <option value="5">제세 공과금</option>
                      <option value="6">금융 비용</option>
                      <option value="7">업무 대행비</option>
                    </CFormSelect>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CRow>
                      <CCol class="pt-2 col-form-label">
                        <CFormSwitch
                          v-model="form.is_except_price"
                          id="is_prep_discount"
                          label="공급가 불포함"
                          :disabled="disabled"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
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
                </CRow>
              </CCol>
              <CCol xl="6">
                <CRow>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model.number="form.pay_time"
                      placeholder="납부순서"
                      type="number"
                      min="0"
                      required
                      :disabled="disabled"
                    />
                    <v-tooltip activator="parent" location="start">
                      동일 납부회차에 2가지 항목을 별도로 납부하여야 하는 경우(ex: 분담금 +
                      업무대행료) 하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.
                    </v-tooltip>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model="form.pay_name"
                      maxlength="20"
                      placeholder="납부회차 명"
                      required
                      :disabled="disabled"
                    />
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model="form.alias_name"
                      maxlength="20"
                      placeholder="별칭 이름"
                      :disabled="disabled"
                    />
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model="form.pay_amt"
                      maxlength="20"
                      type="number"
                      placeholder="납부 약정금액"
                      :disabled="disabled || form.pay_sort === '3'"
                    />
                    <v-tooltip activator="parent" location="start">
                      약정금이 차수, 타입에 관계 없이 정액인 경우 설정(예: 세대별 업무대행비)
                    </v-tooltip>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCol>
          <CCol class="mb-3">
            <!--            <CCol lg="6" xl="3" class="mb-3">-->
            <CFormInput
              v-model="form.pay_ratio"
              maxlength="20"
              type="number"
              placeholder="납부비율(%, 공급가대비)"
              :disabled="disabled || form.pay_sort === '3'"
            />
            <v-tooltip activator="parent" location="start">
              분양가 대비 납부비율, 계약금 항목인 경우 "계약 금액 등록" 데이터 우선, 잔금 항목인
              경우 "공급 가격 등록" 데이터와 비교 차액 데이터 우선
            </v-tooltip>
            <!--            </CCol>-->
          </CCol>
        </CRow>

        <CRow>
          <CCol xl="11">
            <CRow>
              <CCol xl="6">
                <CRow>
                  <CCol lg="6" xl="3" class="mb-3">
                    <DatePicker
                      v-model="form.pay_due_date"
                      maxlength="10"
                      placeholder="납부 약정일"
                      :required="false"
                      :disabled="disabled"
                    />
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model.number="form.days_since_prev"
                      type="number"
                      maxlength="20"
                      placeholder="전회 기준 경과일수"
                      :disabled="disabled"
                    />
                    <v-tooltip activator="parent" location="start">
                      전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수
                    </v-tooltip>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CRow>
                      <CCol class="pt-2 col-form-label">
                        <CFormSwitch
                          v-model="form.is_prep_discount"
                          id="is_prep_discount"
                          label="선납할인 적용"
                          :disabled="disabled"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model="form.prep_discount_ratio"
                      maxlength="20"
                      type="number"
                      placeholder="선납할인율(%, 연리)"
                      :disabled="disabled"
                    />
                  </CCol>
                </CRow>
              </CCol>
              <CCol xl="6">
                <CRow>
                  <CCol lg="6" xl="3" class="mb-3">
                    <DatePicker
                      v-model="form.prep_ref_date"
                      maxlength="10"
                      placeholder="선납 기준일"
                      :required="false"
                      :disabled="disabled"
                    />
                    <v-tooltip activator="parent" location="start">
                      선납 할인 기준은 납부 약정일이 원칙이나 이 값이 있는 경우 선납 기준일로 우선
                      적용한다.
                    </v-tooltip>
                  </CCol>

                  <CCol lg="6" xl="3" class="mb-3">
                    <CRow>
                      <CCol class="pt-2 col-form-label">
                        <CFormSwitch
                          v-model="form.is_late_penalty"
                          id="is_late_penalty"
                          label="연체가산 적용"
                          :disabled="disabled"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <CFormInput
                      v-model="form.late_penalty_ratio"
                      maxlength="20"
                      type="number"
                      placeholder="연체가산율(%, 연리)"
                      :disabled="disabled"
                    />
                  </CCol>
                  <CCol lg="6" xl="3" class="mb-3">
                    <DatePicker
                      v-model="form.extra_due_date"
                      maxlength="10"
                      placeholder="연체 기준일"
                      :required="false"
                      :disabled="disabled"
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

          <CCol xl="1" class="mb-3 text-right">
            <v-btn color="primary" type="submit" :disabled="disabled"> 회차추가</v-btn>
          </CCol>
        </CRow>
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
