<script lang="ts" setup>
import { type PropType } from 'vue'
import { TableSecondary } from '@/utils/cssMixins.ts'
import type { Repository } from '@/store/types/work.ts'
import NoData from '@/views/_Work/components/NoData.vue'

defineProps({
  projId: { type: String, required: true },
  repoList: { type: Array as PropType<Repository[]>, default: () => [] },
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" class="ml-1">저장소 추가</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!repoList.length" />

  <CRow v-else>
    <CCol class="pt-4">
      <CTable hover striped small>
        <CTableHead>
          <CTableRow :color="TableSecondary" class="text-center">
            <CTableHeaderCell>식별자</CTableHeaderCell>
            <CTableHeaderCell>주 저쟝소</CTableHeaderCell>
            <CTableHeaderCell>형상관리시스템</CTableHeaderCell>
            <CTableHeaderCell>저장소(api)</CTableHeaderCell>
            <CTableHeaderCell>비고</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="repo in repoList" :key="repo.pk" class="text-center">
            <CTableDataCell class="text-left pl-3">
              <router-link :to="{ name: '(저장소)', params: { projId } }">
                {{ repo.slug }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>{{ repo.is_default }}</CTableDataCell>
            <CTableDataCell>Git</CTableDataCell>
            <CTableDataCell>
              <router-link :to="{ name: '(저장소)', params: { projId } }">
                {{ repo.github_api_url }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <span class="mr-2">
                <v-icon icon="mdi-account-multiple" color="info" size="16" />
                <router-link to="">사용자</router-link>
              </span>
              <span class="mr-2">
                <v-icon icon="mdi-pencil" color="success" size="16" />
                <router-link to="">편집</router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can-outline" color="warning" size="16" />
                <router-link to="">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
