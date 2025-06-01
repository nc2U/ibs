<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import MultiSelect from '@/components/MultiSelect/index.vue'

const [route, router] = [useRoute(), useRouter()]

// 검색 관련 기능 시작
const search = ref('')
const goSearch = () => router.push({ name: '전체검색', query: { scope: '', q: search.value } })

// 프로젝트 선택 기능 시작
const workStore = useWork()
const getProjects = computed(() =>
  workStore.getAllProjects
    .filter(p => p.slug !== route.params.projId)
    .map(p => ({ value: p.slug, label: p.label })),
)
const selProject = ref(null)
const cngProject = (event: any) => {
  if (event)
    router.replace({
      name: route.name,
      params: { projId: event },
      query: route.query,
    })
}

onBeforeMount(async () => {
  if (route?.query.q) search.value = route.query.q as string
  await workStore.fetchAllIssueProjectList()
})
</script>

<template>
  <CRow class="mb-3">
    <CCol class="p-1">
      <CInputGroup size="">
        <CInputGroupText id="inputGroup-sizing-sm" @click="goSearch">검색</CInputGroupText>
        <CFormInput v-model="search" @keydown.enter="goSearch" @focusin="search = ''" />
      </CInputGroup>
    </CCol>
    <CCol class="p-1">
      <MultiSelect
        v-model="selProject"
        mode="single"
        :options="getProjects"
        placeholder="프로젝트 바로가기"
        @change="cngProject"
      />
    </CCol>
  </CRow>
</template>
