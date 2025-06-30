<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsView from '@/views/_Work/Manages/News/components/NewsView.vue'

defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const infStore = useInform()
const newsList = computed<News[]>(() => infStore.newsList)

const dataSetup = async () => {
  if (route.params.projId) await infStore.fetchNewsList({ project: route.params.projId as string })
}

const route = useRoute()
watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) infStore.fetchNewsList({ project: nVal as string })
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
      <NewsList v-if="route.name === '(공지)'" :news-list="newsList" />

      <NewsView v-else-if="route.name === '(공지) - 보기'" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
