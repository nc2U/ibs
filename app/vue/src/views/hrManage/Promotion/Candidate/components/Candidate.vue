<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type PromotionCandidate } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import CandidateForm from './CandidateForm.vue'

defineProps({
  candidate: { type: Object as PropType<PromotionCandidate>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
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
      <a href="javascript:void(0);" @click="showDetail">{{ candidate.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge color="light" class="text-dark border">
        {{ candidate.current_grade_code }}
      </CBadge>
      <CIcon icon="cil-arrow-right" class="mx-1 text-muted small" />
      <CBadge color="primary">
        {{ candidate.target_grade_code }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ Number(candidate.tenure_years || 0).toFixed(1) }} 년
    </CTableDataCell>
    <CTableDataCell class="text-right fw-bold">
      {{
        candidate.avg_eval_score !== null && candidate.avg_eval_score !== undefined
          ? Number(candidate.avg_eval_score).toFixed(1)
          : '-'
      }}
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="getStatusBadge(candidate.status).color" shape="rounded-pill" class="px-2">
        {{ getStatusBadge(candidate.status).label }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell class="small text-muted">
      {{ candidate.promoted_date || '-' }}
    </CTableDataCell>
    <CTableDataCell class="text-left small">
      {{ candidate.committee_review || '-' }}
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
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
