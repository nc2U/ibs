<script lang="ts" setup>
import { computed, ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Duty } from '@/store/types/company'
import DutyForm from './DutyForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'

defineProps({ company: { type: String, default: null } })
const emit = defineEmits(['multi-submit'])

const refFormModal = ref()
const refAlertModal = ref()

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HR_WORK_CREATE))

const createConfirm = () => {
  if (canHrWorkCreate.value) refFormModal.value.callModal()
  else refAlertModal.value.callModal()
}
const multiSubmit = (payload: Duty) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-right">
    <v-btn color="primary" :disabled="!company" @click="createConfirm"> 직책 정보 신규등록 </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>직책 정보 등록</template>
    <template #default>
      <DutyForm :company="company" @multi-submit="multiSubmit" @close="refFormModal.close()" />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
