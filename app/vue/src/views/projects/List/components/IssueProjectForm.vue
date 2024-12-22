<script lang="ts" setup>
import { ref } from 'vue'
import type { IssueProject } from '@/store/types/work'
import FormModal from '@/components/Modals/FormModal.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'

const refIssueForm = ref()
const callModal = () => refIssueForm.value.callModal()

defineExpose({ callModal })

const emit = defineEmits(['on-submit'])
const onSubmit = (payload: IssueProject) => {
  emit('on-submit', payload)
  refIssueForm.value.close()
}
</script>

<template>
  <FormModal ref="refIssueForm" :size="'xl'">
    <template #header>새 업무 프로젝트 생성</template>
    <template #default>
      <CModalBody class="text-body">
        <ProjectForm @on-submit="onSubmit" />
      </CModalBody>
    </template>
  </FormModal>
</template>
