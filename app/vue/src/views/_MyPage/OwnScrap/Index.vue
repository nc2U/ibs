<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/_MyPage/_menu/headermixin'
import { useAccount } from '@/store/pinia/account'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import DocScrapeList from './components/DocScrapeList.vue'
import PostScrapeList from './components/PostScrapeList.vue'

const mainViewName = ref('스크랩')
const sort = ref<'docs' | 'post'>('docs')
const page = ref<number>(1)

const accStore = useAccount()

// docs
const docScrapeList = computed(() => accStore.docScrapeList)
const docScrapeCount = computed(() => accStore.docScrapeCount)

const fetchDocScrapeList = (page: number) => accStore.fetchDocScrapeList(page)
const patchDocScrape = (pk: number, title: string) => accStore.patchDocScrape(pk, title)
const deleteDocScrape = (pk: number) => accStore.deleteDocScrape(pk)

// board
const scrapeList = computed(() => accStore.scrapeList)
const scrapeCount = computed(() => accStore.scrapeCount)

const fetchScrapeList = (page?: number) => accStore.fetchScrapeList(page)
const patchScrape = (pk: number, title: string) => accStore.patchScrape(pk, title)
const deleteScrape = (pk: number) => accStore.deleteScrape(pk)

const patchTitle = (pk: number, title: string) => patchScrape(pk, title)
const delScrape = (pk: number) => deleteScrape(pk)

const pageSelect = (p: number) => {
  page.value = p
  fetchScrapeList(p)
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await fetchScrapeList(page.value)
  await fetchDocScrapeList(page.value)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <CCardBody class="pb-5">
      <div class="pt-3">
        <CRow class="pb-2">
          <CCol sm="12" lg="9" xl="6">
            <CRow>
              <CCol class="d-grid gap-2 pr-0">
                <CFormCheck
                  v-model="sort"
                  value="docs"
                  :button="{
                    color: 'primary',
                    variant: 'outline',
                    shape: 'rounded-0',
                  }"
                  type="radio"
                  name="options-outlined"
                  id="primary-outlined"
                  label="문서"
                />
              </CCol>

              <CCol class="d-grid gap-2 pl-0">
                <CFormCheck
                  v-model="sort"
                  value="post"
                  :button="{ color: 'success', variant: 'outline', shape: 'rounded-0' }"
                  type="radio"
                  name="options-outlined"
                  id="success-outlined"
                  label="게시글"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <DocScrapeList
          v-if="sort === 'docs'"
          :sort="sort"
          :scrape-list="docScrapeList"
          :scrape-count="docScrapeCount"
          :view-route="mainViewName"
          :page="page"
          @patch-title="patchTitle"
          @del-scrape="delScrape"
          @page-select="pageSelect"
        />

        <PostScrapeList
          v-else
          :scrape-list="scrapeList"
          :scrape-count="scrapeCount"
          :view-route="mainViewName"
          :page="page"
          @patch-title="patchTitle"
          @del-scrape="delScrape"
          @page-select="pageSelect"
        />
      </div>
    </CCardBody>
  </ContentBody>
</template>
