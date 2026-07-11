<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import MeetingList from '@/views/_Work/Manages/Meetings/components/MeetingList.vue'
import MeetingAside from '@/views/_Work/Manages/Meetings/components/MeetingAside.vue'
import MeetingDetail from '@/views/_Work/Manages/Meetings/components/MeetingDetail.vue'
import MeetingForm from '@/views/_Work/Manages/Meetings/components/MeetingForm.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  issueProject: { type: Object as () => IssueProject, default: null },
})

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const route = useRoute()

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)
const categories = computed(() => meetingStore.categoryList)

const { can, PERM } = usePerms()

const canMeetingCreate = computed(() => {
  const opened = props.issueProject?.status !== '9'
  const isList = viewMode.value === 'list'
  return opened && can(PERM.MEETING_CREATE) && isList
})

const viewMode = computed(() => {
  if (route.name === '(회의) - 추가' || route.name === '(회의) - 수정') return 'form'
  if (route.name === '(회의) - 보기') return 'detail'
  return 'list'
})

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
    if (viewMode.value === 'list') {
      await meetingStore.fetchMeetingList({
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
    // Only fetch if entering meeting list or coming from outside meeting module
    if (
      (newName === '(회의)' && oldName !== '(회의)') ||
      (isMeetingRoute(newName) && !isMeetingRoute(oldName))
    ) {
      fetchMeetings()
    }
  },
)
watch(() => route.params.projId, fetchMeetings)

onBeforeMount(fetchMeetings)
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5><v-icon icon="mdi-account-group" color="primary" size="small" class="mr-2" />회의</h5>
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
      <MeetingList v-else :meeting-list="meetingList" :page="page" @page-select="onPageSelect" />
    </template>

    <template v-slot:aside>
      <MeetingAside :categories="categories" @filter-submit="onFilterSubmit" />
    </template>
  </ContentBody>
</template>
