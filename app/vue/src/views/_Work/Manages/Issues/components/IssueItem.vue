<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { DEFAULT_ISSUE_COLUMNS } from '@/views/_Work/Manages/Issues/constants.ts'
import { cutString, dateFormat, timeFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Issue } from '@/store/types/work_issue.ts'
import IssueDropDown from './IssueDropDown.vue'

const props = defineProps({
  issue: { type: Object as PropType<Issue>, required: true },
  columns: { type: Array as PropType<string[]>, default: () => DEFAULT_ISSUE_COLUMNS },
})

const { can, canViewUser, PERM } = usePerms()
const canIssueRead = computed(() => can(PERM.ISSUE_READ) && props.issue.project?.slug)
const canMeetingRead = computed(() => can(PERM.MEETING_READ))

const priorityColor = computed(() => {
  let color = 'blue-grey-lighten-2'
  if (props.issue?.priority.pk === 2) color = 'cyan-accent-4'
  if (props.issue?.priority.pk === 3) color = 'deep-orange-lighten-1'
  if (props.issue?.priority.pk === 4) color = 'deep-orange-darken-4'
  if (props.issue?.priority.pk === 5) color = 'pink-darken-4'
  return color
})

const statusColor = computed(() => {
  let color = 'lime-accent-2'
  if (props.issue?.status.pk === 2) color = 'info'
  if (props.issue?.status.pk === 3) color = 'warning'
  if (props.issue?.status.pk === 4) color = 'grey'
  if (props.issue?.status.pk === 5) color = 'success'
  if (props.issue?.status.pk === 6) color = 'secondary'
  return color
})
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

    <!-- 우선순위 -->
    <CTableDataCell v-else-if="colKey === 'priority'">
      <v-chip size="x-small" :color="priorityColor" variant="flat" border>
        {{ issue.priority.name }}
      </v-chip>
    </CTableDataCell>

    <!-- 상태 -->
    <CTableDataCell v-else-if="colKey === 'status'" class="text-start">
      <v-chip size="x-small" :color="statusColor" variant="flat" border>
        {{ issue.status.name }}
      </v-chip>
    </CTableDataCell>

    <!-- 범주 -->
    <CTableDataCell v-else-if="colKey === 'category'"> {{ issue.category }} </CTableDataCell>

    <!-- 목표버전 -->
    <CTableDataCell v-else-if="colKey === 'fixed_version'">
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
    <CTableDataCell v-else-if="colKey === 'watchers'">
      <template v-for="(w, i) in issue.watchers" :key="w.pk">
        <router-link
          v-if="canViewUser(w.pk)"
          :to="{ name: '사용자 - 보기', params: { userId: w.pk } }"
        >
          {{ w.username }}
        </router-link>
        <span v-else>{{ w.username }}</span>
        <template v-if="i < issue.watchers.length - 1">, </template>
      </template>
    </CTableDataCell>

    <!-- 예상 처리기간 -->
    <CTableDataCell v-else-if="colKey === 'expected_duration'">
      {{ issue.expected_duration_display }}
    </CTableDataCell>

    <!-- 시작일 -->
    <CTableDataCell v-else-if="colKey === 'start_date'">
      {{ dateFormat(issue.start_date, '/') }}
    </CTableDataCell>

    <!-- 완료기한 -->
    <CTableDataCell v-else-if="colKey === 'due_date'">
      <span v-if="issue.due_date">{{ dateFormat(issue.due_date, '/') }}</span>
    </CTableDataCell>

    <!-- 진척도 -->
    <CTableDataCell v-else-if="colKey === 'done_ratio'">
      <CProgress
        :color="issue.done_ratio === 100 ? 'success' : 'warning'"
        :value="issue.done_ratio ?? 0"
        style="width: 110px; float: left; margin-top: 8px"
        height="8"
      />
    </CTableDataCell>

    <!-- 관련 회의 -->
    <CTableDataCell v-else-if="colKey === 'meeting'">
      <template v-if="issue.meeting_desc">
        <router-link
          v-if="canMeetingRead"
          :to="{ name: '(회의) - 보기', params: { meetingId: issue.meeting_desc.pk } }"
        >
          {{ issue.meeting_desc.title }}
        </router-link>
        <span v-else>{{ issue.meeting_desc.title }}</span>
      </template>
    </CTableDataCell>

    <!-- 하위업무 -->
    <CTableDataCell v-else-if="colKey === 'sub_issues'" class="text-left">
      <template v-if="issue.sub_issues?.length">
        <template v-for="(sub, i) in issue.sub_issues" :key="sub.pk">
          <router-link
            v-if="canIssueRead"
            :to="{
              name: '(업무) - 보기',
              params: { projId: issue.project.slug, issueId: sub.pk },
            }"
          >
            #{{ sub.pk }}
          </router-link>
          <span v-else>#{{ sub.pk }}</span>
          <template v-if="i < issue.sub_issues.length - 1">, </template>
        </template>
      </template>
    </CTableDataCell>

    <!-- 연결된 업무 -->
    <CTableDataCell v-else-if="colKey === 'rel_issues'" class="text-left">
      <div v-if="issue.incoming_relation?.issue" class="d-flex align-center ga-1 text-truncate">
        <v-chip size="x-small" color="info" variant="flat">선행</v-chip>
        <router-link
          v-if="canIssueRead"
          :to="{
            name: '(업무) - 보기',
            params: { projId: issue.project.slug, issueId: issue.incoming_relation.issue.pk },
          }"
        >
          #{{ issue.incoming_relation.issue.pk }} {{ issue.incoming_relation.issue.subject }}
        </router-link>
        <span v-else>
          #{{ issue.incoming_relation.issue.pk }} {{ issue.incoming_relation.issue.subject }}
        </span>
      </div>

      <template v-if="issue.outgoing_relations?.length">
        <div
          v-for="rel in issue.outgoing_relations"
          :key="rel.pk"
          class="d-flex align-center ga-1 text-truncate"
        >
          <v-chip size="x-small" color="secondary" variant="flat">후행</v-chip>
          <router-link
            v-if="rel.issue && canIssueRead"
            :to="{
              name: '(업무) - 보기',
              params: { projId: issue.project.slug, issueId: rel.issue.pk },
            }"
          >
            #{{ rel.issue.pk }} {{ rel.issue.subject }}
          </router-link>
          <span v-else-if="rel.issue"> #{{ rel.issue.pk }} {{ rel.issue.subject }} </span>
        </div>
      </template>
    </CTableDataCell>

    <!-- 등록자 -->
    <CTableDataCell v-else-if="colKey === 'creator'">
      <template v-if="issue.creator">
        <router-link
          v-if="canViewUser(issue.creator.pk)"
          :to="{ name: '사용자 - 보기', params: { userId: issue.creator.pk } }"
        >
          {{ issue.creator.username }}
        </router-link>
        <span v-else>{{ issue.creator.username }}</span>
      </template>
    </CTableDataCell>

    <!-- 등록 -->
    <CTableDataCell v-else-if="colKey === 'created'">
      {{ timeFormat(issue.created) }}
    </CTableDataCell>

    <!-- 최근 수정자 -->
    <CTableDataCell v-else-if="colKey === 'updater'">
      <template v-if="issue.updater">
        <router-link
          v-if="canViewUser(issue.updater.pk)"
          :to="{ name: '사용자 - 보기', params: { userId: issue.updater.pk } }"
        >
          {{ issue.updater.username }}
        </router-link>
        <span v-else>{{ issue.updater.username }}</span>
      </template>
    </CTableDataCell>

    <!-- 변경 -->
    <CTableDataCell v-else-if="colKey === 'updated'" class="text-center">
      {{ timeFormat(issue.updated) }}
    </CTableDataCell>
  </template>

  <CTableDataCell class="p-0">
    <IssueDropDown :issue="issue" :is-delete="true" />
  </CTableDataCell>
</template>
