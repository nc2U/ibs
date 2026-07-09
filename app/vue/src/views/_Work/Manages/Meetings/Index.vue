<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import MeetingList from './components/MeetingList.vue'
import MeetingAside from './components/MeetingAside.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const route = useRoute()

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!myProjects.value.length ? navMenu1 : navMenu2))

const { can, PERM } = usePerms()
const canMeetingCreate = computed(() => can(PERM.MEETING_CREATE))

const workStore = useWork()
const myProjects = computed(() => workStore.myProjects)

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)
const categories = computed(() => meetingStore.categoryList)

provide('navMenu', navMenu)

const page = ref(1)

const onFilterSubmit = (filter: MeetingFilter) => {
  page.value = 1
  meetingStore.fetchMeetingList({ ...filter, page: page.value })
}

const onPageSelect = (p: number) => {
  page.value = p
  meetingStore.fetchMeetingList({ page: p })
}

const loading = ref<boolean>(true)

const initData = async () => {
  loading.value = true
  await workStore.fetchAllProjectList()
  await meetingStore.fetchMeetingList({ page: page.value })
  await meetingStore.fetchCategoryList()
  loading.value = false
}

onBeforeMount(initData)

watch(
  () => route.name,
  (newName, oldName) => {
    // Only re-initialize if moving between different feature sets or back to list
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
          <h5>회의</h5>
        </CCol>
        <CCol class="text-right">
          <span v-if="canMeetingCreate" class="mr-2 form-text">
            <TextButton
              name="새 회의록"
              :my-projects="myProjects"
              :project-to="{ name: '(회의) - 추가' }"
            />
          </span>
        </CCol>
      </CRow>

      <!-- 전역 회의 관리 목록은 항상 리스트만 표시 -->
      <MeetingList :meeting-list="meetingList" :page="page" @page-select="onPageSelect" />
    </template>

    <template v-slot:aside>
      <MeetingAside :categories="categories" @filter-submit="onFilterSubmit" />
    </template>
  </ContentBody>
</template>
