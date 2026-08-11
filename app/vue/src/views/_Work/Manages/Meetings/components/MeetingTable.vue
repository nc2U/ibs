<script lang="ts" setup>
import { computed, type PropType, ref, watchEffect } from 'vue'
import { DEFAULT_MEETING_COLUMNS, MEETING_COLUMN_LABEL_MAP } from '../constants'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useRoute, useRouter } from 'vue-router'
import type { Meeting, MeetingCategory } from '@/store/types/work_meeting.ts'
import Pagination from '@/components/Pagination'
import MeetingItem from './MeetingItem.vue'

const props = defineProps({
  meetingList: { type: Array as PropType<Meeting[]>, default: () => [] },
  categories: { type: Array as PropType<MeetingCategory[]>, default: () => [] },
  columns: {
    type: Array as PropType<string[]>,
    default: () => DEFAULT_MEETING_COLUMNS,
  },
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

const pageSelect = (page: number) => emit('page-select', page)

// 활성화할 컬럼 목록 (프로젝트 내부에서는 'project' 컬럼 자동 제외) START
const activeColumns = computed(() => {
  if (route.params.projId) {
    return props.columns.filter(c => c !== 'project')
  }
  return props.columns
})
// 활성화할 컬럼 목록 END

defineExpose({ querySectionRef })
</script>

<template>
  <CCol col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive align="middle">
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <template v-for="colKey in activeColumns" :key="'head-' + colKey">
            <CTableHeaderCell
              scope="col"
              :class="{
                'text-left': colKey === 'status' || colKey === 'title',
              }"
            >
              {{ MEETING_COLUMN_LABEL_MAP[colKey] || colKey }}
            </CTableHeaderCell>
          </template>
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
          <MeetingItem :meeting="meeting" :columns="activeColumns" />
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
