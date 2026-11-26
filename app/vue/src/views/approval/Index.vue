<script setup lang="ts">
import { computed } from 'vue'
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

const isDetailView = computed(() => {
  const name = (route.name as string) || ''
  return /결재 대기함 - 보기|기안 문서함 - 보기|결재 문서함 - 보기|전체 문서함 - 보기/.test(name)
})

const isFormView = computed(() => {
  const name = (route.name as string) || ''
  return /기안 문서함 - 작성|기안 문서함 - 수정/.test(name)
})

const isCompanyScopedView = computed(() => route.name === '전체 문서함' || isFormView.value)
</script>

<template>
  <ComAuthGuard>
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      :selectable="isCompanyScopedView"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <PendingList v-if="route.name === '결재 대기함'" />

        <DraftedList v-else-if="route.name === '기안 문서함'" />

        <ApprovedList v-else-if="route.name === '결재 문서함'" />

        <AllDocumentsList v-else-if="route.name === '전체 문서함'" />

        <DelegationList v-else-if="route.name === '결재 위임 관리'" />

        <DocumentDetail v-else-if="isDetailView" :key="route.fullPath" />

        <DocumentForm v-else-if="isFormView" :key="route.fullPath" />
      </CCardBody>
    </ContentBody>
  </ComAuthGuard>
</template>
