<script lang="ts" setup>
import { type PropType, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { Meeting } from '@/store/types/work_meeting.ts'
import NoData from '@/components/NoData/Index.vue'
import Pagination from '@/components/Pagination'
import MeetingObj from './MeetingObj.vue'

defineProps({
  meetingList: { type: Array as PropType<Meeting[]>, default: () => [] },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select'])

const route = useRoute()
const router = useRouter()

const meetingStore = useMeeting()
const meetingPages = (limit: number) => meetingStore.meetingPages(limit)

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: any) => {
  if (!event.target.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const goDetail = (pk: number) => {
  if (route.params.projId)
    router.push({ name: '(회의) - 보기', params: { projId: route.params.projId, meetingId: pk } })
  else router.push({ name: '회의 - 보기', params: { meetingId: pk } })
}

const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <NoData v-if="!meetingList.length" />

  <CCol v-else col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive>
      <colgroup>
        <col style="width: 5%" />
        <col v-if="!route.params.projId" style="width: 15%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col :style="{ width: route.params.projId ? '35%' : '20%' }" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell v-if="!route.params.projId" scope="col">프로젝트</CTableHeaderCell>
          <CTableHeaderCell scope="col">상태</CTableHeaderCell>
          <CTableHeaderCell scope="col">카테고리</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">회의 일시</CTableHeaderCell>
          <CTableHeaderCell scope="col">작성자</CTableHeaderCell>
          <CTableHeaderCell scope="col">참석자 수</CTableHeaderCell>
          <CTableHeaderCell scope="col">등록일</CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow
          v-for="meeting in meetingList"
          @click="goDetail(meeting.pk)"
          @mouseover="selectedRow = meeting.pk"
          :color="selectedRow === meeting.pk ? 'primary' : ''"
          class="text-center table-row cursor-menu"
          :key="meeting.pk"
        >
          <MeetingObj :meeting="meeting" />
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="page"
      :limit="8"
      :pages="meetingPages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>

<style lang="scss" scoped>
.cursor-menu {
  cursor: pointer;
}
</style>
