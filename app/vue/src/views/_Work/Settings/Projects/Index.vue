<script setup lang="ts">
import { ref, computed, inject, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin3'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import NoData from '@/views/_Work/components/NoData.vue'
import ProjectTable from './components/ProjectTable.vue'

const route = useRoute()

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const workManager = inject<boolean>('workManager', false)

const workStore = useWork()
const projectList = computed(() => workStore.AllIssueProjects)

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="pageTitle" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>프로젝트</h5>
        </CCol>

        <CCol v-if="workManager" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <v-icon icon="mdi-plus-circle" color="success" size="15" />
            <router-link :to="{ name: '프로젝트 - 추가' }" class="ml-1">새 프로젝트</router-link>
          </span>
        </CCol>
      </CRow>

      <SearchList />

      <NoData v-if="!projectList.length" />

      <CRow v-else>
        <CCol>
          <ProjectTable :issue-project-list="projectList" />
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
