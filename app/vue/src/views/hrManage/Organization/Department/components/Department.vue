<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Department } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import DepartmentForm from './DepartmentForm.vue'

const props = defineProps({
  department: { type: Object as PropType<Department>, required: true },
  getDeparts: { type: Array, default: () => [] },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkManager = computed(() => canHrWorkCreate.value || canHrWorkUpdate.value)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Department) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
const getUpperName = (up: number | null) => {
  const deps = up
    ? (props.getDeparts as {
        value: number
        label: string
        level: number
      }[])
    : []
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
    <CTableDataCell class="text-left pl-4">{{ department.task }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManager">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부서 정보 등록</template>
    <template #default>
      <DepartmentForm
        :department="department"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
