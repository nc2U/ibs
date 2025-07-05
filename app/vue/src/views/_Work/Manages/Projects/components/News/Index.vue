<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from '@/views/_Work/Manages/News/components/NewsForm.vue'
import NewsView from '@/views/_Work/Manages/News/components/NewsView.vue'

defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const viewForm = ref(false)

const infStore = useInform()
const news = computed(() => infStore.news as News | null)
const newsList = computed(() => infStore.newsList as News[])

const createNews = (payload: any, proj?: string) => infStore.createNews(payload, proj)
const updateNews = (pk: number, payload: any) => infStore.updateNews(pk, payload)

const newFiles = ref<File[]>([])
const fileUpload = (file: File) => newFiles.value.push(file)

const onSubmit = (payload: any) => {
  payload.project = route.params.projId
  const getData: Record<string, any> = { ...payload }
  getData.newFiles = newFiles.value

  const form = new FormData()

  for (const key in getData) {
    if (key === 'newFiles')
      (getData[key] as any[]).forEach(val => form.append(key, val as string | Blob))
    else {
      const formValue = getData[key] === null ? '' : getData[key]
      form.append(key, formValue as string)
    }
  }
  createNews(form, payload.project)
  viewForm.value = false
}

const page = ref(1)
const pageSelect = (p: number) => {
  if (route.params.projId) {
    page.value = p
    infStore.fetchNewsList({ project: route.params.projId as string, page: p })
  }
}

const dataSetup = async () => {
  if (route.params.newsId) await infStore.fetchNews(Number(route.params.newsId))
  if (route.params.projId) await infStore.fetchNewsList({ project: route.params.projId as string })
}

const route = useRoute()
watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) infStore.fetchNewsList({ project: nVal as string })
  },
)

watch(
  () => route.params.newsId,
  nVal => {
    if (nVal) infStore.fetchNews(Number(nVal))
  },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await dataSetup()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <NewsForm
        v-if="viewForm"
        @on-submit="onSubmit"
        @file-upload="fileUpload"
        @close-form="viewForm = false"
      />

      <NewsList
        v-if="route.name === '(공지)'"
        :page="page"
        :view-form="viewForm"
        :news-list="newsList"
        @view-form="viewForm = true"
        @page-select="pageSelect"
      />

      <NewsView v-else-if="route.name === '(공지) - 보기' && !!news" :news="news as News" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
