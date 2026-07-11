<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from '@/views/_Work/Manages/News/components/NewsForm.vue'
import NewsDetail from '@/views/_Work/Manages/News/components/NewsDetail.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const RefDelNews = ref()
const { can, PERM } = usePerms()
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
      getData[key]?.forEach((val: { file: File | Blob; description: string }) => {
        form.append('new_files', val.file)
        form.append('new_descs', val.description)
      })
    else if (key === 'cngFiles') {
      getData[key]?.forEach((val: { pk: number; file: File | Blob }) => {
        form.append('cngPks', String(val.pk))
        form.append('cngFiles', val.file)
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
  if (route.query.viewForm) viewForm.value = true
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
          <h5>
            <v-icon icon="mdi-bullhorn" color="primary" class="mr-2" />
            공지
          </h5>
        </CCol>

        <CCol v-if="route.name === '(공지)'" class="text-right">
          <span v-if="can(PERM.NEWS_MANAGE)">
            <TextButton name="새 공지" @click="viewForm = !viewForm" />
          </span>

          <span v-if="$route.params.projId && can(PERM.NEWS_READ)">
            <TextButton name="지켜보기" icon="mdi-star" icon-color="amber" color="secondary" />
          </span>
        </CCol>

        <CCol v-else class="text-right">
          <span v-if="can(PERM.NEWS_READ)">
            <TextButton name="관심끄기" icon="mdi-star" icon-color="amber" color="secondary" />
          </span>

          <span v-if="can(PERM.NEWS_MANAGE)">
            <TextButton
              name="편집"
              icon="mdi-pencil"
              icon-color="amber"
              @click="viewForm = !viewForm"
            />
          </span>

          <span v-if="can(PERM.NEWS_MANAGE) && !viewForm">
            <TextButton
              name="삭제"
              icon="mdi-trash-can-outline"
              icon-color="grey"
              @click="RefDelNews.callModal()"
            />
          </span>
        </CCol>
      </CRow>

      <NewsForm
        v-if="viewForm && news"
        :news="news"
        @on-submit="onSubmit"
        @close-form="viewForm = false"
      />

      <template v-if="can(PERM.NEWS_READ)">
        <NewsList
          v-if="route.name === '(공지)'"
          :page="page"
          :view-form="viewForm"
          :news-list="newsList"
          @page-select="pageSelect"
        />

        <NewsDetail
          v-else-if="route.name === '(공지) - 보기' && !!news"
          :news="news as News"
          :view-form="viewForm"
        />
      </template>
      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="mr-2" />
        공지사항을 조회할 수 있는 권한이 없습니다.
      </v-alert>

      <ConfirmModal ref="RefDelNews">
        <template #default>이 공지의 삭제를 계속 진행하시겠습니까?</template>
        <template #footer>
          <v-btn color="warning" size="small" @click="newsDelConfirm">삭제</v-btn>
        </template>
      </ConfirmModal>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
