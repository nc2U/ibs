<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Issue } from '@/store/types/work_issue.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import IssueDropDown from './IssueDropDown.vue'

const props = defineProps({ issue: { type: Object as PropType<Issue>, required: true } })

const emit = defineEmits(['watch-control'])

const { can, PERM } = usePerms()
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
      {{ issue.pk }}
    </router-link>
    <span v-else>{{ issue.pk }}</span>
  </CTableDataCell>
  <CTableDataCell v-if="!$route.params.projId">
    <router-link
      v-if="issue.project?.slug"
      :to="{ name: '(개요)', params: { projId: issue.project.slug } }"
    >
      {{ issue.project.name }}
    </router-link>
    <span v-else>{{ issue.project?.name }}</span>
  </CTableDataCell>
  <CTableDataCell>{{ issue.tracker.name }}</CTableDataCell>
  <CTableDataCell
    :class="{
      'text-danger': issue.status.pk === 1,
      'text-success': issue.status.pk === 3,
      'text-warning': issue.status.pk === 4,
    }"
  >
    {{ issue.status.name }}
  </CTableDataCell>
  <CTableDataCell
    :class="{
      'text-grey': issue.priority.pk === 1,
      'text-warning': issue.priority.pk === 3,
      'text-danger': [4, 5].includes(issue.priority.pk),
      bold: issue.priority.pk === 5,
    }"
  >
    {{ issue.priority.name }}
  </CTableDataCell>
  <CTableDataCell>
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
  <CTableDataCell class="text-left">
    <router-link
      v-if="canIssueRead"
      :to="{
        name: '(업무) - 보기',
        params: { projId: issue.project.slug, issueId: issue.pk },
      }"
    >
      {{ issue.subject }}
    </router-link>
    <span v-else>{{ issue.subject }}</span>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <router-link
      v-if="issue.assigned_to"
      :to="{ name: '사용자 - 보기', params: { userId: issue.assigned_to?.pk } }"
    >
      {{ issue.assigned_to?.username }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell class="text-center">{{ timeFormat(issue.updated) }}</CTableDataCell>
  <CTableDataCell class="p-0">
    <IssueDropDown :issue="issue" @watch-control="emit('watch-control', $event)" />
  </CTableDataCell>
</template>
