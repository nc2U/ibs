<script lang="ts" setup>
import { ref } from 'vue'
import type { IssueProject } from '@/store/types/work_project'
import ProjectForm from './ProjectForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

defineProps<{
  navMenu?: string[]
  currentProject?: IssueProject | null
}>()

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })
</script>

<template>
  <ContentBody ref="cBody" :nav-menu="navMenu" :aside="false">
    <template v-slot:default>
      <ProjectForm />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
