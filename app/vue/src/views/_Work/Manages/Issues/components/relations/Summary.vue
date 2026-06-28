<script lang="ts" setup>
import type { PropType } from 'vue'
import type { SubIssue } from '@/store/types/work_issue.ts'
import { usePerms } from '@/composables/usePerms.ts'

defineProps({
  issuePk: { type: Number, required: true },
  relIssueTos: { type: Array as PropType<SubIssue[]>, default: () => [] },
})

const { can, PERM } = usePerms()
</script>

<template>
  <span class="title mr-2">
    <router-link
      v-if="can(PERM.ISSUE_READ)"
      :to="{ name: '(업무)', query: { issueId: issuePk } }"
    >
      {{ relIssueTos.length }}
    </router-link>
    <span v-else>{{ relIssueTos.length }}</span>
  </span>
  <span class="form-text">
    (<span v-if="relIssueTos.filter(i => !i.closed).length">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{ name: '(업무)', query: { issueId: issuePk, status: 'open' } }"
      >
        {{ relIssueTos.filter(i => !i.closed).length }} 건 진행 중
      </router-link>
      <span v-else>{{ relIssueTos.filter(i => !i.closed).length }} 건 진행 중</span>
    </span>
    <span v-else>모두 완료</span>
    -
    <span v-if="relIssueTos.filter(i => i.closed).length">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{ name: '(업무)', query: { issueId: issuePk, status: 'closed' } }"
      >
        {{ relIssueTos.filter(i => i.closed).length }} 건 완료
      </router-link>
      <span v-else>{{ relIssueTos.filter(i => i.closed).length }} 건 완료</span>
    </span>
    <span v-else>모두 미완료</span>)
  </span>
</template>

<style lang="scss" scoped>
.title {
  font-weight: bold;
}
</style>
