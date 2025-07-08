<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { Company } from '@/store/types/settings'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from './components/ActivityLogList.vue'
import AsideController from './components/aside/AsideController.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const issueProjects = computed(() => workStore.issueProjects)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const toDate = ref(new Date())
const fromDate = computed(() => new Date(toDate.value.getTime() - 9 * 24 * 60 * 60 * 1000))

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const RefActCont = ref()

const toMove = async (date: Date) => (toDate.value = date)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu">
    <template v-slot:default>
      <ActivityLogList
        :to-date="toDate"
        :from-date="fromDate"
        :activities="groupedActivities"
        @to-move="toMove"
      />
    </template>

    <template v-slot:aside>
      <AsideController ref="RefActCont" :to-date="toDate" :from-date="fromDate" />
    </template>
  </ContentBody>
</template>
