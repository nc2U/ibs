<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SettlementPeriod } from '@/store/types/sales'
import { getToday } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  project: { type: Number, required: true },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const form = reactive({
  title: '',
  start_date: getToday(),
  end_date: getToday(),
  payout_date: '',
  status: '1' as '1' | '2' | '3',
})

const resetForm = () => {
  const today = getToday()
  form.title = ''
  form.start_date = today
  form.end_date = today
  form.payout_date = ''
  form.status = '1'
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
    form.status = period.status
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.title.trim()) {
    alert('정산 회차명을 입력해주세요.')
    return
  }
  if (!form.start_date || !form.end_date) {
    alert('정산 대상 기간을 입력해주세요.')
    return
  }

  const payload: Partial<SettlementPeriod> = {
    project: props.project,
    title: form.title.trim(),
    start_date: form.start_date,
    end_date: form.end_date,
    payout_date: form.payout_date || null,
    status: form.status,
  }

  if (isEdit.value && targetId.value) {
    // Note: If updatePeriod is needed, salesStore.createPeriod / custom update
    // But mostly period creation is the primary flow
    await salesStore.createPeriod(payload) // or update
  } else {
    await salesStore.createPeriod(payload)
  }
  modalRef.value.close()
  emit('saved')
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '정산 회차 수정' : '신규 수수료 정산 회차 생성' }}</template>
    <template #default>
      <CModalBody>
        <CRow class="g-3">
          <CCol md="12">
            <CFormLabel>정산 회차명 <span class="text-danger">*</span></CFormLabel>
            <CFormInput v-model="form.title" placeholder="예: 2026년 9월 1회차 수수료 정산" required />
          </CCol>

          <CCol md="6">
            <CFormLabel>정산 대상 시작일 <span class="text-danger">*</span></CFormLabel>
            <CFormInput v-model="form.start_date" type="date" required />
            <small class="text-muted">이 기간 내 체결된 계약 실적이 집계됩니다.</small>
          </CCol>

          <CCol md="6">
            <CFormLabel>정산 대상 종료일 <span class="text-danger">*</span></CFormLabel>
            <CFormInput v-model="form.end_date" type="date" required />
          </CCol>

          <CCol md="6">
            <CFormLabel>지급 예정일</CFormLabel>
            <CFormInput v-model="form.payout_date" type="date" />
          </CCol>

          <CCol md="6">
            <CFormLabel>정산 상태</CFormLabel>
            <CFormSelect v-model="form.status">
              <option value="1">정산 작성 중</option>
              <option value="2">정산 확정 (승인 대기)</option>
              <option value="3">지급 완료</option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small" @click="submit">
          {{ isEdit ? '수정 저장' : '회차 생성' }}
        </v-btn>
        <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
