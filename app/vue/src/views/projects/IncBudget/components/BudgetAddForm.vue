<script lang="ts" setup>
import { ref, reactive, inject, computed } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms.ts'
import type { ProIncBudget } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

export interface AccItem {
  value: number
  label: string
}

export interface OGroup {
  value: number
  label: string
  sort: '1' | '2'
}

export interface UType {
  value: number
  label: string
}

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const accountList = inject<AccItem[]>('accountList')
const orderGroups = inject<OGroup[]>('orderGroups')
const unitTypes = inject<UType[]>('unitTypes')

defineProps({ disabled: Boolean })
const emit = defineEmits<{
  (e: 'on-submit', payload: Omit<ProIncBudget, 'pk' | 'project'>): void
}>()

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive<{
  account: number | ''
  order_group: number | ''
  unit_type: number | ''
  item_name: string
  average_price: number | '' | null
  quantity: number | '' | null
  budget: number | '' | null
  revised_budget: number | '' | null
}>({
  account: '',
  order_group: '',
  unit_type: '',
  item_name: '',
  average_price: null,
  quantity: null,
  budget: null,
  revised_budget: null,
})

const toNullableNumber = (val: number | '' | null) =>
  val !== null && val !== '' ? Number(val) : null

// 폼 유효성 검사:
// 1) 계정(account) 필수
// 2) unit_type 없으면 item_name 필수
// 3) quantity 필수 (0 초과)
// 4) budget 필수 (0 이상)
const isFormValid = computed(
  () =>
    Boolean(form.account) &&
    (Boolean(form.unit_type) || Boolean(form.item_name.trim())) &&
    form.quantity !== null &&
    form.quantity !== '' &&
    Number(form.quantity) > 0 &&
    form.budget !== null &&
    form.budget !== '' &&
    Number(form.budget) >= 0,
)

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
    if (isValidate(event)) {
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
    account: Number(form.account),
    order_group: form.order_group ? Number(form.order_group) : null,
    unit_type: form.unit_type ? Number(form.unit_type) : null,
    item_name: form.item_name.trim(),
    average_price: toNullableNumber(form.average_price),
    quantity: Number(form.quantity),
    budget: Number(form.budget),
    revised_budget: toNullableNumber(form.revised_budget),
  })
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.account = ''
  form.order_group = ''
  form.unit_type = ''
  form.item_name = ''
  form.average_price = null
  form.quantity = null
  form.budget = null
  form.revised_budget = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2" color="success">
      <CCol lg="12" xl="5">
        <CRow>
          <CCol md="3" class="mb-2">
            <CFormSelect v-model="form.account" required :disabled="disabled">
              <option value="">계정과목</option>
              <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
                {{ acc.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="3" class="mb-2">
            <CFormSelect v-model="form.order_group" :disabled="disabled">
              <option value="">차수</option>
              <option v-for="og in orderGroups" :key="og.value" :value="og.value">
                {{ og.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="3" class="mb-2">
            <CFormSelect v-model="form.unit_type" :disabled="disabled">
              <option value="">타입</option>
              <option v-for="ut in unitTypes" :key="ut.value" :value="ut.value">
                {{ ut.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="3" class="mb-2">
            <CFormInput
              v-model="form.item_name"
              placeholder="항목명칭"
              maxlength="20"
              :disabled="disabled"
              :required="!form.unit_type"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="5">
        <CRow>
          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.average_price"
              min="0"
              placeholder="평균가격"
              type="number"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>
          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.quantity"
              min="0"
              placeholder="수량"
              type="number"
              maxlength="9"
              required
              :disabled="disabled"
            />
          </CCol>
          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.budget"
              min="0"
              placeholder="기초 수입 예산"
              type="number"
              maxlength="18"
              required
              :disabled="disabled"
            />
          </CCol>
          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.revised_budget"
              min="0"
              placeholder="현황 수입 예산"
              type="number"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="2">
        <CRow>
          <CCol md="12" class="d-grid gap-2 d-md-block text-end mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid">
              수입 예산 추가
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 수입 예산 등록</template>
    <template #default> 프로젝트의 수입 예산 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
