<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type PromotionCandidate } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import CandidateForm from './CandidateForm.vue'

defineProps<{
  candidate: PromotionCandidate
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: PromotionCandidate): void
  (e: 'on-delete', pk: number): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: PromotionCandidate) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'candidate':
      return { color: 'secondary', label: '심사 대상' }
    case 'recommended':
      return { color: 'info', label: '부서 추천' }
    case 'approved':
      return { color: 'success', label: '승진 확정' }
    case 'rejected':
      return { color: 'danger', label: '심사 탈락' }
    case 'hold':
      return { color: 'warning', label: '심사 보류' }
    default:
      return { color: 'light', label: status }
  }
}
</script>

<template>
  <CTableRow v-if="candidate" class="text-center">
    <CTableDataCell>{{ candidate.eval_year }}년</CTableDataCell>
    <CTableDataCell class="fw-bold">
      <a href="#" @click.prevent="showDetail">{{ candidate.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell>
      <v-chip color="light" variant="flat" size="x-small" class="text-body border">
        {{ candidate.current_grade_code }}
      </v-chip>
      <CIcon icon="cil-arrow-right" class="mx-1 text-muted small" />
      <v-chip color="info" variant="flat" size="x-small">
        {{ candidate.target_grade_code }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell class="text-end">
      {{ Number(candidate.tenure_years || 0).toFixed(1) }} 년
    </CTableDataCell>
    <CTableDataCell class="text-end fw-bold">
      {{
        candidate.avg_eval_score !== null && candidate.avg_eval_score !== undefined
          ? Number(candidate.avg_eval_score).toFixed(1)
          : '-'
      }}
    </CTableDataCell>
    <CTableDataCell>
      <v-chip
        :color="getStatusBadge(candidate.status).color"
        variant="flat"
        size="x-small"
        class="px-2"
      >
        {{ getStatusBadge(candidate.status).label }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell class="small text-muted">
      {{ candidate.promoted_date || '-' }}
    </CTableDataCell>
    <CTableDataCell class="text-start small">
      {{ candidate.committee_review || '-' }}
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" variant="flat" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>승급 심사 상세 및 심의 수정</template>
    <template #default>
      <CandidateForm
        :candidate="candidate"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
