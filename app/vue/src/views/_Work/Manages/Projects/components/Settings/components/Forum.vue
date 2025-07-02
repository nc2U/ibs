<script lang="ts" setup>
import { computed } from 'vue'
import NoData from '@/views/_Work/components/NoData.vue'

const forumList = computed(() => [])
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1">새 게시판</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!forumList.length" />

  <CRow v-else>
    <CCol></CCol>
  </CRow>
</template>
