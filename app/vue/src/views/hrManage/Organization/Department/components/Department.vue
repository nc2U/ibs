<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type Department } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import DepartmentForm from './DepartmentForm.vue'

const props = withDefaults(
  defineProps<{
    department: Department
    getDeparts?: {
      value?: number
      label: string
      level: number
    }[]
  }>(),
  {
    getDeparts: () => [],
  },
)

const emit = defineEmits<{
  (e: 'multi-submit', payload: Department, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManager = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: Department, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
const getUpperName = (up: number | null) => {
  const deps = up ? props.getDeparts : []
  return up && !!deps.length ? deps.filter(d => d.value === up).map(d => d.label)[0] : ''
}
</script>

<template>
  <CTableRow v-if="department" class="text-center">
    <CTableDataCell>{{ department.pk }}</CTableDataCell>
    <CTableDataCell>
      {{ getUpperName(department.upper_depart) }}
    </CTableDataCell>
    <CTableDataCell>{{ department.name }}</CTableDataCell>
    <CTableDataCell>{{ department.manager_name }}</CTableDataCell>
    <CTableDataCell class="text-start ps-4">{{ department.task }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManager">
      <v-btn color="info" variant="flat" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부서 정보 수정</template>
    <template #default>
      <DepartmentForm
        :department="department"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
