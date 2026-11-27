<script lang="ts" setup>
import { ref, computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type Position } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import PositionForm from './PositionForm.vue'

const props = defineProps<{
  position: Position
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: Position, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const comStore = useCompany()
const getPkGrades = computed(() => comStore.getPkGrades)

const grades = computed(() => {
  const ids = props.position.grades || []
  return getPkGrades.value
    .filter(g => ids.includes(g.value as number))
    .map(g => g.label)
    .join(', ')
})

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: Position, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTableRow class="text-center">
    <CTableDataCell>{{ position.pk }}</CTableDataCell>
    <CTableDataCell>{{ position.name }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ grades }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ position.desc }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" variant="flat" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직위 정보 수정</template>
    <template #default>
      <PositionForm
        :position="position"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
