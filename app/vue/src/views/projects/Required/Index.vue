<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin6'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const projSelect = (target: number | null) => {
  // payStore.priceList = []
  // dataReset()
  // if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  // dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5"> ready! </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
