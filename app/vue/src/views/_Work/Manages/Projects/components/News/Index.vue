<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from '@/views/_Work/Manages/News/components/NewsForm.vue'
import NewsView from '@/views/_Work/Manages/News/components/NewsView.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const RefDelNews = ref()

const viewForm = ref(false)

const infStore = useInform()
const news = computed(() => infStore.news as News | null)
const newsList = computed(() => infStore.newsList as News[])

const createNews = (payload: any, proj?: string) => infStore.createNews(payload, proj)
const updateNews = (pk: number, payload: any) => infStore.updateNews(pk, payload)
const deleteNews = (pk: number, proj: null | string) => infStore.deleteNews(pk, proj)

const onSubmit = (payload: any) => {
  payload.project = route.params.projId
  const { pk, ...rest } = payload
  const getData: Record<string, any> = { ...rest }

  const form = new FormData()

  for (const key in getData) {
    if (key === 'files') {
      ;(getData[key] as any[]).forEach(val => form.append(key, JSON.stringify(val)))
    } else if (key === 'newFiles')
      getData[key]?.forEach(val => {
        form.append('new_files', val.file as Blob)
        form.append('new_descs', val.description as string)
      })
    else if (key === 'cngFiles') {
      getData[key]?.forEach(val => {
        form.append('cngPks', val.pk as any)
        form.append('cngFiles', val.file as Blob)
      })
    } else {
      const formValue = getData[key] === null ? '' : getData[key]
      form.append(key, formValue as string)
    }
  }
  if (pk) updateNews(pk, form)
  else createNews(form, payload.project)

  viewForm.value = false
}

const newsDelConfirm = async () => {
  RefDelNews.value.close()
  const newsId = Number(route.params.newsId)
  const projId = route.params.projId as string
  await deleteNews(newsId, projId)
  await router.replace({ name: '(공지)' })
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
  else infStore.removeNews()
  if (route.params.projId) await infStore.fetchNewsList({ project: route.params.projId as string })
}

const [route, router] = [useRoute(), useRouter()]
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
    else infStore.removeNews()
    viewForm.value = false
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
      <span v-if="route.name !== '(공지)'">
        <router-link :to="{ name: '(공지)' }">공지</router-link>
        »
      </span>
      <CRow class="py-2">
        <CCol>
          <h5>{{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}</h5>
        </CCol>

        <CCol v-if="route.name === '(공지)'" class="text-right">
          <span class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="15" />
            <router-link to="" class="ml-1" @click="viewForm = true">새 공지</router-link>
          </span>

          <span v-if="$route.params.projId" class="mr-2 form-text">
            <v-icon icon="mdi-star" color="secondary" size="15" />
            <!--  <router-link to="" class="ml-1" @click="">-->
            지켜보기
            <!--  </router-link>-->
          </span>
        </CCol>

        <CCol v-else class="text-right">
          <span class="mr-2 form-text">
            <v-icon icon="mdi-star" color="amber" size="15" />
            <!--  <router-link to="" class="ml-1">-->
            관심끄기
            <!--  </router-link>-->
          </span>

          <span class="mr-2 form-text">
            <v-icon icon="mdi-pencil" color="amber" size="15" />
            <router-link to="" class="ml-1" @click="viewForm = true">편집</router-link>
          </span>

          <span class="mr-2 form-text">
            <v-icon icon="mdi-trash-can-outline" color="grey" size="15" />
            <router-link to="" class="ml-1" @click="RefDelNews.callModal()">삭제</router-link>
          </span>
        </CCol>
      </CRow>

      <NewsForm v-if="viewForm" :news="news" @on-submit="onSubmit" @close-form="viewForm = false" />

      <NewsList
        v-if="route.name === '(공지)'"
        :page="page"
        :view-form="viewForm"
        :news-list="newsList"
        @page-select="pageSelect"
      />

      <NewsView
        v-else-if="route.name === '(공지) - 보기' && !!news"
        :news="news as News"
        :view-form="viewForm"
      />

      <ConfirmModal ref="RefDelNews">
        <template #default>이 공지의 삭제를 계속 진행하시겠습니까?</template>
        <template #footer>
          <v-btn color="danger" size="small" @click="newsDelConfirm">삭제</v-btn>
        </template>
      </ConfirmModal>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
