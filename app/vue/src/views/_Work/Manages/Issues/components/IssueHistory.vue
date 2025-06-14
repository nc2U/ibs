<script setup lang="ts">
import { onBeforeMount, type PropType, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { TimeEntry } from '@/store/types/work_issue.ts'
import type { IssueLogEntry } from '@/store/types/work_logging.ts'
import AtomicLog from './histories/AtomicLog.vue'
import AtomicComment from './histories/AtomicComment.vue'
import AtomicTimeEntry from './histories/AtomicTimeEntry.vue'

defineProps({
  issueLogList: { type: Array as PropType<IssueLogEntry[]>, default: () => [] },
  timeEntryList: { type: Array as PropType<TimeEntry[]>, default: () => [] },
})

const tabPaneActiveKey = ref(1)

const emit = defineEmits(['del-submit', 'call-reply'])
const callReply = (payload: { id: number; user: string; content: string }) =>
  emit('call-reply', payload)
const delSubmit = (pk: number) => emit('del-submit', pk)

const route = useRoute()
onBeforeMount(() => {
  if (route.query.tap) tabPaneActiveKey.value = Number(route.query.tap)
})
</script>

<template>
  <CNav variant="tabs">
    <CNavItem>
      <CNavLink
        href="javascript:void(0);"
        :active="tabPaneActiveKey === 1"
        @click="tabPaneActiveKey = 1"
      >
        이력
      </CNavLink>
    </CNavItem>
    <CNavItem v-if="issueLogList.filter(l => l.comment).length">
      <CNavLink
        href="javascript:void(0);"
        :active="tabPaneActiveKey === 2"
        @click="tabPaneActiveKey = 2"
      >
        댓글
      </CNavLink>
    </CNavItem>
    <CNavItem v-if="issueLogList.filter(l => !l.comment).length">
      <CNavLink
        href="javascript:void(0);"
        :active="tabPaneActiveKey === 3"
        @click="tabPaneActiveKey = 3"
      >
        항목 변경이력
      </CNavLink>
    </CNavItem>
    <CNavItem v-if="timeEntryList.length">
      <CNavLink
        href="javascript:void(0);"
        :active="tabPaneActiveKey === 4"
        @click="tabPaneActiveKey = 4"
      >
        작업시간
      </CNavLink>
    </CNavItem>
  </CNav>

  <CCard
    v-if="issueLogList.length"
    class="border-top-0 p-2"
    :style="{ '--cui-card-border-radius': 0 }"
  >
    <CCardBody class="pb-0">
      <CTabContent>
        <CTabPane role="tabpanel" aria-labelledby="home-tab" :visible="tabPaneActiveKey === 1">
          <div v-for="log in issueLogList" :key="log.pk">
            <AtomicLog v-if="log.action === 'Updated' && !log.comment" :log="log" />
            <AtomicComment v-else :log="log" @call-reply="callReply" @del-submit="delSubmit" />
          </div>
        </CTabPane>

        <CTabPane role="tabpanel" aria-labelledby="profile-tab" :visible="tabPaneActiveKey === 2">
          <div v-for="log in issueLogList" :key="log.pk">
            <AtomicComment
              v-if="log.action === 'Comment' && log.comment"
              :log="log"
              @call-reply="callReply"
              @del-submit="delSubmit"
            />
          </div>
        </CTabPane>

        <CTabPane role="tabpanel" aria-labelledby="contact-tab" :visible="tabPaneActiveKey === 3">
          <div v-for="log in issueLogList" :key="log.pk">
            <AtomicLog v-if="log.action === 'Updated' && !log.comment" :log="log" />
          </div>
        </CTabPane>

        <CTabPane role="tabpanel" aria-labelledby="profile-tab" :visible="tabPaneActiveKey === 4">
          <div v-for="time in timeEntryList" :key="time.pk">
            <AtomicTimeEntry :time-entry="time" />
          </div>
        </CTabPane>
      </CTabContent>
    </CCardBody>
  </CCard>
</template>

<style lang="scss" scoped>
:deep(.history) {
  color: #7f7f7f;

  .vue-md-it-wrapper {
    float: left;
    margin-right: 1rem;

    blockquote {
      padding-left: 28px !important;
      border-left: 3px solid #ddd !important;
      font-style: italic !important;
    }
  }
}
</style>
