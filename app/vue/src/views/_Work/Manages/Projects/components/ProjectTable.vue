<script lang="ts" setup>
import { type PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'
import { markdownRender } from '@/utils/helper.ts'

defineProps({
  issueProjectsFlat: { type: Array as PropType<IssueProject[]>, default: () => [] },
})
</script>

<template>
  <v-divider class="mb-0" />
  <CTable striped hover small responsive align="middle">
    <colgroup>
      <col style="width: 40%" />
      <col style="width: 15%" />
      <col style="width: 45%" />
    </colgroup>
    <CTableHead>
      <CTableRow color="light" class="text-center">
        <CTableHeaderCell scope="col">이름</CTableHeaderCell>
        <CTableHeaderCell scope="col">식별자</CTableHeaderCell>
        <CTableHeaderCell scope="col">설명</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="proj in issueProjectsFlat" :key="proj.pk">
        <CTableDataCell class="pl-4">
          <div :style="{ paddingLeft: `${proj.depth * 20}px` }">
            <v-icon
              v-if="proj.depth > 0"
              icon="mdi-chevron-right"
              size="small"
              color="grey"
              class="mr-1"
            />
            <router-link :to="{ name: '(개요)', params: { projId: proj.slug } }" class="bold">
              {{ proj.name }}
            </router-link>
            <v-badge
              v-if="proj.status === '9'"
              color="secondary"
              content="잠금보관"
              inline
              rounded="1"
              size="x-small"
              class="ml-2"
            />
          </div>
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ proj.slug }}</CTableDataCell>
        <CTableDataCell>
          <div v-html="markdownRender(proj.description)" class="form-text" />
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>

<style lang="scss" scoped>
.bold {
  font-weight: bold;
}
</style>
