<script lang="ts" setup>
import { ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins'
import { write_human_resource } from '@/utils/pageAuth'
import { type Position } from '@/store/types/company'
import PositionForm from './PositionForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ company: { type: String, default: null } })
const emit = defineEmits(['multi-submit'])

const refFormModal = ref()
const refAlertModal = ref()

const createConfirm = () => {
  if (write_human_resource.value) refFormModal.value.callModal()
  else refAlertModal.value.callModal()
}
const multiSubmit = (payload: Position) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-right">
    <v-btn color="primary" :disabled="!company" @click="createConfirm"> 직위 정보 신규등록 </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>직위 정보 등록</template>
    <template #default>
      <PositionForm :company="company" @multi-submit="multiSubmit" @close="refFormModal.close()" />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
