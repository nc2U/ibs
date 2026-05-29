<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import MeetingList from '@/views/_Work/components/Meetings/MeetingList.vue'
import MeetingAside from '@/views/_Work/components/Meetings/MeetingAside.vue'

const props = defineProps({
  issueProject: { type: Object as () => IssueProject, default: null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const route = useRoute()
const workManager = inject('workManager')

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)
const categories = computed(() => meetingStore.categoryList)
const page = ref(1)

const onFilterSubmit = (filter: MeetingFilter) => {
  page.value = 1
  meetingStore.fetchMeetingList({ ...filter, page: page.value })
}

const onPageSelect = (p: number) => {
  page.value = p
  meetingStore.fetchMeetingList({
    page: p,
    project: route.params.projId as string,
  })
}

const fetchMeetings = async () => {
  if (route.params.projId) {
    await meetingStore.fetchMeetingList({
      page: page.value,
      project: route.params.projId as string,
    })
    await meetingStore.fetchCategoryList(route.params.projId as string)
  }
}

watch(() => route.params.projId, fetchMeetings)

onBeforeMount(fetchMeetings)
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>회의</h5>
        </CCol>

        <CCol class="text-right">
          <span v-if="issueProject?.status !== '9'" class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="15" class="mr-1" />
            <router-link to="" class="ml-1">새 회의록</router-link>
          </span>
        </CCol>
      </CRow>

      <MeetingList :meeting-list="meetingList" :page="page" @page-select="onPageSelect" />
    </template>

    <template v-slot:aside>
      <MeetingAside :categories="categories" @filter-submit="onFilterSubmit" />
    </template>
  </ContentBody>
</template>
