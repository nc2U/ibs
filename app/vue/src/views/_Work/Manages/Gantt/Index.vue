<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useIssue } from '@/store/pinia/work_issue.ts'
import type { Company } from '@/store/types/settings'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import GanttChart from '@/views/_Work/Manages/Gantt/components/GanttChart.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const issueStore = useIssue()
const getGantts = computed(() => issueStore.getGantts)

const sideNavCAll = () => cBody.value.toggle()

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await issueStore.fetchGanttIssues()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
        </CCol>
      </CRow>

      <SearchList />

      <GanttChart :gantts="getGantts" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
