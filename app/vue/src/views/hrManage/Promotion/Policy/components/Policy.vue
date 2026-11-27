<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type PromotionPolicy } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import PolicyForm from './PolicyForm.vue'

defineProps<{
  policy: PromotionPolicy
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: PromotionPolicy, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: PromotionPolicy, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTableRow v-if="policy" class="text-center">
    <CTableDataCell class="fw-bold">
      <v-chip color="secondary" variant="outlined" size="x-small" class="border">
        {{ policy.current_grade_code }}
      </v-chip>
      <CIcon icon="cil-arrow-right" class="mx-1 text-muted small" />
      <v-chip color="info" variant="flat" size="x-small">
        {{ policy.target_grade_code }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell>{{ policy.min_years }}년</CTableDataCell>
    <CTableDataCell class="text-end">
      {{
        policy.min_avg_grade_point !== null && policy.min_avg_grade_point !== undefined
          ? Number(policy.min_avg_grade_point).toFixed(1)
          : '-'
      }}
    </CTableDataCell>
    <CTableDataCell>{{ policy.required_eval_grade || '-' }}</CTableDataCell>
    <CTableDataCell class="text-start small">{{
      policy.required_credentials || '-'
    }}</CTableDataCell>
    <CTableDataCell class="text-start small text-danger">{{
      policy.disqualification_conditions || '-'
    }}</CTableDataCell>
    <CTableDataCell class="text-start small text-muted">{{
      policy.description || '-'
    }}</CTableDataCell>
    <CTableDataCell>
      <v-chip :color="policy.is_active ? 'success' : 'secondary'" variant="flat" size="x-small">
        {{ policy.is_active ? '사용' : '미사용' }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" variant="flat" @click="showDetail">수정</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>승급 정책 상세 및 수정</template>
    <template #default>
      <PolicyForm
        :policy="policy"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
