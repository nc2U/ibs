<script lang="ts" setup>
import { ref } from 'vue'
import { AlertLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import ContractForm from '@/views/contracts/List/components/ContractForm.vue'

defineProps({
  project: { type: Number, default: null },
  unitSet: { type: Boolean, default: false },
})
const emit = defineEmits(['multi-submit', 'on-bank-create', 'on-bank-update'])

const createFormModal = ref()

const createConfirm = () => createFormModal.value.callModal()
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project" @click="createConfirm"> 신규등록</v-btn>
  </CAlert>

  <FormModal ref="createFormModal" size="xl">
    <template #header>청약 / 계약 등록 수정</template>
    <template #default>
      <ContractForm :project="project" :unit-set="unitSet" @close="createFormModal.close()" />
    </template>
  </FormModal>
</template>
