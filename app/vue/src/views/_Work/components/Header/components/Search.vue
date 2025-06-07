<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MultiSelect from '@/components/MultiSelect/index.vue'

const props = defineProps({ getProjects: { type: Array, default: () => [] } })
const emit = defineEmits(['change-project'])

const [route, router] = [useRoute(), useRouter()]

// 검색 관련 기능 시작
const search = ref('')
const goSearch = () => router.push({ name: '전체검색', query: { scope: '', q: search.value } })

onBeforeMount(async () => {
  if (route?.query.q) search.value = route.query.q as string
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
        mode="single"
        :options="getProjects"
        placeholder="프로젝트 바로가기"
        @change="emit('change-project', $event)"
      />
    </CCol>
  </CRow>
</template>
