<script lang="ts" setup>
import { ref } from 'vue'
import ContractForm from './ContractForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'

defineProps<{
  project?: number | null
  unitSet?: boolean
}>()

defineEmits(['subscription-created', 'contract-converted'])

const createFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const isModalOpen = ref(false)

const createConfirm = () => {
  isModalOpen.value = true
  createFormModal.value?.callModal()
}

const onClose = () => {
  createFormModal.value?.close()
  isModalOpen.value = false
}
</script>

<template>
  <CAlert variant="solid" class="text-end bg-more-light">
    <v-btn color="primary" :disabled="!project" @click="createConfirm"> 신규등록</v-btn>
  </CAlert>

  <FormModal ref="createFormModal" size="xl" @close="onClose">
    <template #header>청약 / 계약 등록 수정</template>
    <template #default>
      <ContractForm
        v-if="isModalOpen"
        :project="project ?? undefined"
        :unit-set="unitSet"
        @close="onClose"
        @subscription-created="$emit('subscription-created')"
        @contract-converted="$emit('contract-converted')"
      />
    </template>
  </FormModal>
</template>
