<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/comDocs/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComDocsAuthGuard from '@/components/AuthGuard/ComDocsAuthGuard.vue'

const msg = ref(pageTitle)

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <ComDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody>
        {{ msg }}
        <div style="height: 420px"></div>
      </CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
