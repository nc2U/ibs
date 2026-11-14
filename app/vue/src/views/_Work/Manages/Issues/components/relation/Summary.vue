<script lang="ts" setup>
import type { PropType } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import type { SubIssue } from '@/store/types/work_issue'

const props = defineProps({
  issuePk: { type: Number, required: true },
  relations: { type: Array as PropType<SubIssue[]>, default: () => [] },
  hasOutgoing: { type: Boolean, default: true },
  hasIncoming: { type: Boolean, default: false },
})

const route = useRoute()
const { can, PERM } = usePerms()

const projId = route.params.projId as string
const routeName = projId ? '(업무)' : '업무'
const routeParams = projId ? { projId } : {}
const relQueryKey = !props.hasOutgoing && props.hasIncoming ? 'follows_issue' : 'precedes_issue'
</script>

<template>
  <span class="title me-2">
    <router-link
      v-if="can(PERM.ISSUE_READ)"
      :to="{ name: routeName, params: routeParams, query: { [relQueryKey]: issuePk } }"
    >
      {{ relations.length }}
    </router-link>
    <span v-else>{{ relations.length }}</span>
  </span>
  <span class="form-text">
    (<span v-if="relations.filter(i => !i.closed).length">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{
          name: routeName,
          params: routeParams,
          query: { [relQueryKey]: issuePk, status: 'open' },
        }"
      >
        {{ relations.filter(i => !i.closed).length }} 건 진행 중
      </router-link>
      <span v-else>{{ relations.filter(i => !i.closed).length }} 건 진행 중</span>
    </span>
    <span v-else>모두 완료</span>
    -
    <span v-if="relations.filter(i => i.closed).length">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{
          name: routeName,
          params: routeParams,
          query: { [relQueryKey]: issuePk, status: 'closed' },
        }"
      >
        {{ relations.filter(i => i.closed).length }} 건 완료
      </router-link>
      <span v-else>{{ relations.filter(i => i.closed).length }} 건 완료</span>
    </span>
    <span v-else>모두 미완료</span>)
  </span>
</template>

<style lang="scss" scoped>
.title {
  font-weight: bold;
}
</style>
