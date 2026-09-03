<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type PromotionPolicy } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import PolicyForm from './PolicyForm.vue'

defineProps({
  policy: { type: Object as PropType<PromotionPolicy>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: PromotionPolicy) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="policy" class="text-center">
    <CTableDataCell class="fw-bold">
      <CBadge color="light" class="text-dark border">
        {{ policy.current_grade_code }}
      </CBadge>
      <CIcon icon="cil-arrow-right" class="mx-1 text-muted small" />
      <CBadge color="primary">
        {{ policy.target_grade_code }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ policy.min_years }}년</CTableDataCell>
    <CTableDataCell class="text-right">
      {{
        policy.min_avg_grade_point !== null && policy.min_avg_grade_point !== undefined
          ? Number(policy.min_avg_grade_point).toFixed(1)
          : '-'
      }}
    </CTableDataCell>
    <CTableDataCell>{{ policy.required_eval_grade || '-' }}</CTableDataCell>
    <CTableDataCell class="text-left small">{{
      policy.required_credentials || '-'
    }}</CTableDataCell>
    <CTableDataCell class="text-left small text-danger">{{
      policy.disqualification_conditions || '-'
    }}</CTableDataCell>
    <CTableDataCell class="text-left small text-muted">{{
      policy.description || '-'
    }}</CTableDataCell>
    <CTableDataCell>
      <CBadge :color="policy.is_active ? 'success' : 'secondary'" shape="rounded-pill">
        {{ policy.is_active ? '사용' : '미사용' }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">수정</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>승급 정책 상세 및 수정</template>
    <template #default>
      <PolicyForm
        :policy="policy"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
