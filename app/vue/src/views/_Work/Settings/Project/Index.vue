<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin2'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { IssueProject, ProjectFilter } from '@/store/types/work_project.ts'
import ColumnSelector, {
  type ColumnOption,
} from '@/views/_Work/components/atomics/ColumnSelector.vue'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from '@/views/_Work/Manages/Projects/components/QuerySection.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import ProjectTable from './components/ProjectTable.vue'
import NoData from '@/components/NoData/Index.vue'

const cBody = ref()
const sideNavCall = () => cBody.value.toggle()

const { can, PERM } = usePerms()
const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))

const route = useRoute()
const workStore = useWork()

const projectResultsFlat = computed<IssueProject[]>(() => workStore.projectResultsFlat)
const allReadableProjects = computed(() => workStore.getAllReadableProjects)

const allColumnsPool: ColumnOption[] = [
  { key: 'name', label: '이름', fixed: true },
  { key: 'slug', label: '식별자' },
  { key: 'description', label: '설명' },
  { key: 'is_public', label: '공개여부' },
  { key: 'created', label: '등록일' },
  { key: 'updated', label: '수정일' },
]

const getSavedColumns = (): string[] => {
  const saved = localStorage.getItem('project-table-columns')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) return parsed
    } catch {
      // ignore
    }
  }
  return ['name', 'slug', 'description']
}

const selectedColumns = ref<string[]>(getSavedColumns())

watch(
  selectedColumns,
  nVal => {
    localStorage.setItem('project-table-columns', JSON.stringify(nVal))
  },
  { deep: true },
)

// 검색양식 관련 계산 및 메서드
const filterSubmit = (payload: ProjectFilter) => {
  workStore.fetchIssueProjectList(payload)
}

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({ status: '1' })
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :pageTitle="pageTitle" :navMenu="navMenu" @side-nav-call="sideNavCall" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              icon="mdi-office-building-cog-outline"
              color="blue-grey-lighten-1"
              size="small"
              class="mr-2"
            />
            프로젝트 관리
          </h5>
        </CCol>

        <CCol v-if="canProjectCreate" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <TextButton name="새 프로젝트" :to="{ name: '프로젝트 - 추가' }" />
          </span>
        </CCol>
      </CRow>

      <QuerySection
        ref="querySectionRef"
        :all-readable-projects="allReadableProjects"
        @filter-submit="filterSubmit"
      >
        <template #option>
          <ColumnSelector v-model="selectedColumns" :all-columns="allColumnsPool" />
        </template>
      </QuerySection>

      <NoData v-if="!projectResultsFlat.length" />

      <ProjectTable v-else :issue-projects-flat="projectResultsFlat" :columns="selectedColumns" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
