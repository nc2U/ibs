<script setup lang="ts">
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useLogging } from '@/store/pinia/work_logging'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings'
import type { ActLogEntry } from '@/store/types/work_logging'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from './components/ActivityLogList.vue'
import AsideController from './components/aside/AsideController.vue'

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const sideNavCall = () => cBody.value?.toggle()

const navMenu = computed(() => (!allReadableProjectsFlat.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const allReadableProjectsFlat = computed(() => workStore.allReadableProjectsFlat)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const parseQueryDate = (raw: unknown): Date | null => {
  if (typeof raw !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null
  const [y, m, d] = raw.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  return isNaN(dt.getTime()) ? null : dt
}

const toDate = ref<Date>(parseQueryDate(route.query.from) ?? new Date())
const fromDate = computed(() => new Date(toDate.value.getTime() - 9 * 24 * 60 * 60 * 1000))

watch(
  () => route.query.from,
  val => {
    const parsed = parseQueryDate(val)
    if (parsed) toDate.value = parsed
  },
)

onBeforeMount(() => {
  workStore.removeIssueProject()
})

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const toMove = (date: Date) => {
  toDate.value = date
}

const loading = ref<boolean>(true)
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCall" />

  <ContentBody ref="cBody" :nav-menu="navMenu">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-history" color="primary" size="small" class="me-2" />업무실행내역
          </h5>
        </CCol>
      </CRow>

      <ActivityLogList
        :to-date="toDate"
        :from-date="fromDate"
        :activities="groupedActivities"
        @to-move="toMove"
      />
    </template>

    <template v-slot:aside>
      <AsideController
        :to-date="toDate"
        :from-date="fromDate"
        @update:to-date="toDate = $event"
        @loading-start="loading = true"
        @loading-end="loading = false"
      />
    </template>
  </ContentBody>
</template>
