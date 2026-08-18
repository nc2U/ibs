<script setup lang="ts">
import { onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/comDocs/_menu/headermixin'
import { useRoute, useRouter } from 'vue-router'

const [route, router] = [useRoute(), useRouter()]

const comSelect = async (target: number | null, skipClearQuery = false) => {
  if (!!target) {
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  loading.value = false
})
</script>

<template>
  <ComDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">전자 결제 페이지</CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
