<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { Company } from '@/store/types/settings'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import MeetingList from '@/views/_Work/components/Meetings/MeetingList.vue'
import MeetingAside from '@/views/_Work/components/Meetings/MeetingAside.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const issueProjects = computed(() => workStore.issueProjects)

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
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  await meetingStore.fetchMeetingList({ page: page.value })
  await meetingStore.fetchCategoryList()
  loading.value = false
})
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
      </CRow>

      <MeetingList :meeting-list="meetingList" :page="page" @page-select="onPageSelect" />
    </template>

    <template v-slot:aside>
      <MeetingAside :categories="categories" @filter-submit="onFilterSubmit" />
    </template>
  </ContentBody>
</template>
