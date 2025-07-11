<script lang="ts" setup>
import type { PropType } from 'vue'
import { bgLight } from '@/utils/cssMixins.ts'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import { cutString, dateFormat, numberToHour, timeFormat } from '@/utils/baseMixins'
import { markdownRender } from '@/utils/helper.ts'

defineProps({
  activity: { type: Array as PropType<ActLogEntry[]>, required: true },
  date: { type: String, required: true },
})

const getIcon = (sort: string, progress: boolean) => {
  if (sort === '1') return progress ? 'mdi-folder-check' : 'mdi-folder-edit'
  else if (sort === '2') return 'mdi-comment-text-multiple'
  else if (sort === '3') return 'mdi-cog-outline'
  else if (sort === '4') return 'mdi-message-badge'
  else if (sort === '9') return 'mdi-folder-clock-outline'
  else return 'mdi-folder-plus'
}
</script>

<template>
  <CRow>
    <CCol>
      <CAlert class="px-3 py-1" :class="bgLight">
        <span class="date-title">
          {{ String(date) === dateFormat(new Date()) ? '오늘' : dateFormat(date as string, '/') }}
        </span>
      </CAlert>

      <CRow v-for="(act, i) in activity" :key="act.pk" class="pl-3">
        <CCol :class="{ 'ml-5': i > 0 && act.sort !== '3' }">
          <v-icon
            :icon="getIcon(act.sort, act.status_log === '종료')"
            size="15"
            :color="act.sort === '1' && act.status_log === '종료' ? 'success' : 'brown-lighten-3'"
            class="mr-1"
          />
          <span class="form-text underline mr-2">{{ timeFormat(act.timestamp, true) }}</span>

          <span v-if="!$route.params.projId || act.project?.slug !== $route.params.projId">
            {{ act.project?.name }} -
          </span>

          <span v-if="act.sort === '1'">
            <router-link
              :to="{
                name: '(업무) - 보기',
                params: { projId: act.project?.slug, issueId: act.issue?.pk },
              }"
            >
              {{ act.issue?.tracker }} #{{ act.issue?.pk }} ({{
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
            <div v-if="act.user" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.user.pk } }">
                {{ act.user.username }}
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
              {{ act.issue?.tracker }} #{{ act.issue?.pk }}
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
                name: '(저장소) - 리비전 보기',
                params: {
                  projId: act.project.slug,
                  repoId: act.change_set.repo.pk,
                  sha: act.change_set.sha,
                },
              }"
            >
              리비전 {{ act.change_set.sha.substring(0, 8) }} ({{ act.change_set.repo.slug }})
              {{ cutString(act.change_set.message, 50) }}
            </router-link>
            <div class="form-text ml-5 pl-3">
              {{ act.user.username }}
            </div>
          </span>

          <span v-if="act.sort === '4'">
            <router-link to="">{{ act.news?.title }}</router-link>

            <div class="ml-5 pl-2 fst-italic">{{ act.news?.summary }}</div>

            <div v-if="act.user" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.user.pk } }">
                {{ act.user.username }}
              </router-link>
            </div>
          </span>

          <span v-if="act.sort === '9'">
            <router-link
              :to="{
                name: '(소요시간)',
                params: { projId: act.project?.slug, issueId: act.issue?.pk },
                query: { issue: act.issue?.pk },
              }"
            >
              {{ numberToHour(act.spent_time?.hours ?? 0) }} 시간 ({{ act.issue?.tracker }} #{{
                act.issue?.pk
              }}
              ({{ act.status_log || act.issue?.status.name }}) {{ act.issue?.subject }})
            </router-link>

            <div class="ml-4 pl-3 fst-italic form-text">
              <span v-if="act.sort === '9' && act.spent_time?.comment" class="pl-3">
                {{ cutString(act.spent_time.comment, 100) }}
              </span>
            </div>
            <div v-if="act.user" class="form-text ml-5 pl-2">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: act.user.pk } }">
                {{ act.user.username }}
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
