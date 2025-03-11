<script lang="ts" setup>
import { ref } from 'vue'
import { pageTitle, navMenu } from '@/views/comDocs/_menu/headermixin'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const msg = ref(pageTitle)
</script>

<template>
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
  <ContentBody>
    <CCardBody>
      {{ msg }}
      <div style="height: 420px"></div>
    </CCardBody>
  </ContentBody>
</template>
