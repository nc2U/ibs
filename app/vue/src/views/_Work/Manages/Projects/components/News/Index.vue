<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUpdate } from 'vue'
import { useWork } from '@/store/pinia/work'
import { type PostFilter, useBoard } from '@/store/pinia/board'
import NoData from '@/views/_Work/components/NoData.vue'
import NewsList from '@/views/_Work/Manages/News/components/NewsList.vue'

const emit = defineEmits(['aside-visible'])

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)

const boardStore = useBoard()
const postList = computed(() => boardStore.postList)
const fetchPostList = (payload: PostFilter) => boardStore.fetchPostList(payload)

const dataSetup = () => fetchPostList({ board: 1, issue_project: issueProject.value?.pk ?? '' })

onBeforeUpdate(() => dataSetup())

onBeforeMount(() => {
  emit('aside-visible', false)
  dataSetup()
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default></template>

    <template v-slot:aside></template>
  </ContentBody>
  
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
