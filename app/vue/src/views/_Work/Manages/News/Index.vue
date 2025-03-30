<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useBoard } from '@/store/pinia/board'
import { useRoute } from 'vue-router'
import type { Company } from '@/store/types/settings'
import NoData from '@/views/_Work/components/NoData.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import NewsList from './components/NewsList.vue'

const emit = defineEmits(['aside-visible'])

const route = useRoute()

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const boardStore = useBoard()
const postList = computed(() => boardStore.postList)

onBeforeMount(() => {
  emit('aside-visible', false)
  boardStore.fetchPostList({ board: 1 })
})
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
        </CCol>

        <CCol class="text-right">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="sm" />
            <router-link to="" class="ml-1">새 공지</router-link>
          </span>
        </CCol>
      </CRow>

      <NoData v-if="!postList.length" />

      <CRow v-else>
        <NewsList :post-list="postList" />
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
