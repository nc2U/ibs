<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin2'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from './components/QuerySection.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const cBody = ref()
const sideNavCall = () => cBody.value.toggle()

const { can, PERM } = usePerms() // 사용자 권한 데이터
const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))

const route = useRoute()

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :pageTitle="pageTitle" :navMenu="navMenu" @side-nav-call="sideNavCall" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              icon="mdi-office-building-cog"
              color="teal-lighten-1"
              size="small"
              class="mr-2"
            />
            프로젝트 관리
          </h5>
        </CCol>

        <CCol v-if="canProjectCreate" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <TextButton name="새 프로젝트" :to="{ name: '프로젝트 - 추가' }" />
          </span>
        </CCol>
      </CRow>

      <QuerySection />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
