<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useTableColumns } from '@/composables/useTableColumns'
import type { Company } from '@/store/types/settings'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import ColumnSelector, {
  type ColumnOption,
} from '@/views/_Work/components/atomics/ColumnSelector.vue'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import MeetingTable from './components/MeetingTable.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import QuerySection from '@/views/_Work/Manages/Meetings/components/QuerySection.vue'
import NoData from '@/components/NoData/Index.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const route = useRoute()

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!allReadableProjectsFlat.value.length ? navMenu1 : navMenu2))

const { can, PERM } = usePerms()
const canMeetingCreate = computed(() => can(PERM.MEETING_CREATE))
const canProjectPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))

const workStore = useWork()
const allReadableProjectsFlat = computed(() => workStore.allReadableProjectsFlat)
const allReadableProjects = computed(() =>
  workStore.getAllReadableProjects.filter(pjt => pjt.module?.meeting),
)
const myProjects = computed(() => workStore.getMyProjects.filter(pjt => pjt.module?.meeting))

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)
const categories = computed(() => meetingStore.categoryList)

provide('navMenu', navMenu)

const page = ref(1)
const meetingListRef = ref()
const activeQueryId = ref<number | null>(null)

const listFilter = ref<MeetingFilter>({})

const onFilterSubmit = (filter: MeetingFilter) => {
  page.value = 1
  listFilter.value = filter
  meetingStore.fetchMeetingList({ ...filter, page: page.value })
}

const onPageSelect = (p: number) => {
  page.value = p
  meetingStore.fetchMeetingList({ ...listFilter.value, page: p })
}

const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  if (meetingListRef.value?.querySectionRef) {
    meetingListRef.value.querySectionRef.applyQuery(query)
  }
}

const onResetQuery = () => {
  activeQueryId.value = null
  if (meetingListRef.value?.querySectionRef) {
    meetingListRef.value.querySectionRef.resetFilter()
  }
}

// Columns Selector

const allColumnsPool: ColumnOption[] = [
  { key: 'name', label: '이름', fixed: true },
  { key: 'slug', label: '식별자' },
  { key: 'description', label: '설명' },
  { key: 'is_public', label: '공개여부' },
  { key: 'created', label: '등록일' },
  { key: 'updated', label: '수정일' },
]

const { selectedColumns } = useTableColumns('meeting-table-columns', allColumnsPool, [
  'name',
  'slug',
  'description',
])

const loading = ref<boolean>(true)

const initData = async () => {
  loading.value = true
  await meetingStore.fetchMeetingList({ page: page.value })
  await meetingStore.fetchCategoryList()
  loading.value = false
}

onBeforeMount(initData)

watch(
  () => route.name,
  (newName, oldName) => {
    const isMeetingRoute = (name: any) =>
      name && (name.includes('회의') || name.includes('Meeting'))
    if (isMeetingRoute(newName) && !isMeetingRoute(oldName)) {
      initData()
    } else if (newName === '회의' && oldName !== '회의') {
      initData()
    }
  },
)
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5><v-icon icon="mdi-account-group" color="primary" size="small" class="mr-2" />회의</h5>
        </CCol>
        <CCol class="text-right">
          <span v-if="canMeetingCreate" class="mr-2 form-text">
            <TextButton
              name="새 회의록"
              :project-list="myProjects"
              :project-to="{ name: '(회의) - 추가' }"
            />
          </span>
        </CCol>
      </CRow>

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
              <ColumnSelector v-model="selectedColumns" :all-columns="allColumnsPool" />
            </template>
          </QuerySection>
        </CCol>
      </CRow>

      <NoData v-if="!meetingList.length" />

      <!-- 전역 회의 관리 목록 -->
      <MeetingTable
        v-else
        ref="meetingListRef"
        :meeting-list="meetingList"
        :categories="categories"
        :columns="selectedColumns"
        :page="page"
        @page-select="onPageSelect"
      />
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
