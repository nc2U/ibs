<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useWork } from '@/store/pinia/work'

const emit = defineEmits(['aside-visible'])

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)

onBeforeMount(() => emit('aside-visible', false))
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default></template>

    <template v-slot:aside></template>
  </ContentBody>
  
  <CRow class="py-2">
    <CCol>
      <h5>파일</h5>
    </CCol>

    <CCol class="text-right">
      <span v-if="issueProject?.status !== '9'" class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" class="ml-1">파일추가</router-link>
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-divider class="mb-0" />
      <CTable small>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>파일</CTableHeaderCell>
            <CTableHeaderCell>날짜</CTableHeaderCell>
            <CTableHeaderCell>크기</CTableHeaderCell>
            <CTableHeaderCell>D/L</CTableHeaderCell>
            <CTableHeaderCell>Checksum</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
      </CTable>
    </CCol>
  </CRow>
</template>
