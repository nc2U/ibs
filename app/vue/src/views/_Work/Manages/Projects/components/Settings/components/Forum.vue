<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { useBoard } from '@/store/pinia/board.ts'
import NoData from '@/views/_Work/components/NoData.vue'

const route = useRoute()

const brdStore = useBoard()
const boardList = computed(() => brdStore.boardList)

onBeforeMount(() => {
  brdStore.fetchBoardList({ project: route.params.projId as string })
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1">새 게시판</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!boardList.length" />

  <CRow v-else>
    <CCol>{{ boardList }}</CCol>
  </CRow>
</template>
