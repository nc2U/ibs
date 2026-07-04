<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useInform } from '@/store/pinia/work_inform.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from './components/NewsForm.vue'
import NewsList from './components/NewsList.vue'
import TopCreateButton from '@/views/_Work/components/atomics/TopCreateButton.vue'
import { CRow } from '@coreui/vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const viewForm = ref(false)
const route = useRoute()

const { can, PERM } = usePerms()

provide('navMenu', navMenu)
provide('query', route?.query)

const sideNavCAll = () => cBody.value.toggle()

const infStore = useInform()
const newsList = computed(() => infStore.newsList)
const importantNews = computed(() => newsList.value.filter(n => n.is_important))

const createNews = (payload: any) => infStore.createNews(payload)

const onSubmit = (payload: any) => {
  const getData: Record<string, any> = { ...payload }

  const form = new FormData()

  for (const key in getData) {
    if (key === 'newFiles')
      (getData[key] as any[]).forEach(val => {
        form.append('new_files', val.file as Blob)
        form.append('new_descs', val.description as string)
      })
    else {
      const formValue = getData[key] === null ? '' : getData[key]
      form.append(key, formValue as string)
    }
  }
  createNews(form)
  viewForm.value = false
}

const page = ref(1)
const pageSelect = (p: number) => {
  page.value = p
  infStore.fetchNewsList({ page: p })
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await infStore.fetchNewsList({ page: page.value })
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-bullhorn-variant" color="info" class="mr-2" />
            {{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}
          </h5>
        </CCol>

        <CCol class="text-right">
          <span v-if="can(PERM.NEWS_MANAGE)" class="mr-2 form-text">
            <TopCreateButton name="새 공지" @click="viewForm = !viewForm" />
          </span>

          <span v-if="$route.params.projId && can(PERM.NEWS_READ)" class="mr-2 form-text">
            <v-icon icon="mdi-star" color="secondary" size="15" class="mr-1" />
            <!--  <router-link to="" class="ml-1" @click="">-->지켜보기
            <!--  </router-link>-->
          </span>
        </CCol>
      </CRow>

      <NewsForm v-if="viewForm" @on-submit="onSubmit" @close-form="viewForm = false" />

      <v-alert
        v-if="importantNews.length && !viewForm"
        color="primary"
        variant="tonal"
        class="mb-4 py-2"
      >
        <v-icon icon="mdi-alert-decagram" class="mr-2" />
        <strong>중요 공지사항이 {{ importantNews.length }}건 있습니다.</strong>
      </v-alert>

      <NewsList
        v-if="can(PERM.NEWS_READ)"
        :page="page"
        :view-form="viewForm"
        :news-list="newsList"
        @page-select="pageSelect"
      />
      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="mr-2" />
        공지사항을 조회할 수 있는 권한이 없습니다.
      </v-alert>
    </template>

    <template v-slot:aside>
      <CRow class="mb-4">
        <CCol>
          <h6 class="asideTitle">최근 공지</h6>
          <v-divider class="mt-0" />
          <ul class="list-unstyled aside-menu">
            <li v-for="news in newsList.slice(0, 5)" :key="news.pk" class="mb-2 text-truncate">
              <v-icon icon="mdi-chevron-right" size="x-small" class="mr-1" />
              <router-link
                v-if="can(PERM.NEWS_READ)"
                :to="{
                  name: '(공지) - 보기',
                  params: { projId: news.project?.slug, newsId: news.pk },
                }"
                class="text-body-2"
              >
                {{ news.title }}
              </router-link>
              <span v-else class="text-body-2 text-muted">{{ news.title }}</span>
            </li>
          </ul>
        </CCol>
      </CRow>
    </template>
  </ContentBody>
</template>
