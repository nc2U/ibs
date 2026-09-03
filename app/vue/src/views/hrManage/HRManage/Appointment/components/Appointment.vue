<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type PersonnelOrder } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import AppointmentForm from './AppointmentForm.vue'

defineProps({
  order: { type: Object as PropType<PersonnelOrder>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: PersonnelOrder) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)

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
      <CBadge color="primary">{{ order.order_type_desc }}</CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ order.order_no || '-' }}</CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">{{ order.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell class="text-muted small">{{ formatPrevState(order) }}</CTableDataCell>
    <CTableDataCell class="fw-semibold">{{ formatNewState(order) }}</CTableDataCell>
    <CTableDataCell class="text-left small">{{ order.description || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="xl">
    <template #header>인사 발령 상세 및 수정</template>
    <template #default>
      <AppointmentForm
        :order="order"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
