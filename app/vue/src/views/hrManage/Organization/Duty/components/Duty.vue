<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Duty } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import StaffForm from './DutyForm.vue'

defineProps({ duty: { type: Object as PropType<Duty>, required: true } })

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Duty) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="duty" class="text-center">
    <CTableDataCell>{{ duty.pk }}</CTableDataCell>
    <CTableDataCell>{{ duty.code }}</CTableDataCell>
    <CTableDataCell>{{ duty.name }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ duty.desc }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직책 정보 등록</template>
    <template #default>
      <StaffForm
        :duty="duty"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
