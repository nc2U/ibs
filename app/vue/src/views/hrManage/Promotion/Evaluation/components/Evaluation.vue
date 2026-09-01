<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type StaffEvaluation } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import EvaluationForm from './EvaluationForm.vue'

defineProps({
  evaluation: { type: Object as PropType<StaffEvaluation>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: StaffEvaluation) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)

const getGradeBadge = (grade: string) => {
  switch (grade) {
    case 'S':
      return { color: 'danger', label: 'S (탁월)' }
    case 'A':
      return { color: 'primary', label: 'A (우수)' }
    case 'B':
      return { color: 'success', label: 'B (보통)' }
    case 'C':
      return { color: 'warning', label: 'C (미흡)' }
    case 'D':
      return { color: 'secondary', label: 'D (불량)' }
    default:
      return { color: 'light', label: grade }
  }
}
</script>

<template>
  <CTableRow v-if="evaluation" class="text-center">
    <CTableDataCell>{{ evaluation.eval_year }}년</CTableDataCell>
    <CTableDataCell>
      <CBadge color="info" shape="rounded-pill">{{ evaluation.eval_period_desc }}</CBadge>
    </CTableDataCell>
    <CTableDataCell class="fw-bold">
      <a href="javascript:void(0);" @click="showDetail">{{ evaluation.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="getGradeBadge(evaluation.grade).color" shape="rounded-pill" class="px-2">
        {{ getGradeBadge(evaluation.grade).label }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell class="text-right fw-bold">
      {{ evaluation.score !== null && evaluation.score !== undefined ? Number(evaluation.score).toFixed(1) : '-' }}
    </CTableDataCell>
    <CTableDataCell>{{ evaluation.evaluator_name || '-' }}</CTableDataCell>
    <CTableDataCell>{{ evaluation.reviewer_name || '-' }}</CTableDataCell>
    <CTableDataCell class="text-left small">{{ evaluation.achievement_summary || '-' }}</CTableDataCell>
    <CTableDataCell class="text-left small">{{ evaluation.notes || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>인사 평가 상세 및 수정</template>
    <template #default>
      <EvaluationForm
        :evaluation="evaluation"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
