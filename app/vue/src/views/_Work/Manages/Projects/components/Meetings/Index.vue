<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import {
  ALL_MEETING_COLUMNS,
  DEFAULT_MEETING_COLUMNS,
} from '@/views/_Work/Manages/Meetings/constants.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useTableColumns } from '@/composables/useTableColumns.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ColumnSelector from '@/views/_Work/components/atomics/ColumnSelector.vue'
import QuerySection from '@/views/_Work/Manages/Meetings/components/QuerySection.vue'
import MeetingTable from '@/views/_Work/Manages/Meetings/components/MeetingTable.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import MeetingDetail from '@/views/_Work/Manages/Meetings/components/MeetingDetail.vue'
import MeetingForm from '@/views/_Work/Manages/Meetings/components/MeetingForm.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import NoData from '@/components/NoData/Index.vue'

const props = defineProps({
  currentProject: { type: Object as () => IssueProject, default: null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const route = useRoute()

const workStore = useWork()
const allReadableProjects = computed(() => workStore.getAllReadableProjects)

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)
const categories = computed(() => meetingStore.categoryList)

const { can, PERM } = usePerms()
const canProjectPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))

const canMeetingCreate = computed(() => {
  const opened = props.currentProject?.status === '1'
  const isList = viewMode.value === 'list'
  return opened && can(PERM.MEETING_CREATE) && isList
})

const viewMode = computed(() => {
  if (route.name === '(회의) - 추가' || route.name === '(회의) - 수정') return 'form'
  if (route.name === '(회의) - 보기') return 'detail'
  return 'list'
})

const page = ref(1)
const meetingListRef = ref()
const querySectionRef = ref()
const activeQueryId = ref<number | null>(null)
const listFilter = ref<MeetingFilter>({})

const onFilterSubmit = (filter: MeetingFilter) => {
  page.value = 1
  listFilter.value = filter
  meetingStore.fetchMeetingList({
    ...filter,
    project: route.params.projId as string,
    page: page.value,
  })
}

const onPageSelect = (p: number) => {
  page.value = p
  meetingStore.fetchMeetingList({
    ...listFilter.value,
    project: route.params.projId as string,
    page: p,
  })
}

const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  querySectionRef.value?.applyQuery(query)
}

const onResetQuery = () => {
  activeQueryId.value = null
  querySectionRef.value?.resetFilter()
}

const fetchMeetings = async () => {
  if (route.params.projId) {
    if (viewMode.value === 'list') {
      await meetingStore.fetchMeetingList({
        ...listFilter.value,
        page: page.value,
        project: route.params.projId as string,
      })
    }
    await meetingStore.fetchCategoryList(route.params.projId as string)
  }
}

watch(
  () => route.name,
  (newName, oldName) => {
    const isMeetingRoute = (name: any) => name && name.includes('(회의)')
    if (
      (newName === '(회의)' && oldName !== '(회의)') ||
      (isMeetingRoute(newName) && !isMeetingRoute(oldName))
    ) {
      fetchMeetings()
    }
  },
)
watch(() => route.params.projId, fetchMeetings)

// Columns Selector Start
const { selectedColumns } = useTableColumns(
  'project-meeting-table-columns',
  ALL_MEETING_COLUMNS,
  DEFAULT_MEETING_COLUMNS,
)
// Columns Selector End!

onBeforeMount(fetchMeetings)
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-account-group" color="green-darken-1" size="small" class="mr-2" />회의
          </h5>
        </CCol>

        <CCol class="text-right">
          <span v-if="canMeetingCreate" class="mr-2 form-text">
            <TextButton
              name="새 회의록"
              :to="{ name: '(회의) - 추가', params: { projId: route.params.projId } }"
            />
          </span>
        </CCol>
      </CRow>

      <MeetingForm v-if="viewMode === 'form'" />
      <MeetingDetail v-else-if="viewMode === 'detail'" />
      <template v-else>
        <!-- 검색 조건 영역 -->
        <CRow class="mb-1">
          <CCol col="12">
            <QuerySection
              ref="querySectionRef"
              :categories="categories"
              :search-projects="allReadableProjects"
              @filter-submit="onFilterSubmit"
            >
              <template #option>
                <ColumnSelector v-model="selectedColumns" :all-columns="ALL_MEETING_COLUMNS" />
              </template>
            </QuerySection>
          </CCol>
        </CRow>

        <NoData v-if="!meetingList.length" />

        <MeetingTable
          v-else
          ref="meetingListRef"
          :meeting-list="meetingList"
          :categories="categories"
          :search-projects="allReadableProjects"
          :page="page"
          @filter-submit="onFilterSubmit"
          @page-select="onPageSelect"
        />
      </template>
    </template>

    <template v-slot:aside>
      <SavedQueryAside
        target-type="meeting"
        :active-query-id="activeQueryId ?? undefined"
        :can-project-pub-query="canProjectPubQuery"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
    </template>
  </ContentBody>
</template>
