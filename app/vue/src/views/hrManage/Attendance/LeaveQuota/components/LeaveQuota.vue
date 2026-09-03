<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type StaffLeaveQuota } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import LeaveQuotaForm from './LeaveQuotaForm.vue'

defineProps({
  quota: { type: Object as PropType<StaffLeaveQuota>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: StaffLeaveQuota) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="quota" class="text-center">
    <CTableDataCell>{{ quota.year }}년</CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">{{ quota.staff_name }}</a>
    </CTableDataCell>
    <CTableDataCell class="text-right">{{
      Number(quota.granted_days || 0).toFixed(2)
    }}</CTableDataCell>
    <CTableDataCell class="text-right">{{
      Number(quota.carry_over_days || 0).toFixed(2)
    }}</CTableDataCell>
    <CTableDataCell class="text-right">{{
      Number(quota.reward_days || 0).toFixed(2)
    }}</CTableDataCell>
    <CTableDataCell class="text-right fw-bold text-primary">
      {{ Number(quota.total_granted_days || 0).toFixed(2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right text-danger">
      {{ Number(quota.used_days || 0).toFixed(2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right fw-bold text-success">
      {{ Number(quota.remaining_days || 0).toFixed(2) }}
    </CTableDataCell>
    <CTableDataCell class="small text-muted">
      {{ quota.valid_start }} ~ {{ quota.valid_end }}
    </CTableDataCell>
    <CTableDataCell class="text-left small">{{ quota.note || '-' }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>연차 부여 상세 및 수정</template>
    <template #default>
      <LeaveQuotaForm
        :quota="quota"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
