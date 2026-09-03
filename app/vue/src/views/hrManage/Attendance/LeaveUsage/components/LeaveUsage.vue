<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type StaffLeaveUsage } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import LeaveUsageForm from './LeaveUsageForm.vue'

defineProps({
  usage: { type: Object as PropType<StaffLeaveUsage>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: StaffLeaveUsage) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow
    v-if="usage"
    class="text-center"
    :class="{ 'table-secondary opacity-75': usage.is_cancelled }"
  >
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">{{ usage.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="usage.deduction_days > 0 ? 'primary' : 'info'" shape="rounded-pill">
        {{ usage.leave_type_desc }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ usage.start_date }}</CTableDataCell>
    <CTableDataCell>{{ usage.end_date }}</CTableDataCell>
    <CTableDataCell
      class="text-right fw-bold"
      :class="usage.deduction_days > 0 ? 'text-danger' : 'text-muted'"
    >
      {{ Number(usage.deduction_days || 0).toFixed(2) }} 일
    </CTableDataCell>
    <CTableDataCell class="text-left small">{{ usage.reason || '-' }}</CTableDataCell>
    <CTableDataCell>
      <CBadge v-if="usage.is_cancelled" color="danger">취소됨</CBadge>
      <CBadge v-else color="success">정상</CBadge>
    </CTableDataCell>
    <CTableDataCell class="small text-muted">
      {{ usage.created ? usage.created.substring(0, 10) : '-' }}
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>휴가 사용 상세 및 수정</template>
    <template #default>
      <LeaveUsageForm
        :usage="usage"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
