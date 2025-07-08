<script lang="ts" setup>
import { computed, onBeforeMount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBoard } from '@/store/pinia/board.ts'
import NoData from '@/views/_Work/components/NoData.vue'

const route = useRoute()

const brdStore = useBoard()
const boardList = computed(() => brdStore.boardList)
const fetchBoardList = (payload: any) => brdStore.fetchBoardList(payload)

const projId = computed(() => route.params.projId as string)

watch(projId, nVal => {
  if (nVal) fetchBoardList({ project: nVal })
})

onBeforeMount(() => {
  fetchBoardList({ project: projId.value })
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
    <CCol class="mt-3">
      <CTable table small hover responsive>
        <col width="40" />
        <col width="40" />
        <col width="30" />
        <CTableHead>
          <CTableRow color="secondary">
            <CTableHeaderCell colspan="3">게시판</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="brd in boardList" :key="brd.pk">
            <CTableDataCell>
              <router-link to="">{{ brd.name }}</router-link>
            </CTableDataCell>
            <CTableDataCell>{{ brd.description }}</CTableDataCell>
            <CTableDataCell>
              <v-icon icon="mdi-pencil" color="amber" size="15" />
              <v-icon icon="mdi-trash-can-outline" color="grey" size="15" />
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
