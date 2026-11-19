<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRouter, type LocationQueryRaw } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useInform } from '@/store/pinia/work_inform'
import { markdownRender, sanitizeExternalUrl } from '@/utils/helper'
import type { IssueProject, SimpleMember } from '@/store/types/work_project'
import Loading from '@/components/Loading/Index.vue'
import OverViewHeader from './components/OverViewHeader.vue'
import IssueTracker from './components/IssueTracker.vue'
import NewsBox from './components/NewsBox.vue'
import MemberBox from './components/MemberBox.vue'
import SubProjects from './components/SubProjects.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const props = defineProps<{
  navMenu?: any
  currentProject?: IssueProject | null
  query?: LocationQueryRaw
}>()

const router = useRouter()

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })

const workStore = useWork()
const currentProject = computed<IssueProject | null>(
  () => props.currentProject ?? workStore.currentProject,
)
const allMembers = computed<SimpleMember[]>(
  () => (currentProject.value as IssueProject)?.all_members ?? [],
)
const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const computedMembers = computed(() => {
  const organizedData = {} as { [key: string]: Array<{ pk: number; username: string }> }

  allMembers.value.forEach(item => {
    item.roles.forEach(role => {
      if (organizedData[role.name]) {
        organizedData[role.name].push(item.user)
      } else {
        organizedData[role.name] = [item.user]
      }
    })

    if (item.add_roles) {
      item.add_roles.forEach(role => {
        if (organizedData[role.name]) {
          organizedData[role.name].push(item.user)
        } else {
          organizedData[role.name] = [item.user]
        }
      })
    }
  })

  return organizedData
})

const issueStore = useIssue()
const trackerSum = computed(() => issueStore.trackerSum)

const loading = ref(false)

const safeHomepage = computed(() => sanitizeExternalUrl(currentProject.value?.homepage))
const renderedDescription = computed(() =>
  currentProject.value?.description ? markdownRender(currentProject.value.description) : '',
)

watch(
  () => currentProject.value?.pk,
  async pk => {
    const proj = currentProject.value
    if (pk && proj) {
      loading.value = true
      try {
        const tasks: Promise<unknown>[] = []
        if (!proj.module || proj.module.issue) {
          tasks.push(issueStore.fetchTrackerSummary(pk))
        }
        if (!proj.module || proj.module.news) {
          tasks.push(infStore.fetchNewsList({ project: proj.slug }))
        } else {
          infStore.newsList = []
        }
        await Promise.all(tasks)
      } catch (err) {
        console.error('Failed to load project overview data:', err)
      } finally {
        loading.value = false
      }
    }
  },
  { immediate: true },
)

const deleteProject = async (slug: string) => {
  const deleted = await workStore.deleteIssueProject(slug)
  if (deleted) {
    await router.push({ name: '워크스페이스' })
  }
}
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody
    ref="cBody"
    :nav-menu="navMenu"
    :current-project="currentProject"
    :query="query"
    :aside="false"
  >
    <template v-slot:default>
      <OverViewHeader
        v-if="currentProject"
        :project="currentProject"
        @delete-project="deleteProject"
      />

      <CAlert v-if="currentProject && currentProject.status !== '1'" color="warning">
        <v-icon icon="mdi-lock" color="warning" size="small" />
        이 워크스페이스는 닫혀 있거나 잠금보관 상태이며 읽기 전용입니다.
      </CAlert>

      <CRow v-if="renderedDescription" class="my-2">
        <CCol class="text-muted" v-html="renderedDescription" />
      </CRow>

      <CRow v-if="safeHomepage" class="ps-2 my-2">
        <li>
          <a :href="safeHomepage" target="_blank" rel="noopener noreferrer">
            {{ currentProject?.homepage }}
          </a>
        </li>
      </CRow>

      <CRow>
        <CCol v-if="!currentProject?.module || currentProject.module.issue" lg="6">
          <CRow class="mb-3">
            <IssueTracker :trackers="currentProject?.trackers" :tracker-summary="trackerSum" />
          </CRow>
        </CCol>

        <CCol lg="6">
          <NewsBox
            v-if="(!currentProject?.module || currentProject.module.news) && !!newsList.length"
            :news-list="newsList.slice(0, 5)"
          />

          <MemberBox
            v-if="!!Object.keys(computedMembers).length"
            :project-members="computedMembers"
          />

          <SubProjects
            v-if="currentProject?.sub_projects?.length"
            :sub-projects="currentProject?.sub_projects"
          />
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
