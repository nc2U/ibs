<script lang="ts" setup>
import { computed, ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type PersonnelOrder } from '@/store/types/company.ts'
import AppointmentForm from './AppointmentForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ company: { type: String, default: null } })
const emit = defineEmits(['multi-submit'])

const refFormModal = ref()
const refAlertModal = ref()

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))

const createConfirm = () => {
  if (canHrWorkCreate.value) refFormModal.value.callModal()
  else refAlertModal.value.callModal()
}
const multiSubmit = (payload: PersonnelOrder) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-right">
    <v-btn color="primary" :disabled="!company" @click="createConfirm">
      인사 발령 등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="xl">
    <template #header>인사 발령 등록</template>
    <template #default>
      <AppointmentForm
        :company="company"
        @multi-submit="multiSubmit"
        @close="refFormModal.close()"
      />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
