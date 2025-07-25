<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { IssueProject, SimpleMember } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import OverViewHeader from './components/OverViewHeader.vue'
import TimeSummary from './components/TimeSummary.vue'
import IssueTracker from './components/IssueTracker.vue'
import NewsBox from './components/NewsBox.vue'
import MemberBox from './components/MemberBox.vue'
import SubProjects from './components/SubProjects.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const iProject = computed<IssueProject | null>(() => workStore.issueProject)
const allMembers = computed<SimpleMember[]>(
  () => (workStore.issueProject as IssueProject)?.all_members ?? [],
)
const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const computedMembers = computed(() => {
  const organizedData = {} as { [key: string]: Array<{ pk: number; username: string }> }

  allMembers.value.forEach(item => {
    // Iterate over the roles of each user
    item.roles.forEach(role => {
      // If the role exists in the organizedData, push the user
      if (organizedData[role.name]) {
        organizedData[role.name].push(item.user)
      } else {
        // If the role doesn't exist, create a new array with the user
        organizedData[role.name] = [item.user]
      }
    })

    // Check if there are additional roles
    if (item.add_roles) {
      item.add_roles.forEach(role => {
        // If the role exists in the organizedData, push the user
        if (organizedData[role.name]) {
          organizedData[role.name].push(item.user)
        } else {
          // If the role doesn't exist, create a new array with the user
          organizedData[role.name] = [item.user]
        }
      })
    }
  })

  return organizedData
})

const patchIssueProject = (payload: { slug: string; status?: '1' | '9' }) =>
  workStore.patchIssueProject(payload)

const issueStore = useIssue()
const trackerSum = computed(() => issueStore.trackerSum)

watch(
  () => iProject.value,
  nVal => {
    if (nVal?.pk) issueStore.fetchTrackerSummary(nVal.pk)
  },
)

const closeProject = (slug: string) => patchIssueProject({ slug, status: '9' })

const reopenProject = (slug: string) => patchIssueProject({ slug, status: '1' })

const deleteProject = (slug: string) => {
  alert(`delete-project :: ${slug}`)
}

const loading = ref(true)
onBeforeMount(async () => {
  if (iProject.value) await issueStore.fetchTrackerSummary(iProject.value?.pk)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <OverViewHeader
        :project="iProject as IssueProject"
        @close-project="closeProject"
        @reopen-project="reopenProject"
        @delete-project="deleteProject"
      />

      <CAlert v-if="iProject?.status === '9'" color="warning">
        <v-icon icon="mdi-lock" color="warning" size="sm" />
        이 프로젝트는 닫혀 있으며 읽기 전용입니다.
      </CAlert>

      <CRow class="mt-2">
        <CCol>{{ iProject?.description }}</CCol>
      </CRow>

      <CRow v-if="iProject?.homepage" class="pl-2 my-3">
        <li>
          <a :href="iProject.homepage" target="_blank">{{ iProject?.homepage }}</a>
        </li>
      </CRow>

      <CRow>
        <CCol lg="6">
          <CRow class="mb-3">
            <IssueTracker :trackers="iProject?.trackers" :tracker-summary="trackerSum" />
          </CRow>

          <CRow class="mb-3">
            <TimeSummary :project="iProject as IssueProject" />
          </CRow>
        </CCol>

        <CCol lg="6">
          <NewsBox v-if="!!newsList.length" :news-list="newsList.slice(0, 5)" />

          <MemberBox
            v-if="!!Object.keys(computedMembers).length"
            :project-memgers="computedMembers"
          />

          <SubProjects
            v-if="iProject?.sub_projects?.length"
            :sub-projects="iProject?.sub_projects"
          />
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
