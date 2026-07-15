<script lang="ts" setup>
import type { PropType } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'

defineProps({
  issuePk: { type: Number, required: true },
  relations: { type: Array as PropType<any[]>, default: () => [] },
})

const route = useRoute()
const { can, PERM } = usePerms()

const projId = route.params.projId as string
const routeName = projId ? '(업무)' : '업무'
const routeParams = projId ? { projId } : {}
</script>

<template>
  <span class="title mr-2">
    <router-link
      v-if="can(PERM.ISSUE_READ)"
      :to="{ name: routeName, params: routeParams, query: { issueId: issuePk } }"
    >
      {{ relations.length }}
    </router-link>
    <span v-else>{{ relations.length }}</span>
  </span>
  <span class="form-text">
    (<span v-if="relations.filter(i => !i.closed).length">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{ name: routeName, params: routeParams, query: { issueId: issuePk, status: 'open' } }"
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
          query: { issueId: issuePk, status: 'closed' },
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
