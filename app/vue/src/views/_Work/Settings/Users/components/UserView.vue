<script lang="ts" setup>
import { computed, inject, type PropType } from 'vue'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { dateFormat, elapsedTime, timeFormat } from '@/utils/baseMixins'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useLogging } from '@/store/pinia/work_logging.ts'
import IssueSummary from './atomicViews/IssueSummary.vue'
import ProjectSummary from './atomicViews/ProjectSummary.vue'
import ActivityLog from '@/views/_Work/Manages/Activity/components/ActivityLog.vue'

const props = defineProps({
  issueProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  issueNum: {
    type: Object,
    default: () => {},
  },
})

const route = useRoute()

const workManager = inject('workManager', false)

const accStore = useAccount()
const user = computed(() => accStore.user)

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const issueProjects = computed(() => props.issueProjects.slice())
</script>

<template>
  <CRow class="py-2 mb-2">
    <CCol>
      <span class="h5" style="font-size: 1.15em">
        {{ user?.profile?.name || user?.username }}
      </span>
    </CCol>

    <CCol v-if="user && workManager" class="text-right form-text">
      <span class="mr-2">
        <v-icon icon="mdi-pencil" color="amber" size="sm" />
        <router-link :to="{ name: '사용자 - 수정', params: { userId: user.pk } }" class="ml-1">
          편집
        </router-link>
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CCol lg="6">
      <CRow class="mb-3">
        <CCol class="pl-5">
          <ul>
            <li>로그인 : {{ user?.username }}</li>
            <li>등록시각 : {{ user ? dateFormat(user.date_joined, '/') : '' }}</li>
            <li>
              마지막 로그인 :
              {{ user?.last_login ? timeFormat(user.last_login, false, '/') : '' }}
              {{ user?.last_login ? `(${elapsedTime(user?.last_login)})` : '' }}
            </li>
          </ul>
        </CCol>
      </CRow>

      <CRow>
        <CCol>
          <span class="h5" style="font-size: 1.15em">업무</span>
        </CCol>
      </CRow>

      <IssueSummary :issue-num="issueNum" />

      <template v-if="issueProjects.length">
        <CRow>
          <CCol>
            <span class="h5" style="font-size: 1.15em">프로젝트</span>
          </CCol>
        </CRow>

        <ProjectSummary :issue-projects="issueProjects" />
      </template>
    </CCol>

    <CCol lg="6" class="pl-2">
      <template v-if="!!Object.keys(groupedActivities).length">
        <CRow class="mb-2">
          <CCol>
            <h5 style="font-size: 1.15em">
              <router-link
                :to="{
                  name: '작업내역',
                  query: { user: route.params.userId },
                }"
              >
                작업내역
              </router-link>
            </h5>
          </CCol>
        </CRow>

        <ActivityLog
          v-for="(activity, date) in groupedActivities"
          :key="date"
          :activity="activity"
          :date="date as string"
        />
      </template>
    </CCol>
  </CRow>
</template>
