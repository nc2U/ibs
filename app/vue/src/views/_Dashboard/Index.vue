<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useBoard } from '@/store/pinia/board'
import MainCarousel from './components/MainCarousel.vue'
import WiseWord from './components/WiseWord.vue'
import MyIssue from '@/views/_Work/MyIssue/Index.vue'
import NoticeBoard from './components/NoticeBoard/ListComp.vue'

const noticeRoute = ref('공지 게시판')

const boardStore = useBoard()
const postList = computed(() => boardStore.postList)
const noticeList = computed(() => boardStore.noticeList)

onBeforeMount(() => boardStore.fetchPostList({ board: 1 }))
</script>

<template>
  <CContainer fluid>
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
        <NoticeBoard
          :main-view-name="noticeRoute"
          :notice-list="noticeList"
          :post-list="postList"
        />
      </CCol>
    </CRow>
  </CContainer>
</template>
