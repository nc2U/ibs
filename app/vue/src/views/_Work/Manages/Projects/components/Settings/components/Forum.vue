<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBoard } from '@/store/pinia/board.ts'
import draggable from 'vuedraggable'
import NoData from '@/views/_Work/components/NoData.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const RefForumForm = ref()

const route = useRoute()

const brdStore = useBoard()
const boardList = computed(() => brdStore.boardList)
const fetchBoardList = (payload: any) => brdStore.fetchBoardList(payload)

const projId = computed(() => route.params.projId as string)

watch(projId, nVal => {
  if (nVal) fetchBoardList({ project: nVal })
})

onBeforeMount(() => fetchBoardList({ project: projId.value }))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1" @click="RefForumForm.callModal()">새 게시판</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!boardList.length" />

  <CRow v-else>
    <CCol class="mt-3">
      <CTable table small hover responsive>
        <col style="width: 30%" />
        <col style="width: 45%" />
        <col style="width: 25%" />
        <CTableHead>
          <CTableRow color="secondary">
            <CTableHeaderCell class="pl-2" colspan="3">게시판</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="brd in boardList" :key="brd.pk">
            <CTableDataCell class="pl-2">
              <router-link to="">{{ brd.name }}</router-link>
            </CTableDataCell>
            <CTableDataCell>{{ brd.description }}</CTableDataCell>
            <CTableDataCell>
              <v-icon
                icon="mdi-arrow-up-down-bold"
                color="success"
                size="16"
                class="cursor-move mr-3"
              />
              <span class="mr-3 cursor-pointer">
                <v-icon icon="mdi-pencil" color="amber" size="15" class="mr-2" />
                <router-link to="">편집</router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can-outline" color="grey" size="15" class="mr-2" />
                <router-link to="">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <FormModal ref="RefForumForm" size="lg"></FormModal>
</template>
