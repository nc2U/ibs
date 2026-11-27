<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type PersonnelOrder } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import AppointmentForm from './AppointmentForm.vue'

defineProps<{
  order: PersonnelOrder
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: PersonnelOrder, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: PersonnelOrder, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)

const formatPrevState = (order: PersonnelOrder) => {
  const parts = [order.prev_department_name, order.prev_position_name, order.prev_duty_name].filter(
    Boolean,
  )
  return parts.length ? parts.join(' / ') : '-'
}

const formatNewState = (order: PersonnelOrder) => {
  const parts = [order.new_department_name, order.new_position_name, order.new_duty_name].filter(
    Boolean,
  )
  return parts.length ? parts.join(' / ') : '-'
}
</script>

<template>
  <CTableRow v-if="order" class="text-center">
    <CTableDataCell>{{ order.order_date }}</CTableDataCell>
    <CTableDataCell>
      <v-chip color="info" variant="flat" size="x-small">{{ order.order_type_desc }}</v-chip>
    </CTableDataCell>
    <CTableDataCell>{{ order.order_no || '-' }}</CTableDataCell>
    <CTableDataCell>
      <a href="#" role="button" @click.prevent="showDetail">{{ order.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell class="text-muted small">{{ formatPrevState(order) }}</CTableDataCell>
    <CTableDataCell class="fw-semibold">{{ formatNewState(order) }}</CTableDataCell>
    <CTableDataCell class="text-start small">{{ order.description || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" variant="flat" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="xl">
    <template #header>인사 발령 상세 및 수정</template>
    <template #default>
      <AppointmentForm
        :order="order"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
