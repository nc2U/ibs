<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Issue } from '@/store/types/work_issue.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import IssueDropDown from './IssueDropDown.vue'

defineProps({ issue: { type: Object as PropType<Issue>, required: true } })

const emit = defineEmits(['watch-control'])
</script>

<template>
  <CTableDataCell>
    <router-link
      :to="{
        name: '(업무) - 보기',
        params: { projId: issue.project.slug, issueId: issue.pk },
      }"
    >
      {{ issue.pk }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell v-if="!$route.params.projId">
    <router-link :to="{ name: '(개요)', params: { projId: issue.project.slug } }">
      {{ issue.project.name }}
    </router-link>
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
  <CTableDataCell class="text-left">
    <router-link
      :to="{
        name: '(업무) - 보기',
        params: { projId: issue.project.slug, issueId: issue.pk },
      }"
    >
      {{ issue.subject }}
    </router-link>
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
