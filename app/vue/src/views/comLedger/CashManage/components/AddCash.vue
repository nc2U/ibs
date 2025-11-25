<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { CompanyBank, CashBook } from '@/store/types/comCash'
import type { Project } from '@/store/types/project'
import { AlertLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import CashForm from '@/views/comCash/CashManage/components/CashForm.vue'

defineProps({
  company: { type: Number, default: null },
  projects: { type: Array as PropType<Project[]>, default: () => [] },
})
const emit = defineEmits(['multi-submit', 'patch-d3-hide', 'on-bank-create', 'on-bank-update'])

const createFormModal = ref()

const createConfirm = () => createFormModal.value.callModal()

const multiSubmit = (payload: { formData: CashBook; sepData: CashBook | null }) =>
  emit('multi-submit', payload)

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!company" @click="createConfirm"> 신규등록</v-btn>
  </CAlert>

  <FormModal ref="createFormModal" size="lg">
    <template #header>본사 입출금 거래 건별 등록</template>
    <template #default>
      <CashForm
        :projects="projects"
        @multi-submit="multiSubmit"
        @patch-d3-hide="patchD3Hide"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
        @close="createFormModal.close()"
      />
    </template>
  </FormModal>
</template>
