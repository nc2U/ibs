<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import type { ContractSalesAgent } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'

const emit = defineEmits<{
  (e: 'confirm', payload: { id: number; isApproved: boolean; approvalNote: string }): void
}>()

const modalRef = ref()
const targetMapping = ref<ContractSalesAgent | null>(null)
const contractLabel = ref<string>('')

const form = reactive({
  is_settlement_approved: true,
  approval_note: '',
})

const displayContractInfo = computed(() => {
  if (contractLabel.value) return contractLabel.value
  if (targetMapping.value?.unit_info) {
    return `${targetMapping.value.unit_info} (${targetMapping.value.contractor_name || ''})`
  }
  return targetMapping.value ? `계약 번호 #${targetMapping.value.contract}` : ''
})

const open = (mapping: ContractSalesAgent, label?: string) => {
  targetMapping.value = mapping
  contractLabel.value = label || ''
  form.is_settlement_approved = mapping.is_settlement_approved
  form.approval_note = mapping.approval_note || ''
  modalRef.value?.callModal()
}

const close = () => {
  modalRef.value?.close()
}

const submit = () => {
  if (!targetMapping.value) return
  emit('confirm', {
    id: targetMapping.value.id,
    isApproved: form.is_settlement_approved,
    approvalNote: form.approval_note.trim(),
  })
  close()
}

defineExpose({ open, close })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>수수료 정산 승인 / 보류 관리</template>
    <template #icon>
      <v-icon icon="mdi-check-decagram-outline" size="small" color="primary" class="mr-2" />
    </template>
    <template #default>
      <CModalBody class="p-4">
        <!-- 대상 계약 및 담당자 요약 정보 -->
        <div v-if="targetMapping" class="p-3 mb-4 rounded bg-light border">
          <div class="row g-2 align-items-center">
            <div class="col-12 col-md-6">
              <span class="text-secondary small d-block">대상 계약</span>
              <strong class="text-body">
                {{ displayContractInfo }}
              </strong>
            </div>
            <div class="col-6 col-md-3">
              <span class="text-secondary small d-block">담당 상담사</span>
              <strong class="text-primary">
                {{ targetMapping.sales_person_name || '-' }}
              </strong>
            </div>
            <div class="col-6 col-md-3">
              <span class="text-secondary small d-block">소속 팀</span>
              <span class="badge bg-secondary">
                {{ targetMapping.team_name || '-' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 승인 여부 선택 -->
        <div class="mb-4">
          <CFormLabel class="fw-bold mb-2">정산 대상 승인 상태</CFormLabel>
          <div class="d-flex gap-3">
            <div
              class="border rounded p-3 flex-fill cursor-pointer transition-all"
              :class="{
                'border-success bg-success-subtle text-success fw-bold': form.is_settlement_approved,
                'border-light text-muted': !form.is_settlement_approved,
              }"
              @click="form.is_settlement_approved = true"
            >
              <div class="d-flex align-items-center">
                <input
                  id="statusApproved"
                  v-model="form.is_settlement_approved"
                  type="radio"
                  :value="true"
                  class="form-check-input me-2"
                />
                <label for="statusApproved" class="cursor-pointer mb-0">
                  <v-icon icon="mdi-check-circle" size="small" class="me-1" color="success" />
                  정산 승인
                </label>
              </div>
              <p class="small mb-0 mt-1 text-secondary ps-4">
                계약금 및 구비서류 완료. 정산 회차 실행 시 수수료 계산에 정상 반영됩니다.
              </p>
            </div>

            <div
              class="border rounded p-3 flex-fill cursor-pointer transition-all"
              :class="{
                'border-danger bg-danger-subtle text-danger fw-bold': !form.is_settlement_approved,
                'border-light text-muted': form.is_settlement_approved,
              }"
              @click="form.is_settlement_approved = false"
            >
              <div class="d-flex align-items-center">
                <input
                  id="statusPending"
                  v-model="form.is_settlement_approved"
                  type="radio"
                  :value="false"
                  class="form-check-input me-2"
                />
                <label for="statusPending" class="cursor-pointer mb-0">
                  <v-icon icon="mdi-alert-circle" size="small" class="me-1" color="danger" />
                  정산 보류 (미승인)
                </label>
              </div>
              <p class="small mb-0 mt-1 text-secondary ps-4">
                서류 미비/분납 등 사유로 이번 정산 회차 계산 대상에서 자동 제외됩니다.
              </p>
            </div>
          </div>
        </div>

        <!-- 정산 보류 사유 입력 -->
        <div v-if="!form.is_settlement_approved" class="mb-3">
          <CFormLabel class="fw-bold text-danger">
            정산 보류 사유 <span class="text-secondary small fw-normal">(선택 또는 권장)</span>
          </CFormLabel>
          <CFormTextarea
            v-model="form.approval_note"
            rows="3"
            placeholder="예: 계약금 2차 분납 500만원 미납 (입금 확인 후 승인 예정), 인감증명서 미징구 등"
          />
          <div class="form-text text-secondary mt-1">
            * 입력하신 보류 사유는 실적 목록에 표시되며, 차후 서류 완비 시 언제든 [승인]으로 전환할 수 있습니다.
          </div>
        </div>
      </CModalBody>

      <CModalFooter>
        <v-btn
          :color="form.is_settlement_approved ? 'success' : 'danger'"
          size="small"
          class="me-2"
          @click="submit"
        >
          <v-icon
            :icon="form.is_settlement_approved ? 'mdi-check' : 'mdi-alert-circle-outline'"
            size="small"
            class="me-1"
          />
          {{ form.is_settlement_approved ? '정산 승인으로 저장' : '정산 보류로 저장' }}
        </v-btn>
        <v-btn color="light" size="small" flat @click="close">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.transition-all {
  transition: all 0.2s ease;
}
</style>
