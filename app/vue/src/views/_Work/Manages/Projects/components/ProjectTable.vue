<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { markdownRender } from '@/utils/helper.ts'

defineProps({
  issueProjectsFlat: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const isOwnProject = (project: IssueProject) =>
  project.all_members?.map(m => m.user.pk).includes(userInfo?.value?.pk as number)
</script>

<template>
  <v-divider class="mb-0" />
  <CTable striped hover responsive align="middle">
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
          <span :style="{ paddingLeft: `${proj.depth * 10}px` }">
            <v-icon
              v-if="proj.depth > 0"
              icon="mdi-chevron-right"
              size="small"
              color="grey"
              class="mr-1"
            />
            <router-link
              :to="{ name: '(개요)', params: { projId: proj.slug } }"
              class="bold"
              :class="{ 'text-grey': proj.status !== '1' }"
            >
              {{ proj.name }}
            </router-link>
            <v-icon
              v-if="!proj.is_public"
              icon="mdi-lock"
              size="15"
              color="blue-grey-lighten-2"
              class="ml-2"
              title="비공개 프로젝트"
            />
            <v-icon
              v-if="isOwnProject(proj)"
              icon="mdi-account-tag"
              color="success"
              size="15"
              class="ml-2"
              title="내 프로젝트"
            />
            <v-icon
              v-if="proj?.is_bookmarked"
              icon="mdi-bookmark"
              color="info"
              size="15"
              class="ml-2"
              title="북마크됨"
            />
          </span>
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ proj.slug }}</CTableDataCell>
        <CTableDataCell>
          <span v-html="markdownRender(proj.description)" class="text-muted" />
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>

<style lang="scss" scoped>
.bold {
  font-weight: bold;
}

.dark-theme .text-grey {
  color: #888888 !important;
}

// 1. 마크다운 내부의 p 태그 마진 제거
.text-muted :deep(p) {
  margin-bottom: 0 !important;
  line-height: 1.5;
}

// 2. 셀의 수직 정렬 강화 (CTableDataCell에 적용)
:deep(td) {
  vertical-align: middle !important;
}
</style>
