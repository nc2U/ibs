<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUpdate, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { type PostFilter, useBoard } from '@/store/pinia/board'
import NoData from '@/views/_Work/components/NoData.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const props = defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: () => null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()

const boardStore = useBoard()
const postList = computed(() => boardStore.postList)
// const fetchPostList = (payload: PostFilter) => boardStore.fetchPostList(payload)

const dataSetup = async () => {
  // await fetchPostList({ board: 1, issue_project: props.issueProject?.pk ?? '' })
  if (route.params.projId) {
    await workStore.fetchNewsList({ project: route.params.projId as string })
  }
}

const route = useRoute()
watch(
  () => route.params,
  nVal => {
    if (nVal && nVal.projId) {
      workStore.fetchNewsList({ project: nVal.projId as string })
    }
  },
  { deep: true },
)

onBeforeUpdate(() => dataSetup())

onBeforeMount(() => dataSetup())
</script>

<template>
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
