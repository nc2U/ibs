<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/_MyPage/_menu/headermixin'
import type { User } from '@/store/types/accounts'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ListController from '@/views/_MyPage/OwnDocs/components/ListController.vue'
import DocsList from '@/views/_MyPage/OwnDocs/components/DocsList.vue'

const mainViewName = ref('내 등록 문서')
const userInfo = inject<ComputedRef<User>>('userInfo')

const docsFilter = ref<DocsFilter>({
  creator: '',
  search: '',
  ordering: '-created',
  page: 1,
})

const listFiltering = (payload: DocsFilter) => {
  docsFilter.value.ordering = payload.ordering
  docsFilter.value.search = payload.search
  docsFilter.value.page = payload.page
  fetchDocsList({ ...docsFilter.value })
}

const pageSelect = (page: number) => {
  docsFilter.value.page = page
  listFiltering(docsFilter.value)
}

const docStore = useDocs()
const docsList = computed(() => docStore.docsList)

const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)

const dataSetup = (pk: number) => {
  docsFilter.value.creator = pk
  fetchDocsList(docsFilter.value)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(userInfo?.value.pk as number)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <CCardBody class="pb-5">
      <div class="pt-3">
        <ListController ref="fController" :docs-filter="docsFilter" @list-filter="listFiltering" />

        <DocsList :docs-list="docsList" :view-route="mainViewName" @page-select="pageSelect" />
      </div>
    </CCardBody>
  </ContentBody>
</template>
