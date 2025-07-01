<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useInform } from '@/store/pinia/work_inform.ts'
import Loading from '@/components/Loading/Index.vue'
import MainCarousel from './components/MainCarousel.vue'
import WiseWord from './components/WiseWord.vue'
import MyIssue from '@/views/_Work/MyIssue/Index.vue'
import NoticeList from './components/NoticeList.vue'

const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const loading = ref(true)
onBeforeMount(() => {
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
        <NoticeList :news-list="newsList" />
      </CCol>
    </CRow>
  </CContainer>
</template>
