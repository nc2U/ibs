<script setup lang="ts">
import { pageTitle, navMenu } from '@/views/proDocs/_menu/headermixin1.ts'
import { useProDocsDocument } from '@/views/proDocs/composables/useProDocsDocument.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProDocsAuthGuard from '@/components/AuthGuard/ProDocsAuthGuard.vue'
import NoAuth from '@/views/_Accounts/NoAuth.vue'
import ListController from '@/components/Documents/ListController.vue'
import CategoryTabs from '@/components/Documents/CategoryTabs.vue'
import DocsList from '@/components/Documents/DocsList.vue'
import DocsDetail from '@/components/Documents/DocsDetail.vue'
import DocsForm from '@/components/Documents/DocsForm.vue'

const {
  can,
  PERM,
  fController,
  formRef,
  typeNumber,
  mainViewName,
  docsFilter,
  heatedPage,
  loading,
  project,
  projName,
  canDocsRead,
  canUpdateCurrentDoc,
  docs,
  docsList,
  categoryList,
  route,
  listFiltering,
  selectCate,
  pageSelect,
  docsRenewal,
  docsScrape,
  onSubmit,
  docsHit,
  linkHit,
  fileHit,
} = useProDocsDocument({ typeNumber: 1, mainViewName: '일반 문서 관리' })
</script>

<template>
  <ProDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <NoAuth v-if="project && !canDocsRead" />
      <CCardBody v-else class="pb-5">
        <div v-if="route.name === `${mainViewName}`" class="pt-3">
          <ListController
            ref="fController"
            :project="project"
            :docs-filter="docsFilter"
            @list-filter="listFiltering"
          />

          <CategoryTabs
            :category="Number(docsFilter.category) || 0"
            :category-list="categoryList"
            @select-cate="selectCate"
          />

          <DocsList
            :project="project"
            :limit="docsFilter.limit || 10"
            :page="docsFilter.page || 1"
            :docs-list="docsList"
            :view-route="mainViewName"
            @page-select="pageSelect"
          />
        </div>

        <div v-else-if="route.name.includes('보기')">
          <DocsDetail
            v-if="docs"
            :type-num="typeNumber"
            :heated-page="heatedPage"
            :re-order="docsFilter.ordering !== '-created'"
            :category="Number(docsFilter.category) || undefined"
            :docs="docs"
            :view-route="mainViewName"
            :curr-page="docsFilter.page ?? 1"
            :docs-filter="docsFilter"
            @docs-hit="docsHit"
            @link-hit="linkHit"
            @file-hit="fileHit"
            @docs-scrape="docsScrape"
            @docs-renewal="docsRenewal"
          />
        </div>

        <div v-else-if="route.name.includes('작성')">
          <DocsForm
            v-if="can(PERM.DOCS_CREATE)"
            ref="formRef"
            :sort-name="projName"
            :type-num="typeNumber"
            :category-list="categoryList"
            :view-route="mainViewName"
            @on-submit="onSubmit"
          />
          <CAlert v-else color="danger" class="m-3">이 페이지에 접근할 권한이 없습니다.</CAlert>
        </div>

        <div v-else-if="route.name.includes('수정')">
          <DocsForm
            v-if="canUpdateCurrentDoc"
            ref="formRef"
            :sort-name="projName"
            :type-num="typeNumber"
            :category-list="categoryList"
            :docs="docs ?? undefined"
            :view-route="mainViewName"
            @on-submit="onSubmit"
          />
          <CAlert v-else color="danger" class="m-3">이 페이지에 접근할 권한이 없습니다.</CAlert>
        </div>
      </CCardBody>
    </ContentBody>
  </ProDocsAuthGuard>
</template>
