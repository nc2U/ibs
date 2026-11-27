<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Grade } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import GradeForm from './GradeForm.vue'

const props = defineProps<{
  grade: Grade
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: Grade, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const comStore = useCompany()
const pkPositions = computed(() => comStore.getPkPositions)

const positions = computed(() => {
  const ids = props.grade.positions || []
  return pkPositions.value
    .filter(p => ids.includes(p.value as number))
    .map(p => p.label)
    .join(', ')
})

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: Grade, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTableRow v-if="grade" class="text-center">
    <CTableDataCell>{{ grade.pk }}</CTableDataCell>
    <CTableDataCell>{{ grade.code }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ grade.role }}</CTableDataCell>
    <CTableDataCell>{{ grade.min_promotion_years ?? '-' }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ positions }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ grade.promotion_criteria }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" variant="flat" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직급 정보 수정</template>
    <template #default>
      <GradeForm
        :grade="grade"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
