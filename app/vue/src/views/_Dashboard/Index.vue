<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useBoard } from '@/store/pinia/board'
import Loading from '@/components/Loading/Index.vue'
import MainCarousel from './components/MainCarousel.vue'
import WiseWord from './components/WiseWord.vue'
import MyIssue from '@/views/_Work/MyIssue/Index.vue'
import NoticeApp from './components/NoticeApp/atomics/ListComp.vue'
import { useInform } from '@/store/pinia/work_inform.ts'

const noticeRoute = ref('공지 게시판')

// const boardStore = useBoard()
// const postList = computed(() => boardStore.postList)
// const noticeList = computed(() => boardStore.noticeList)

const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const loading = ref(true)
onBeforeMount(() => {
  // boardStore.fetchPostList({ board: 1 })
  infStore.fetchNewsList({})
  loading.value = false
})
</script>

<template>
  <CContainer fluid>
    <Loading v-model:active="loading" />
    <CRow class="mt-3">
      <CCol>
        <MainCarousel />
      </CCol>
    </CRow>
    <CRow>
      <CCol>
        <WiseWord />
      </CCol>
    </CRow>
    <CRow class="mb-3">
      <CCol>
        <MyIssue />
      </CCol>
    </CRow>
    <CRow>
      <CCol xl="12">
        <NoticeApp :main-view-name="noticeRoute" :news-list="newsList" />
      </CCol>
    </CRow>
  </CContainer>
</template>
