<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import { cutString, dateFormat, timeFormat } from '@/utils/baseMixins'
import { markdownRender } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'

const props = defineProps({
  activity: { type: Array as PropType<ActLogEntry[]>, required: true },
  date: { type: String, required: true },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const { canViewUser } = usePerms()

const getEventGroupKey = (act: ActLogEntry): string => {
  if (act.sort === '1') {
    return `issue-${act.target_id}`
  } else if (act.sort === '2') {
    return `issue-${act.parent_id || act.target_id}`
  } else if (act.sort === '3') {
    return `meeting-${act.target_id}`
  } else if (act.sort === '4') {
    return `news-${act.target_id}`
  } else if (act.sort === '5') {
    return `doc-${act.target_id}`
  } else if (act.sort === '6') {
    return `post-${act.target_id}`
  }
  return `unknown-${act.pk}`
}

const sortedActivityEvents = computed(() => {
  const events = [...props.activity]
  const eventsByGroup = new Map<string, ActLogEntry[]>()

  for (const event of events) {
    const key = getEventGroupKey(event)
    if (!eventsByGroup.has(key)) {
      eventsByGroup.set(key, [])
    }
    eventsByGroup.get(key)!.push(event)
  }

  const sorted: { act: ActLogEntry; inGroup: boolean }[] = []

  const sortedByTime = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  )

  for (const event of sortedByTime) {
    const key = getEventGroupKey(event)
    const groupEvents = eventsByGroup.get(key)
    if (groupEvents) {
      eventsByGroup.delete(key)
      groupEvents.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      )
      groupEvents.forEach((e, idx) => {
        sorted.push({
          act: e,
          inGroup: idx > 0,
        })
      })
    }
  }

  return sorted
})

const getIcon = (sort: string, progress: boolean) => {
  if (sort === '1') return progress ? 'mdi-folder-check' : 'mdi-folder-edit'
  else if (sort === '2') return 'mdi-comment-text-multiple'
  else if (sort === '3') return 'mdi-account-group'
  else if (sort === '4') return 'mdi-message-badge'
  else if (sort === '5') return 'mdi-file-document'
  else if (sort === '6') return 'mdi-text-box-multiple'
  else return 'mdi-folder-plus'
}

const getTargetRoute = (act: ActLogEntry) => {
  if (!act.project?.slug || !act.target_id) return null
  if (act.sort === '1') {
    return { name: '(업무) - 보기', params: { projId: act.project.slug, issueId: act.target_id } }
  } else if (act.sort === '2') {
    if (!act.parent_id) return null
    return {
      name: '(업무) - 보기',
      params: { projId: act.project.slug, issueId: act.parent_id },
      query: { tap: 2 },
      hash: `#note-${act.target_id}`,
    }
  } else if (act.sort === '3') {
    return { name: '(회의) - 보기', params: { projId: act.project.slug, meetingId: act.target_id } }
  } else if (act.sort === '4') {
    return { name: '(공지) - 보기', params: { projId: act.project.slug, newsId: act.target_id } }
  } else if (act.sort === '5') {
    return { name: '(문서) - 보기', params: { projId: act.project.slug, docId: act.target_id } }
  } else if (act.sort === '6') {
    if (!act.parent_id) return null
    return {
      name: '(게시판) - 게시물 보기',
      params: { projId: act.project.slug, forumId: act.parent_id, postId: act.target_id },
    }
  }
  return null
}
</script>

<template>
  <CRow>
    <CCol>
      <CAlert class="px-3 py-1" :style="{ background: isDark ? '#2A2B36' : '#EBEDEF' }">
        <span class="date-title">
          {{ String(date) === dateFormat(new Date()) ? '오늘' : dateFormat(date as string, '/') }}
        </span>
      </CAlert>

      <CRow
        v-for="({ act, inGroup }, i) in sortedActivityEvents"
        :key="act.pk"
        class="pl-3"
      >
        <CCol :class="{ 'ml-4': inGroup }">
          <v-icon
            v-if="inGroup"
            icon="mdi-subdirectory-arrow-right"
            size="13"
            class="mr-1 text-medium-emphasis"
          />
          <v-icon
            :icon="getIcon(act.sort, act.status_log === '종료' || act.status_log === '완료')"
            size="15"
            :color="
              (act.sort === '1' && (act.status_log === '완료' || act.status_log === '종료')) ||
              (act.sort === '3' && act.status_log === '완료됨')
                ? 'success'
                : 'brown-lighten-3'
            "
            class="mr-1"
          />
          <span class="form-text underline mr-2">{{ timeFormat(act.timestamp, 'short') }}</span>

          <span v-if="!$route.params.projId || act.project?.slug !== $route.params.projId">
            {{ act.project?.name || '회사 본사' }} -
          </span>

          <router-link v-if="getTargetRoute(act)" :to="getTargetRoute(act)!">
            {{ act.title || act.summary || '(제목 없음)' }}
          </router-link>
          <span v-else>{{ act.title || act.summary || '(제목 없음)' }}</span>

          <div v-if="act.summary" class="ml-5 pl-4 fst-italic form-text">
            <div v-html="markdownRender(cutString(act.summary, 113))" class="form-text" />
          </div>

          <div v-if="act.creator" class="form-text ml-5 pl-2">
            <router-link
              v-if="canViewUser(act.creator.pk)"
              :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }"
            >
              {{ act.creator.username }}
            </router-link>
            <span v-else>{{ act.creator.username }}</span>
          </div>

          <v-divider class="my-2" />
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.date-title {
  font-size: 1.1em;
  font-weight: bold;
}
</style>
