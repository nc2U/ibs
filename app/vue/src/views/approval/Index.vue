<script setup lang="ts">
import { onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/approval/_menu/headermixin'
import { useRoute } from 'vue-router'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PendingList from '@/views/approval/components/PendingList.vue'
import DraftedList from '@/views/approval/components/DraftedList.vue'
import DocumentForm from '@/views/approval/components/DocumentForm.vue'
import DocumentDetail from '@/views/approval/components/DocumentDetail.vue'

const route = useRoute()

const comSelect = async (target: number | null) => {
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
      <CCardBody class="pb-5">
        <PendingList v-if="route.name === '결재 대기함'" />

        <DraftedList v-else-if="route.name === '기안함'" />

        <DocumentForm v-else-if="route.name === '결재문서 작성'" />

        <DocumentDetail v-else-if="route.name === '결재문서 상세'" />

        <DocumentForm v-else-if="route.name === '결재문서 수정'" />
      </CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
