<script lang="ts" setup>
import { computed, inject, type PropType, ref, watchEffect } from 'vue'
import type {
  Issue,
  IssueFilter,
  IssueProject,
  IssueStatus,
  Tracker,
} from '@/store/types/work_project.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { timeFormat } from '@/utils/baseMixins'
import { useRoute, useRouter } from 'vue-router'
import NoData from '@/views/_Work/components/NoData.vue'
import SearchList from './SearchList.vue'
import IssueDropDown from './IssueDropDown.vue'
import Pagination from '@/components/Pagination'

defineProps({
  projStatus: { type: String, default: '' },
  issueList: { type: Array as PropType<Issue[]>, default: () => [] },
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getUsers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getVersions: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['filter-submit', 'page-select'])

const [route, router] = [useRoute(), useRouter()]

const workManager = inject('workManager')

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: any) => {
  if (!event.target.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const filterSubmit = (payload: IssueFilter) => emit('filter-submit', payload)

const workStore = useWork()
const my_perms = computed(() => workStore.issueProject?.my_perms)
const issuePages = (pageNum: number) => workStore.issuePages(pageNum)
const pageSelect = (page: number) => emit('page-select', page)

// 지켜보기 / 관심끄기
const watchControl = (payload: any, issuePk: number) => {
  const form = new FormData()
  if (payload.watchers)
    payload.watchers.forEach(val => form.append('watchers', JSON.stringify(val)))
  else if (payload.del_watcher) form.append('del_watcher', JSON.stringify(payload.del_watcher))
  workStore.patchIssue(issuePk, form)
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>업무</h5>
    </CCol>

    <CCol class="text-right">
      <span
        v-if="projStatus !== '9' && (workManager || my_perms?.issue_create)"
        class="mr-2 form-text"
      >
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: `${String(route.name)} - 추가` }" class="ml-1"
          >새 업무만들기</router-link
        >
      </span>

      <span>
        <CDropdown color="secondary" variant="input-group" placement="bottom-end">
          <CDropdownToggle
            :caret="false"
            color="light"
            variant="ghost"
            size="sm"
            shape="rounded-pill"
          >
            <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
            <v-tooltip activator="parent" location="top">Actions</v-tooltip>
          </CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem
              v-if="route.params.projId"
              class="form-text"
              @click="router.push({ name: '(업무) - 보고서' })"
            >
              <router-link to="">
                <v-icon icon="mdi-chart-bar" color="amber" size="sm" />
                요약
              </router-link>
            </CDropdownItem>
            <CDropdownItem v-if="projStatus !== '9'" class="form-text" disabled>
              <!--              <router-link to="">-->
              <v-icon icon="mdi-file-document-arrow-right" color="blue-lighten" size="sm" />
              가져오기
              <!--              </router-link>-->
            </CDropdownItem>
            <CDropdownItem
              v-if="projStatus !== '9' && route.params.projId && workManager"
              class="form-text"
              @click="router.push({ name: '(설정)', query: { menu: '업무추적' } })"
            >
              <router-link to="">
                <v-icon icon="mdi-cog" color="secondary" size="sm" />
                설정
              </router-link>
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CCol>
  </CRow>

  <SearchList
    :all-projects="allProjects"
    :status-list="statusList"
    :tracker-list="trackerList"
    :get-issues="getIssues"
    :get-users="getUsers"
    :get-versions="getVersions"
    @filter-submit="filterSubmit"
  />

  <NoData v-if="!issueList.length" />

  <CCol v-else col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive>
      <colgroup>
        <col style="width: 8%" />
        <col style="width: 16%" />
        <col style="width: 8%" />
        <col style="width: 8%" />
        <col style="width: 8%" />
        <col style="width: 20%" />
        <col style="width: 12%" />
        <col style="width: 15%" />
        <col style="width: 5%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell scope="col">프로젝트</CTableHeaderCell>
          <CTableHeaderCell scope="col">유형</CTableHeaderCell>
          <CTableHeaderCell scope="col">상태</CTableHeaderCell>
          <CTableHeaderCell scope="col">우선순위</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">담당자</CTableHeaderCell>
          <CTableHeaderCell scope="col">변경</CTableHeaderCell>
          <CTableHeaderCell scope="col"></CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow
          v-for="issue in issueList"
          :key="issue.pk"
          class="text-center table-row cursor-menu"
          :color="selectedRow === issue.pk ? 'primary' : ''"
          @click="selectedRow = issue.pk"
        >
          <CTableDataCell>
            <router-link
              :to="{
                name: '(업무) - 보기',
                params: { projId: issue.project.slug, issueId: issue.pk },
              }"
            >
              {{ issue.pk }}
            </router-link>
          </CTableDataCell>
          <CTableDataCell>
            <router-link :to="{ name: '(개요)', params: { projId: issue.project.slug } }">
              {{ issue.project.name }}
            </router-link>
          </CTableDataCell>
          <CTableDataCell>{{ issue.tracker.name }}</CTableDataCell>
          <CTableDataCell
            :class="{
              'text-danger': issue.status.pk === 1,
              'text-success': issue.status.pk === 3,
              'text-warning': issue.status.pk === 4,
            }"
          >
            {{ issue.status.name }}
          </CTableDataCell>
          <CTableDataCell
            :class="{
              'text-grey': issue.priority.pk === 1,
              'text-warning': issue.priority.pk === 3,
              'text-danger': [4, 5].includes(issue.priority.pk),
              bold: issue.priority.pk === 5,
            }"
          >
            {{ issue.priority.name }}
          </CTableDataCell>
          <CTableDataCell class="text-left">
            <router-link
              :to="{
                name: '(업무) - 보기',
                params: { projId: issue.project.slug, issueId: issue.pk },
              }"
            >
              {{ issue.subject }}
            </router-link>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <router-link
              v-if="issue.assigned_to"
              :to="{ name: '사용자 - 보기', params: { userId: issue.assigned_to?.pk } }"
            >
              {{ issue.assigned_to?.username }}
            </router-link>
          </CTableDataCell>
          <CTableDataCell class="text-center">{{ timeFormat(issue.updated) }}</CTableDataCell>
          <CTableDataCell class="p-0">
            <IssueDropDown :issue="issue" @watch-control="watchControl" />
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="1"
      :limit="8"
      :pages="issuePages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>
