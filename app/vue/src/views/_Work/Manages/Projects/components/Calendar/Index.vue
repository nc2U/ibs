<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useMeeting } from '@/store/pinia/work_meeting'
import { useCalendar } from '@/store/pinia/work_calendar'
import type { IssueFilter } from '@/store/types/work_issue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from '@/views/_Work/Manages/Projects/components/QuerySection.vue'
import SharedCalendar from '@/views/_Work/Manages/Calendar/components/SharedCalendar.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const route = useRoute()
const issueStore = useIssue()
const workStore = useWork()
const meetingStore = useMeeting()
const calendarStore = useCalendar()

const searchProjects = computed(() => workStore.getSearchProjects)

const fetchData = async (slug: string) => {
  await issueStore.fetchIssueList({ project: slug })
  await meetingStore.fetchMeetingList({ project: slug })
}

watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) fetchData(nVal as string)
  },
)

const filterSubmit = (payload: IssueFilter) => {
  issueStore.fetchIssueList({ ...payload, project: route.params.projId as string })
}

const summary = computed(() => {
  const issues = issueStore.issueList
  return {
    total: issues.length,
    open: issues.filter(i => !i.status.closed).length,
    closed: issues.filter(i => i.status.closed).length,
  }
})

const loading = ref(true)
const combinedLoading = computed(() => loading.value || calendarStore.loading)

onBeforeMount(async () => {
  if (route.params.projId) {
    await fetchData(route.params.projId as string)
  }
  loading.value = false
})
</script>

<template>
  <Loading :active="combinedLoading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              icon="mdi-calendar-clock"
              color="green-darken-1"
              size="small"
              class="mr-2"
            />캘린더
          </h5>
        </CCol>
      </CRow>

      <QuerySection :search-projects="searchProjects" @filter-submit="filterSubmit" />

      <CRow class="mb-3">
        <CCol>
          <SharedCalendar :project-slug="route.params.projId as string" />
        </CCol>
      </CRow>

      <v-card variant="outlined" class="mt-4 pa-4 border-dashed rounded-lg">
        <CRow align="center">
          <CCol md="4" class="border-right d-none d-md-block">
            <div class="text-subtitle-2 text-grey mb-2">프로젝트 업무 현황</div>
            <div class="d-flex justify-space-around align-center">
              <div class="text-center">
                <div class="text-h6 font-weight-bold">{{ summary.total }}</div>
                <div class="text-caption text-grey">전체</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-info">{{ summary.open }}</div>
                <div class="text-caption text-grey">진행중</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-success">{{ summary.closed }}</div>
                <div class="text-caption text-grey">완료</div>
              </div>
            </div>
          </CCol>
          <CCol md="8" class="pl-md-6">
            <div class="text-subtitle-2 text-grey mb-2">일정 가이드</div>
            <div class="d-flex flex-wrap gap-4">
              <div class="d-flex align-center mr-4">
                <v-icon icon="mdi-arrow-right-bold" color="success" size="small" class="mr-1" />
                <span class="text-body-2">오늘 시작</span>
              </div>
              <div class="d-flex align-center mr-4">
                <v-icon icon="mdi-arrow-left-bold" color="danger" size="small" class="mr-1" />
                <span class="text-body-2">오늘 종료</span>
              </div>
              <div class="d-flex align-center">
                <v-icon icon="mdi-rhombus" color="danger" size="small" class="mr-1" />
                <span class="text-body-2">오늘 시작/종료</span>
              </div>
            </div>
            <div class="mt-2 text-caption text-grey-darken-1">
              * 바(Bar)의 색상은 업무의 현재 상태(신규/진행/완료 등)를 나타냅니다.
            </div>
          </CCol>
        </CRow>
      </v-card>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>

<style lang="scss" scoped>
.border-dashed {
  border-style: dashed !important;
  border-width: 1.5px !important;
}

.gap-4 {
  gap: 1rem;
}
</style>
