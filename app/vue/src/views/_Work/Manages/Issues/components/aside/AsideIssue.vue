<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Issue } from '@/store/types/work_issue.ts'
import WatcherAdd from './WatcherAdd.vue'

const props = defineProps({
  watchers: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
  issue: { type: Object as PropType<Issue>, required: true },
})

const refWatcherAdd = ref()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const workManager = computed(() => accStore.workManager)

const route = useRoute()
const { can, PERM } = usePerms()

// 1. 관람자 추가 자격 조건 (책임자군이거나 watcher_create 권한 소유자)
const canAddWatcher = computed(() => {
  const currentUserId = userInfo.value?.pk
  if (!currentUserId) return false
  if (workManager.value) return true

  const isAssignee = props.issue.assigned_to?.pk === currentUserId
  const isCreator = props.issue.creator?.pk === currentUserId
  if (isAssignee || isCreator) return true

  return can(PERM.ISSUE_WATCHER_CREATE)
})

// 2. 관람자 삭제 자격 조건 (자기 자신이거나, 책임자군이거나, watcher_delete 권한 소유자)
const canDeleteWatcher = (watcherPk: number) => {
  const currentUserId = userInfo.value?.pk
  if (!currentUserId) return false
  if (workManager.value) return true

  if (watcherPk === currentUserId) return true

  const isAssignee = props.issue.assigned_to?.pk === currentUserId
  const isCreator = props.issue.creator?.pk === currentUserId
  if (isAssignee || isCreator) return true

  return can(PERM.ISSUE_WATCHER_DELETE)
}

const issueStore = useIssue()
const watcherAddSubmit = (payload: number[]) => {
  const form = new FormData()
  payload.forEach(val => form.append('watchers', val.toString()))
  issueStore.patchIssue(props.issue.pk, form)
}

const delWatcher = (pk: number) => {
  const form = new FormData()
  form.append('del_watcher', JSON.stringify(pk))
  issueStore.patchIssue(props.issue.pk, form)
}
</script>

<template>
  <template v-if="workManager && route.name === '(업무) - 보기'">
    <CRow class="mb-1">
      <CCol>
        <h6 class="asideTitle">업무 관람자 ({{ watchers.length }})</h6>
      </CCol>
      <CCol v-if="canAddWatcher" class="text-right">
        <router-link to="" @click="refWatcherAdd.callModal()">추가</router-link>
      </CCol>
    </CRow>
    <CRow v-for="watcher in watchers" :key="watcher.pk">
      <CCol class="col-xxl-5">
        <router-link :to="{ name: '사용자 - 보기', params: { userId: watcher.pk } }">
          {{ watcher.username }}
        </router-link>
        <span v-if="canDeleteWatcher(watcher.pk)" @click="delWatcher(watcher.pk)">
          <v-icon icon="mdi-trash-can-outline" size="sm" color="grey" class="ml-2 pointer" />
          <v-tooltip activator="parent" location="right">삭제</v-tooltip>
        </span>
      </CCol>
    </CRow>
  </template>

  <WatcherAdd ref="refWatcherAdd" :watchers="watchers" @watcher-add-submit="watcherAddSubmit" />
</template>

<style lang="scss" scoped>
.asideTitle {
  font-size: 1.1em;
}
</style>
