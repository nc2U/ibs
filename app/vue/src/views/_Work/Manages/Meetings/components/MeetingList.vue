<script lang="ts" setup>
import { type PropType, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { Meeting, MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'
import type { selectProject } from '@/store/types/work_project.ts'
import NoData from '@/components/NoData/Index.vue'
import QuerySection from './QuerySection.vue'
import MeetingItem from './MeetingItem.vue'
import Pagination from '@/components/Pagination'

const props = defineProps({
  meetingList: { type: Array as PropType<Meeting[]>, default: () => [] },
  categories: { type: Array as PropType<MeetingCategory[]>, default: () => [] },
  searchProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['filter-submit', 'page-select'])

const route = useRoute()
const router = useRouter()

const meetingStore = useMeeting()
const meetingPages = (limit: number) => meetingStore.meetingPages(limit)

const querySectionRef = ref()

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: any) => {
  if (!event.target.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const goDetail = (meeting: Meeting) => {
  const projId = (route.params.projId as string) || meeting.project_desc?.slug
  if (projId && meeting.pk) {
    router.push({ name: '(회의) - 보기', params: { projId, meetingId: meeting.pk } })
  }
}

const filterSubmit = (payload: MeetingFilter) => emit('filter-submit', payload)
const pageSelect = (page: number) => emit('page-select', page)

defineExpose({ querySectionRef })
</script>

<template>
  <!-- 검색 조건 영역 -->
  <CRow class="mb-1">
    <CCol col="12">
      <QuerySection
        ref="querySectionRef"
        :categories="categories"
        :search-projects="searchProjects"
        @filter-submit="filterSubmit"
      />
    </CCol>
  </CRow>

  <NoData v-if="!meetingList.length" />

  <CCol v-else col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive>
      <colgroup>
        <col style="width: 5%" />
        <col v-if="!route.params.projId" style="width: 15%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col :style="{ width: route.params.projId ? '30%' : '20%' }" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col style="width: 5%" />
        <col style="width: 10%" />
        <col style="width: 5%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell v-if="!route.params.projId" scope="col">프로젝트</CTableHeaderCell>
          <CTableHeaderCell scope="col" class="text-left">상태</CTableHeaderCell>
          <CTableHeaderCell scope="col">카테고리</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">회의 일시</CTableHeaderCell>
          <CTableHeaderCell scope="col">작성자</CTableHeaderCell>
          <CTableHeaderCell scope="col">참석</CTableHeaderCell>
          <CTableHeaderCell scope="col">등록일</CTableHeaderCell>
          <CTableHeaderCell scope="col">PDF</CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow
          v-for="meeting in meetingList"
          @click="goDetail(meeting)"
          @mouseover="selectedRow = meeting.pk"
          class="text-center table-row pointer"
          :key="meeting.pk"
        >
          <MeetingItem :meeting="meeting" />
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
