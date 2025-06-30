<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { Company } from '@/store/types/settings'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsList from './components/NewsList.vue'

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const sideNavCAll = () => cBody.value.toggle()

const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await infStore.fetchNewsList({})
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <NewsList :news-list="newsList" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
