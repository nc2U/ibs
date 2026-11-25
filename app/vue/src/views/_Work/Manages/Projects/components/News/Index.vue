<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform'
import type { News } from '@/store/types/work_inform'
import type { IssueProject } from '@/store/types/work_project'
import {
  buildNewsFormData,
  type NewsFormPayload,
} from '@/views/_Work/Manages/News/components/newsFormHelper'
import Loading from '@/components/Loading/Index.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsForm from '@/views/_Work/Manages/News/components/NewsForm.vue'
import NewsDetail from '@/views/_Work/Manages/News/components/NewsDetail.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import { useWork } from '@/store/pinia/work_project'

defineProps<{
  navMenu?: string[]
  currentProject?: IssueProject | null
  query?: LocationQueryRaw
}>()

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })

const workStore = useWork()
const isProjectActive = computed(() => workStore.currentProject?.status === '1')

const RefDelNews = ref<InstanceType<typeof ConfirmModal> | null>(null)
const { can, PERM } = usePerms()
const canNewsManage = computed(() => isProjectActive.value && can(PERM.NEWS_MANAGE))
const viewForm = ref(false)

const infStore = useInform()
const news = computed(() => infStore.news as News | null)
const newsList = computed(() => infStore.newsList as News[])

const createNews = (payload: FormData, proj?: string) => infStore.createNews(payload, proj)
const updateNews = (pk: number, payload: FormData) => infStore.updateNews(pk, payload)
const deleteNews = (pk: number, proj: null | string) => infStore.deleteNews(pk, proj)

const onSubmit = async (payload: NewsFormPayload) => {
  const projSlug = String(route.params.projId ?? '')
  const form = buildNewsFormData({ ...payload, project: projSlug })
  const ok = payload.pk ? await updateNews(payload.pk, form) : await createNews(form, projSlug)
  if (ok) {
    viewForm.value = false
    if (!payload.pk) page.value = 1
  }
}

const newsDelConfirm = async () => {
  const newsId = Number(route.params.newsId)
  const projId = route.params.projId as string
  const ok = await deleteNews(newsId, projId)
  if (!ok) return
  RefDelNews.value?.close()
  await router.replace({ name: '(공지)', params: { projId } })
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
  if (route.params.projId)
    await infStore.fetchNewsList({ project: route.params.projId as string, page: page.value })
}

const [route, router] = [useRoute(), useRouter()]
watch(
  () => route.params?.projId,
  nVal => {
    page.value = 1
    if (nVal) infStore.fetchNewsList({ project: nVal as string, page: 1 })
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

watch(
  () => route.query.viewForm,
  nVal => {
    if (nVal && canNewsManage.value && route.name === '(공지)') viewForm.value = true
  },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  try {
    if (route.query.viewForm && canNewsManage.value) viewForm.value = true
    await dataSetup()
  } catch (err) {
    console.error('Failed to load project news data:', err)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  infStore.removeNews()
  infStore.newsList = []
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :aside="false">
    <template v-slot:default>
      <span v-if="route.name !== '(공지)'">
        <router-link :to="{ name: '(공지)', params: { projId: route.params.projId } }">
          공지
        </router-link>
        »
      </span>

      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-message-badge" color="green-darken-1" class="me-2" />
            공지
          </h5>
        </CCol>

        <CCol v-if="route.name === '(공지)'" class="text-end">
          <span v-if="canNewsManage">
            <TextButton name="새 공지" @click="viewForm = !viewForm" />
          </span>
        </CCol>

        <CCol v-else class="text-end">
          <span v-if="canNewsManage">
            <TextButton
              name="편집"
              icon="mdi-pencil"
              icon-color="amber"
              @click="viewForm = !viewForm"
            />
          </span>

          <span v-if="canNewsManage && !viewForm">
            <TextButton
              name="삭제"
              icon="mdi-trash-can-outline"
              icon-color="grey"
              @click="RefDelNews?.callModal()"
            />
          </span>
        </CCol>
      </CRow>

      <NewsForm v-if="viewForm" :news="news" @on-submit="onSubmit" @close-form="viewForm = false" />

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
          :can-manage="canNewsManage"
        />
      </template>
      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="me-2" />
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
