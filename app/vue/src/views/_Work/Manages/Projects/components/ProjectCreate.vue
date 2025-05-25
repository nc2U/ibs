<script lang="ts" setup>
import ProjectForm from './ProjectForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
</script>

<template>
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <ProjectForm />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
