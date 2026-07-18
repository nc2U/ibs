<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { dateFormat, elapsedTime, timeFormat } from '@/utils/baseMixins'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useLogging } from '@/store/pinia/work_logging.ts'
import IssueSummary from './atomicViews/IssueSummary.vue'
import ProjectSummary from './atomicViews/ProjectSummary.vue'
import ActivityLog from '@/views/_Work/Manages/Activity/components/ActivityLog.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  projectResults: { type: Array as PropType<IssueProject[]>, default: () => [] },
  issueNum: {
    type: Object,
    default: () => {},
  },
})

const route = useRoute()

const accStore = useAccount()
const user = computed(() => accStore.user)
const userInfo = computed(() => accStore.userInfo)
const workManager = computed(() => accStore.workManager)

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const projectResults = computed(() => props.projectResults.slice())
</script>

<template>
  <CRow class="py-2 mb-2">
    <CCol>
      <span class="h5" style="font-size: 1.15em">
        {{ user?.profile?.name || user?.username }}
      </span>
    </CCol>

    <CCol class="text-right form-text">
      <span v-if="user?.pk === userInfo?.pk">
        <TextButton
          name="내 계정"
          icon="mdi-pencil"
          icon-color="amber"
          :to="{ name: '사용자 - 내 계정' }"
        />
      </span>
      <span v-if="workManager && user?.pk !== userInfo?.pk">
        <TextButton
          name="편집"
          icon="mdi-pencil"
          icon-color="amber"
          :to="{ name: '사용자 - 수정', params: { userId: user?.pk } }"
        />
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
              {{ user?.last_login ? timeFormat(user.last_login, 'full', '/') : '' }}
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

      <template v-if="projectResults.length">
        <CRow>
          <CCol>
            <span class="h5" style="font-size: 1.15em">프로젝트</span>
          </CCol>
        </CRow>

        <ProjectSummary :project-results="projectResults" />
      </template>
    </CCol>

    <CCol lg="6" class="pl-2">
      <template v-if="!!Object.keys(groupedActivities).length">
        <CRow class="mb-2">
          <CCol>
            <h5 style="font-size: 1.15em">
              <router-link
                :to="{
                  name: '업무실행내역',
                  query: { user: route.params.userId },
                }"
              >
                업무실행내역
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
