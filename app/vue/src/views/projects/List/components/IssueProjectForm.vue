<script lang="ts" setup>
import { ref } from 'vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'

const refIssueForm = ref()
const callModal = () => refIssueForm.value.callModal()

defineExpose({ callModal })

const emit = defineEmits(['get-project'])
const modalClose = () => {
  refIssueForm.value.close()
  emit('get-project', '2')
}
</script>

<template>
  <FormModal ref="refIssueForm" :size="'xl'">
    <template #header>새 업무 프로젝트 생성</template>
    <template #default>
      <CModalBody class="text-body">
        <ProjectForm :redirect="false" @modal-close="modalClose" />
      </CModalBody>
    </template>
  </FormModal>
</template>
