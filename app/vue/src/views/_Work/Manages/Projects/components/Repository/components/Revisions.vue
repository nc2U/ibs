<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Commit } from '@/store/types/work.ts'

defineProps({ commitList: { type: Array as PropType<Commit[]>, default: () => [] } })

const revSort = ref<'latest' | 'all'>('latest')
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ revSort === 'all' ? '리비전' : '최근 리비전' }}</h5>
    </CCol>
  </CRow>

  <CRow class="my-5">
    <CCol>
      <v-btn>차이점 보기</v-btn>
    </CCol>
  </CRow>

  <CTable hover responsive striped>
    <CTableHead>
      <CTableRow>
        <CTableHeaderCell>#</CTableHeaderCell>
        <CTableHeaderCell>일자</CTableHeaderCell>
        <CTableHeaderCell>작성자</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="commit in commitList" :key="commit.pk">
        <CTableDataCell>{{ commit.pk }}</CTableDataCell>
        <CTableDataCell>{{ commit.date }}</CTableDataCell>
        <CTableDataCell>{{ commit.author }}</CTableDataCell>
        <CTableDataCell>{{ commit.message }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CRow class="my-5">
    <CCol>
      <v-btn>차이점 보기</v-btn>
    </CCol>
  </CRow>

  <CRow v-if="revSort === 'latest'">
    <CCol>
      <router-link to="" @click="() => (revSort = 'all')">전체 리비전 보기</router-link>
    </CCol>
  </CRow>
  <CRow v-else> Pagination...</CRow>
</template>
