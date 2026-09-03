<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu as defaultNavMenu, pageTitle } from '@/views/approval/_menu/headermixin'
import { useRoute } from 'vue-router'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PendingList from '@/views/approval/components/PendingList.vue'
import DraftedList from '@/views/approval/components/DraftedList.vue'
import ApprovedList from '@/views/approval/components/ApprovedList.vue'
import AllDocumentsList from '@/views/approval/components/AllDocumentsList.vue'
import DelegationList from '@/views/approval/components/DelegationList.vue'
import DocumentForm from '@/views/approval/components/DocumentForm.vue'
import DocumentDetail from '@/views/approval/components/DocumentDetail.vue'
import ComAuthGuard from '@/components/AuthGuard/ComAuthGuard.vue'

const route = useRoute()

const navMenu = computed(() => defaultNavMenu)

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
  <ComAuthGuard>
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

        <DraftedList v-else-if="route.name === '기안 문서함'" />

        <ApprovedList v-else-if="route.name === '결재 문서함'" />

        <AllDocumentsList v-else-if="route.name === '전체 문서함'" />

        <DelegationList v-else-if="route.name === '결재 위임 관리'" />

        <DocumentDetail
          v-else-if="
            /결재 대기함 - 보기|기안 문서함 - 보기|결재 문서함 - 보기|전체 문서함 - 보기/.test(
              route.name as string,
            )
          "
        />

        <DocumentForm
          v-else-if="/기안 문서함 - 작성|기안 문서함 - 수정/.test(route.name as string)"
        />
      </CCardBody>
    </ContentBody>
  </ComAuthGuard>
</template>
