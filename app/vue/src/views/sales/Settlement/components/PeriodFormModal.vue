<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SettlementPeriod } from '@/store/types/sales'
import { colorLight } from '@/utils/cssMixins'
import { getToday } from '@/utils/baseMixins'
import { isValidate, message } from '@/utils/helper'
import FormModal from '@/components/Modals/FormModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  project: { type: Number, required: true },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const isSubmitting = ref(false)
const targetId = ref<number | null>(null)
const validated = ref(false)
const currentStatusDisplay = ref('정산 작성 중')

const form = reactive({
  title: '',
  start_date: getToday(),
  end_date: getToday(),
  payout_date: '',
})

const resetForm = () => {
  const today = getToday()
  validated.value = false
  form.title = ''
  form.start_date = today
  form.end_date = today
  form.payout_date = ''
  currentStatusDisplay.value = '정산 작성 중'
  targetId.value = null
  isEdit.value = false
}

const open = (period?: SettlementPeriod) => {
  resetForm()
  if (period) {
    isEdit.value = true
    targetId.value = period.id
    form.title = period.title
    form.start_date = period.start_date
    form.end_date = period.end_date
    form.payout_date = period.payout_date || ''
    currentStatusDisplay.value = period.status_display || '정산 작성 중'
  }
  modalRef.value?.callModal()
}

const submit = async (event: Event) => {
  if (isSubmitting.value) return

  if (isValidate(event)) {
    validated.value = true
    return
  }

  if (!form.title.trim() || !form.start_date || !form.end_date) {
    validated.value = true
    return
  }

  if (form.start_date > form.end_date) {
    message('warning', '입력 확인', '정산 대상 종료일은 시작일보다 이전일 수 없습니다.')
    return
  }

  isSubmitting.value = true
  try {
    const payload: Partial<SettlementPeriod> = {
      project: props.project,
      title: form.title.trim(),
      start_date: form.start_date,
      end_date: form.end_date,
      payout_date: form.payout_date || null,
    }

    const ok =
      isEdit.value && targetId.value
        ? await salesStore.updatePeriod(targetId.value, payload)
        : await salesStore.createPeriod(payload)

    if (!ok) return
    modalRef.value?.close()
    emit('saved')
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '정산 회차 수정' : '신규 수수료 정산 회차 생성' }}</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="submit">
        <CModalBody>
          <CRow class="g-3">
            <CCol md="12">
              <CFormLabel class="small required">정산 회차명</CFormLabel>
              <CFormInput
                v-model="form.title"
                placeholder="예: 2026년 9월 1회차 수수료 정산"
                required
              />
              <CFormFeedback invalid>정산 회차명을 입력해주세요.</CFormFeedback>
            </CCol>

            <CCol md="6">
              <CFormLabel class="small required">정산 대상 시작일</CFormLabel>
              <DatePicker v-model="form.start_date" required placeholder="정산 대상 시작일" />
              <CFormFeedback invalid>정산 대상 시작일을 입력해주세요.</CFormFeedback>
              <small class="text-muted d-block mt-1">
                이 기간 내 체결된 계약 실적이 집계됩니다.
              </small>
            </CCol>

            <CCol md="6">
              <CFormLabel class="small required">정산 대상 종료일</CFormLabel>
              <DatePicker v-model="form.end_date" required placeholder="정산 대상 종료일" />
              <CFormFeedback invalid>정산 대상 종료일을 입력해주세요.</CFormFeedback>
            </CCol>

            <CCol md="6">
              <CFormLabel class="small">지급 예정일</CFormLabel>
              <DatePicker v-model="form.payout_date" placeholder="지급 예정일" />
            </CCol>

            <CCol md="6">
              <CFormLabel class="small">정산 상태</CFormLabel>
              <div class="pt-1">
                <v-chip color="warning" variant="flat" size="small">
                  {{ currentStatusDisplay }}
                </v-chip>
                <div class="form-text text-muted small mt-1">
                  정산 상태는 [정산 확정] 및 지급 완료 처리 시 자동으로 전환됩니다.
                </div>
              </div>
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            type="submit"
            color="primary"
            size="small"
            :loading="isSubmitting"
            :disabled="isSubmitting"
          >
            {{ isEdit ? '수정 저장' : '회차 생성' }}
          </v-btn>
          <v-btn
            :color="colorLight"
            size="small"
            flat
            :disabled="isSubmitting"
            @click="modalRef?.close()"
          >
            취소
          </v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>
</template>
