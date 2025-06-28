<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBoard } from '@/store/pinia/board'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import NoData from '@/views/_Work/components/NoData.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const infStore = useInform()

const boardStore = useBoard()
const postList = computed(() => boardStore.postList)

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
      <CRow class="py-2">
        <CCol>
          <h5>공지</h5>
        </CCol>

        <CCol class="text-right">
          <span v-if="issueProject?.status !== '9'" class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="sm" />
            <router-link to="" class="ml-1">새 공지</router-link>
          </span>

          <span class="form-text">
            <v-icon icon="mdi-star" color="secondary" size="sm" />
            <router-link to="" class="ml-1">지켜보기</router-link>
          </span>
        </CCol>
      </CRow>

      <NoData v-if="!postList.length" />

      <CRow v-else>
        <NewsList :post-list="postList" />
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
