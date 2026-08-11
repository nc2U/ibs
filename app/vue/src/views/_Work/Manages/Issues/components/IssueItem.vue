<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { DEFAULT_ISSUE_COLUMNS } from '@/views/_Work/Manages/Issues/constants.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Issue } from '@/store/types/work_issue.ts'
import IssueDropDown from './IssueDropDown.vue'

const props = defineProps({
  issue: { type: Object as PropType<Issue>, required: true },
  columns: { type: Array as PropType<string[]>, default: () => DEFAULT_ISSUE_COLUMNS },
})

const { can, canViewUser, PERM } = usePerms()
const canIssueRead = computed(() => can(PERM.ISSUE_READ) && props.issue.project?.slug)
</script>

<template>
  <CTableDataCell>
    <router-link
      v-if="canIssueRead"
      :to="{
        name: '(업무) - 보기',
        params: { projId: issue.project.slug, issueId: issue.pk },
      }"
    >
      #{{ issue.pk }}
    </router-link>
    <span v-else>{{ issue.pk }}</span>
  </CTableDataCell>

  <template v-for="colKey in columns" :key="'body-' + issue.pk + '-' + colKey">
    <!-- 제목 -->
    <CTableDataCell v-if="colKey === 'subject'" class="text-left">
      <v-icon v-if="issue.is_private" icon="mdi-lock" size="x-small" color="warning" class="mr-2" />
      <router-link
        v-if="canIssueRead"
        :to="{
          name: '(업무) - 보기',
          params: { projId: issue.project.slug, issueId: issue.pk },
        }"
      >
        {{ issue.subject }}
      </router-link>
      <span v-else>
        {{ issue.subject }}
      </span>
    </CTableDataCell>

    <!-- 프로젝트 -->
    <CTableDataCell v-else-if="colKey === 'project' && !$route.params.projId">
      <router-link
        v-if="issue.project?.slug"
        :to="{ name: '(개요)', params: { projId: issue.project.slug } }"
      >
        {{ issue.project.name }}
      </router-link>
      <span v-else>{{ issue.project?.name }}</span>
    </CTableDataCell>

    <!-- 상위업무 -->
    <CTableDataCell v-else-if="colKey === 'parent'" class="text-left truncate">
      <span v-if="issue?.parent?.pk">
        <v-icon
          v-if="issue?.parent?.is_private"
          icon="mdi-lock"
          size="x-small"
          color="warning"
          class="mr-2"
        />
        <router-link
          v-if="canIssueRead"
          :to="{
            name: '(업무) - 보기',
            params: { projId: issue.project.slug, issueId: issue?.parent?.pk },
          }"
        >
          {{ cutString(issue?.parent?.subject, 16) }}
        </router-link>
        <span v-else>
          {{ cutString(issue?.parent?.subject, 16) }}
        </span>
      </span>
    </CTableDataCell>

    <!-- 유형 -->
    <CTableDataCell v-else-if="colKey === 'tracker'">{{ issue.tracker.name }}</CTableDataCell>

    <!-- 상태 -->
    <CTableDataCell
      v-else-if="colKey === 'status'"
      :class="{
        'text-danger': issue.status.pk === 1,
        'text-success': issue.status.pk === 3,
        'text-warning': issue.status.pk === 4,
      }"
    >
      {{ issue.status.name }}
    </CTableDataCell>

    <!-- 우선순위 -->
    <CTableDataCell
      v-else-if="colKey === 'priority'"
      :class="{
        'text-grey': issue.priority.pk === 1,
        'text-warning': issue.priority.pk === 3,
        'text-danger': [4, 5].includes(issue.priority.pk),
        bold: issue.priority.pk === 5,
      }"
    >
      {{ issue.priority.name }}
    </CTableDataCell>

    <!-- 범주 -->
    <CTableDataCell v-else-if="colKey === 'category'"></CTableDataCell>

    <!-- 목표버전 -->
    <CTableDataCell v-else-if="colKey === 'fixed_version'" class="text-left">
      <router-link
        v-if="issue.fixed_version && issue.project?.slug"
        :to="{
          name: '(로드맵) - 보기',
          params: { projId: issue.project.slug, verId: issue.fixed_version.pk },
        }"
      >
        {{ issue.fixed_version.name }}
      </router-link>
      <span v-else-if="issue.fixed_version">{{ issue.fixed_version.name }}</span>
    </CTableDataCell>

    <!-- 담당자 -->
    <CTableDataCell v-else-if="colKey === 'assigned_to'" class="text-center">
      <template v-if="issue.assigned_to">
        <router-link
          v-if="canViewUser(issue.assigned_to.pk)"
          :to="{ name: '사용자 - 보기', params: { userId: issue.assigned_to.pk } }"
        >
          {{ issue.assigned_to.username }}
        </router-link>
        <span v-else>{{ issue.assigned_to.username }}</span>
      </template>
    </CTableDataCell>

    <!-- 업무관람자 -->
    <CTableDataCell v-else-if="colKey === 'watchers'"></CTableDataCell>

    <!-- 공개여부 -->
    <CTableDataCell v-else-if="colKey === 'is_private'"></CTableDataCell>

    <!-- 예상 처리기간 -->
    <CTableDataCell v-else-if="colKey === 'expected_duration'"></CTableDataCell>

    <!-- 시작일 -->
    <CTableDataCell v-else-if="colKey === 'start_date'"></CTableDataCell>

    <!-- 완료기한 -->
    <CTableDataCell v-else-if="colKey === 'due_date'"></CTableDataCell>

    <!-- 진척도 -->
    <CTableDataCell v-else-if="colKey === 'done_ratio'"></CTableDataCell>

    <!-- 관련 회의 -->
    <CTableDataCell v-else-if="colKey === 'meeting'"></CTableDataCell>

    <!-- 하위업무 -->
    <CTableDataCell v-else-if="colKey === 'sub_issues'"></CTableDataCell>

    <!-- 연결된 업무 -->
    <CTableDataCell v-else-if="colKey === 'rel_issues'"></CTableDataCell>

    <!-- 등록자 -->
    <CTableDataCell v-else-if="colKey === 'creator'"></CTableDataCell>

    <!-- 등록일 -->
    <CTableDataCell v-else-if="colKey === 'created'"></CTableDataCell>

    <!-- 최근 수정자 -->
    <CTableDataCell v-else-if="colKey === 'updater'"></CTableDataCell>

    <!-- 변경일 -->
    <CTableDataCell v-else-if="colKey === 'updated'" class="text-center">
      {{ timeFormat(issue.updated) }}
    </CTableDataCell>
  </template>

  <CTableDataCell class="p-0">
    <IssueDropDown :issue="issue" :is-delete="true" />
  </CTableDataCell>
</template>
