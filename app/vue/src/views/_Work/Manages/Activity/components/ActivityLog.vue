<script lang="ts" setup>
import { inject, type PropType } from 'vue'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import { cutString, dateFormat, timeFormat } from '@/utils/baseMixins'
import { markdownRender } from '@/utils/helper.ts'

defineProps({
  activity: { type: Array as PropType<ActLogEntry[]>, required: true },
  date: { type: String, required: true },
})

const isDark = inject('isDark')

const getIcon = (sort: string, progress: boolean) => {
  if (sort === '1') return progress ? 'mdi-folder-check' : 'mdi-folder-edit'
  else if (sort === '2') return 'mdi-comment-text-multiple'
  else if (sort === '3') return 'mdi-account-group'
  else if (sort === '4') return 'mdi-message-badge'
  else if (sort === '5') return 'mdi-file-document'
  else if (sort === '6') return 'mdi-text-box-multiple'
  else return 'mdi-folder-plus'
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

      <CRow v-for="(act, i) in activity" :key="act.pk" class="pl-3">
        <CCol :class="{ 'ml-5': i > 0 && act.sort !== '3' && act.sort !== '2' }">
          <v-icon
            :icon="getIcon(act.sort, act.status_log === '종료')"
            size="15"
            :color="
              (act.sort === '1' && act.status_log === '종료') ||
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

          <span v-if="act.sort === '1'">
            <router-link
              :to="{
                name: '(업무) - 보기',
                params: { projId: act.project?.slug, issueId: act.issue?.pk },
              }"
            >
              [업무] {{ act.issue?.tracker }} #{{ act.issue?.pk }} ({{
                act.status_log || act.issue?.status.name
              }})
              {{ act.issue?.subject }}
            </router-link>
            <div class="ml-5 pl-4 fst-italic form-text">
              <div
                v-if="act.sort === '1' && !act.status_log"
                v-html="markdownRender(cutString(act.issue?.description, 113))"
                class="form-text"
              />
            </div>
            <div v-if="act.creator" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }">
                {{ act.creator.username }}
              </router-link>
            </div>
          </span>

          <span v-if="act.sort === '2'">
            <router-link
              :to="{
                name: '(업무) - 보기',
                params: { projId: act.project?.slug, issueId: act.issue?.pk },
                query: { tap: 2 },
                hash: `#note-${act.comment?.pk}`,
              }"
            >
              [의견] {{ act.issue?.tracker }} #{{ act.issue?.pk }}
              {{ act.issue?.subject }}
            </router-link>

            <div class="ml-5 pl-4 fst-italic">
              <div
                v-if="act.sort === '2'"
                v-html="markdownRender(cutString(act.comment?.content, 113))"
                class="form-text"
              />
            </div>
          </span>

          <span v-if="act.sort === '3'">
            <router-link
              :to="{
                name: act.project?.slug ? '(회의) - 보기' : '회의 - 보기',
                params: { projId: act.project?.slug, meetingId: act.meeting?.pk },
              }"
            >
              [회의록] #{{ act.meeting?.pk }} ({{ act.status_log || '등록' }})
              {{ act.meeting?.title }}
            </router-link>

            <div class="ml-5 pl-4 fst-italic">
              <div
                v-if="act.meeting?.agenda"
                v-html="markdownRender(cutString(act.meeting.agenda, 113))"
                class="form-text"
              />
            </div>

            <div v-if="act.creator" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }">
                {{ act.creator.username }}
              </router-link>
            </div>
          </span>

          <span v-if="act.sort === '4'">
            <router-link
              :to="{
                name: '(공지) - 보기',
                params: { projId: act.project?.slug, newsId: act.news?.pk },
              }"
            >
              [공지] {{ act.news?.title }}
            </router-link>

            <div class="ml-5 pl-4 fst-italic">
              <div
                v-if="act.news?.summary"
                v-html="markdownRender(cutString(act.news.summary, 113))"
                class="form-text"
              />
            </div>

            <div v-if="act.creator" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }">
                {{ act.creator.username }}
              </router-link>
            </div>
          </span>

          <span v-if="act.sort === '5'">
            <router-link
              :to="{
                name: '(문서) - 보기',
                params: { projId: act.project?.slug, docId: act.document?.pk },
              }"
            >
              [문서] {{ act.document?.title }}
            </router-link>

            <div class="ml-5 pl-4 fst-italic">
              <div
                v-if="act.document?.content"
                v-html="markdownRender(cutString(act.document.content, 113))"
                class="form-text"
              />
            </div>

            <div v-if="act.creator" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }">
                {{ act.creator.username }}
              </router-link>
            </div>
          </span>

          <span v-if="act.sort === '6'">
            <router-link
              :to="{
                name: '(게시판) - 게시물 보기',
                params: {
                  projId: act.project?.slug,
                  forumId: act.post?.forum,
                  postId: act.post?.pk,
                },
              }"
            >
              [게시물] {{ act.post?.title }}
            </router-link>

            <div class="ml-5 pl-4 fst-italic">
              <div
                v-if="act.post?.content"
                v-html="markdownRender(cutString(act.post.content, 113))"
                class="form-text"
              />
            </div>

            <div v-if="act.creator" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.creator.pk } }">
                {{ act.creator.username }}
              </router-link>
            </div>
          </span>

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
