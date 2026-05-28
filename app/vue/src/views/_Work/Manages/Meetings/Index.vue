<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import type { Company } from '@/store/types/settings'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const issueProjects = computed(() => workStore.issueProjects)

provide('navMenu', navMenu)

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
    <template v-slot:default> 회의 리스트 준비 중... </template>

    <template v-slot:aside>
      <!-- Meeting Aside Content -->
    </template>
  </ContentBody>
</template>
