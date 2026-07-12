<script setup lang="ts">
import { computed, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from './components/ActivityLogList.vue'
import AsideController from './components/aside/AsideController.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!allProjectsTree.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const allProjectsTree = computed(() => workStore.allProjectsTree)

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
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-history" color="primary" size="small" class="mr-2" />업무실행내역
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
        ref="RefActCont"
        :to-date="toDate"
        :from-date="fromDate"
        @loading-start="loading = true"
        @loading-end="loading = false"
      />
    </template>
  </ContentBody>
</template>
