<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { Company } from '@/store/types/settings'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from './components/NewsForm.vue'
import NewsList from './components/NewsList.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const viewForm = ref(false)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const sideNavCAll = () => cBody.value.toggle()

const infStore = useInform()
const newsList = computed(() => infStore.newsList)

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

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}</h5>
        </CCol>

        <CCol class="text-right">
          <span class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="15" class="mr-1" />
            <router-link to="" class="ml-1" @click="viewForm = true">새 공지</router-link>
          </span>

          <span v-if="$route.params.projId" class="mr-2 form-text">
            <v-icon icon="mdi-star" color="secondary" size="15" class="mr-1" />
            <!--  <router-link to="" class="ml-1" @click="">-->지켜보기
            <!--  </router-link>-->
          </span>
        </CCol>
      </CRow>

      <NewsForm v-if="viewForm" @on-submit="onSubmit" @close-form="viewForm = false" />

      <NewsList
        :page="page"
        :view-form="viewForm"
        :news-list="newsList"
        @page-select="pageSelect"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
