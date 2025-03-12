<script lang="ts" setup>
import { ref } from 'vue'
import type { SuitCase } from '@/store/types/docs'
import FormModal from '@/components/Modals/FormModal.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const refIssueForm = ref()
const callModal = () => refIssueForm.value.callModal()

defineExpose({ callModal })

const emit = defineEmits(['on-submit'])
const onSubmit = (payload: SuitCase) => {
  emit('on-submit', payload)
  refIssueForm.value.close()
}
</script>

<template>
  <FormModal ref="refIssueForm" :size="'xl'">
    <template #header>새 소송사건 생성</template>
    <template #default>
      <CModalBody class="text-body px-4">
        <CaseForm @on-submit="onSubmit" />
      </CModalBody>
    </template>
  </FormModal>
</template>
