<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/notices/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const msg = ref(pageTitle)
const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />
  <ContentBody>
    <CCardBody>
      {{ msg }}
      <div style="height: 420px"></div>
    </CCardBody>
  </ContentBody>
</template>
