<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import {
  DEFAULT_PROJECT_COLUMNS,
  PROJECT_COLUMN_LABEL_MAP,
} from '@/views/_Work/Settings/Project/constants.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { markdownRender } from '@/utils/helper.ts'

defineProps({
  issueProjectsFlat: { type: Array as PropType<IssueProject[]>, default: () => [] },
  columns: {
    type: Array as PropType<string[]>,
    default: () => DEFAULT_PROJECT_COLUMNS,
  },
})

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const isOwnProject = (project: IssueProject) =>
  project.all_members?.map(m => m.user.pk).includes(userInfo?.value?.pk as number)
</script>

<template>
  <v-divider class="mb-0" />
  <CTable striped hover responsive align="middle">
    <CTableHead>
      <CTableRow color="light" class="text-center">
        <template v-for="colKey in columns" :key="'head-' + colKey">
          <CTableHeaderCell
            scope="col"
            :class="{
              'text-left pl-4': colKey === 'name',
              'text-left': colKey === 'description',
            }"
          >
            {{ PROJECT_COLUMN_LABEL_MAP[colKey] || colKey }}
          </CTableHeaderCell>
        </template>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow
        v-for="proj in issueProjectsFlat"
        :key="proj.pk"
        :class="{ 'text-grey': proj.status !== '1' }"
      >
        <template v-for="colKey in columns" :key="'body-' + proj.pk + '-' + colKey">
          <!-- 이름 컬럼 -->
          <CTableDataCell v-if="colKey === 'name'" class="pl-4">
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
                title="비공개 워크스페이스"
              />
              <v-icon
                v-if="isOwnProject(proj)"
                icon="mdi-account-tag"
                color="success"
                size="15"
                class="ml-2"
                title="내 워크스페이스"
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

          <!-- 식별자 -->
          <CTableDataCell v-else-if="colKey === 'slug'" class="text-center">
            {{ proj.slug }}
          </CTableDataCell>

          <!-- 설명 -->
          <CTableDataCell v-else-if="colKey === 'description'">
            <span v-html="markdownRender(proj.description)" class="text-muted" />
          </CTableDataCell>

          <!-- 상태 -->
          <CTableDataCell v-else-if="colKey === 'status'" class="text-center">
            {{ proj.status_display }}
          </CTableDataCell>

          <!-- 홈페이지 -->
          <CTableDataCell v-else-if="colKey === 'homepage'" class="text-center">
            {{ proj.homepage }}
          </CTableDataCell>

          <!-- 상위 워크스페이스 -->
          <CTableDataCell v-else-if="colKey === 'parent'" class="text-center">
            {{ proj.parent_name }}
          </CTableDataCell>

          <!-- 공개여부 -->
          <CTableDataCell v-else-if="colKey === 'is_public'" class="text-center">
            <v-chip size="x-small" :color="proj.is_public ? 'primary' : 'grey'" variant="tonal">
              {{ proj.is_public ? '공개' : '비공개' }}
            </v-chip>
          </CTableDataCell>

          <!-- 등록일 -->
          <CTableDataCell
            v-else-if="colKey === 'created'"
            class="text-center text-caption text-muted"
          >
            {{ proj.created ? proj.created.substring(0, 10) : '-' }}
          </CTableDataCell>

          <!-- 수정일 -->
          <CTableDataCell
            v-else-if="colKey === 'updated'"
            class="text-center text-caption text-muted"
          >
            {{ proj.updated ? proj.updated.substring(0, 10) : '-' }}
          </CTableDataCell>
        </template>
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
