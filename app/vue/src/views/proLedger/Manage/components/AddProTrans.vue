<script lang="ts" setup>
import { ref } from 'vue'
import { AlertLight } from '@/utils/cssMixins'
import { type ProBankAcc, type ProjectCashBook } from '@/store/types/proCash'
import FormModal from '@/components/Modals/FormModal.vue'
import ProTransForm from '@/views/proLedger/Manage/components/ProTransForm.vue'

defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['multi-submit', 'on-bank-create', 'on-bank-update'])

const createFormModal = ref()

const createConfirm = () => createFormModal.value.callModal()

const multiSubmit = (payload: { formData: ProjectCashBook; sepData: ProjectCashBook | null }) =>
  emit('multi-submit', payload)

const onBankCreate = (payload: ProBankAcc) => emit('on-bank-create', payload)
const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project" @click="createConfirm"> 신규등록</v-btn>
  </CAlert>

  <FormModal ref="createFormModal" size="lg">
    <template #header>프로젝트 입출금 거래 건별 등록</template>
    <template #default>
      <ProTransForm @close="createFormModal.close()" />
    </template>
  </FormModal>
</template>
