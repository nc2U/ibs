<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useWork } from '@/store/pinia/work'
import NoData from '@/views/_Work/components/NoData.vue'

const emit = defineEmits(['aside-visible'])

const newsList = computed(() => [])

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)

onBeforeMount(() => emit('aside-visible', false))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>공지</h5>
    </CCol>

    <CCol class="text-right">
      <span v-if="issueProject.status !== '9'" class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" class="ml-1">새 공지</router-link>
      </span>

      <span class="form-text">
        <v-icon icon="mdi-star" color="secondary" size="sm" />
        <router-link to="" class="ml-1">지켜보기</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!newsList.length" />

  <CRow v-else>
    <CCol></CCol>
  </CRow>
</template>
