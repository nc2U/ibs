<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUnmount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useMeeting } from '@/store/pinia/work_meeting'
import { useCalendar } from '@/store/pinia/work_calendar'
import { useCalendarFilter } from '@/store/pinia/work_calendar_filter'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import type { IssueFilter } from '@/store/types/work_issue'
import type { CustomQuery } from '@/store/types/work_inform'
import type { IssueProject } from '@/store/types/work_project'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from '@/views/_Work/Manages/Calendar/components/QuerySection.vue'
import SharedCalendar from '@/views/_Work/Manages/Calendar/components/SharedCalendar.vue'
import SummaryStatus from '@/views/_Work/Manages/Calendar/components/SummaryStatus.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import Loading from '@/components/Loading/Index.vue'

defineProps({
  navMenu: { type: Array as PropType<string[]>, default: () => [] },
  currentProject: { type: Object as PropType<IssueProject | null>, default: null },
  query: { type: Object, default: () => ({}) },
})

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })

const { can, PERM } = usePerms()
const canPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))
const canCalendarRead = computed(() => can(PERM.CALENDAR_READ))

const route = useRoute()
const issueStore = useIssue()
const workStore = useWork()
const meetingStore = useMeeting()
const calendarStore = useCalendar()
const accStore = useAccount()

const allReadableProjects = computed(() => workStore.getAllReadableProjects)
const getUsers = computed(() => accStore.getUsers)
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const meetingCategories = computed(() => meetingStore.categoryList)

const calendarFilterStore = useCalendarFilter()
const activeFilters = ref<Record<string, unknown>>(
  calendarFilterStore.buildFilterPayload((route.params.projId as string) || ''),
)
const calendarRef = ref<InstanceType<typeof SharedCalendar> | null>(null)
const querySectionRef = ref<InstanceType<typeof QuerySection> | null>(null)
const activeQueryId = computed(() => calendarFilterStore.activeQueryId)

const filterSubmit = (payload: IssueFilter) => {
  if (!canCalendarRead.value) return
  activeFilters.value = { ...payload }
  const range = calendarRef.value?.currentRange || { start: '', end: '' }
  calendarStore.fetchCalendarEvents(payload, range.start, range.end)
}

const onQueryClick = (query: CustomQuery) => {
  querySectionRef.value?.applyQuery(query)
}

const onResetQuery = () => {
  querySectionRef.value?.resetFilter()
}

const summary = computed(() => {
  const issues = calendarStore.events.filter(e => e.type === 'issue')
  return {
    total: issues.length,
    open: issues.filter(i => i.status && !i.status.closed).length,
    closed: issues.filter(i => i.status && i.status.closed).length,
  }
})

const loading = ref(true)
const combinedLoading = computed(() => loading.value || calendarStore.loading)

const loadProjectCalendarData = async (slug?: string) => {
  loading.value = true
  try {
    if (slug) {
      await meetingStore.fetchCategoryList(slug)
      const payload = calendarFilterStore.buildFilterPayload(slug)
      activeFilters.value = { ...payload }
      const range = calendarRef.value?.currentRange
      if (range?.start && range?.end) {
        await calendarStore.fetchCalendarEvents(payload, range.start, range.end)
      }
    }
  } catch (err) {
    console.error('Failed to load project calendar data:', err)
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.projId as string | undefined,
  (newSlug, oldSlug) => {
    if (newSlug && newSlug !== oldSlug) {
      loadProjectCalendarData(newSlug)
    }
  },
)

onBeforeMount(async () => {
  await loadProjectCalendarData(route.params.projId as string | undefined)
})

onBeforeUnmount(() => {
  calendarStore.events = []
  calendarFilterStore.resetFilter()
})
</script>

<template>
  <Loading :active="combinedLoading" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :aside="canCalendarRead">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              icon="mdi-calendar-clock"
              color="green-darken-1"
              size="small"
              class="me-2"
            />캘린더
          </h5>
        </CCol>
      </CRow>

      <template v-if="canCalendarRead">
        <QuerySection
          ref="querySectionRef"
          :search-projects="allReadableProjects"
          :status-list="statusList"
          :tracker-list="trackerList"
          :priority-list="priorityList"
          :meeting-categories="meetingCategories"
          :get-users="getUsers"
          @filter-submit="filterSubmit"
        />

        <CRow class="mb-3">
          <CCol>
            <SharedCalendar
              ref="calendarRef"
              :project-slug="route.params.projId as string"
              :issue-filters="activeFilters"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol>
            <SummaryStatus :summary="summary" title="워크스페이스 업무 현황" />
          </CCol>
        </CRow>
      </template>

      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="me-2" />
        캘린더를 조회할 수 있는 권한이 없습니다.
      </v-alert>
    </template>

    <template v-slot:aside>
      <SavedQueryAside
        target-type="calendar"
        :active-query-id="activeQueryId ?? undefined"
        :can-project-pub-query="canPubQuery"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
    </template>
  </ContentBody>
</template>
