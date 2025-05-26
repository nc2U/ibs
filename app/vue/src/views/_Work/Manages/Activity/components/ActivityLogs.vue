<script lang="ts" setup>
import { useRoute } from 'vue-router'
import type { Prop, PropType } from 'vue'
import { bgLight } from '@/utils/cssMixins.ts'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import type { ActLogEntry } from '@/store/types/work_project.ts'
import { cutString, dateFormat, numberToHour, timeFormat } from '@/utils/baseMixins'

defineProps({
  groupedActivities: Object as PropType<{ [key: string]: ActLogEntry[] }>,
  default: () => {},
})

const getIcon = (sort: string, progress: boolean) => {
  if (sort === '1') return progress ? 'mdi-forward' : 'mdi-folder-plus'
  else if (sort === '2') return 'mdi-comment-text-multiple'
  else if (sort === '9') return 'mdi-folder-clock-outline'
  else return 'mdi-folder-plus'
}

const route = useRoute()
</script>

<template>
  <CRow v-for="(val, key) in groupedActivities" :key="key">
    <CCol>
      <CAlert class="px-3 py-1" :class="bgLight">
        <span class="date-title">
          {{ String(key) === dateFormat(new Date()) ? '오늘' : dateFormat(key as string, '/') }}
        </span>
      </CAlert>

      <CRow v-for="(act, i) in val" :key="act.pk" class="pl-3">
        <CCol :class="{ 'ml-5': i }">
          <v-icon
            :icon="getIcon(act.sort, !!act.status_log)"
            size="15"
            :color="act.sort === '1' && act.issue?.status.closed ? 'success' : 'brown-lighten-3'"
            class="mr-1"
          />
          <span class="form-text underline mr-2">{{ timeFormat(act.timestamp, true) }}</span>
          <span v-if="!route.params.projId || act.project?.slug !== route.params.projId">
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
            <div class="ml-4 pl-3 fst-italic">
              <VueMarkdownIt
                v-if="act.sort === '1' && !act.status_log"
                :source="cutString(act.issue?.description, 113)"
                class="form-text pl-4"
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

            <div class="ml-4 pl-3 fst-italic">
              <VueMarkdownIt
                v-if="act.sort === '2'"
                :source="cutString(act.comment?.content, 113)"
                class="form-text pl-4"
              />
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

            <div class="ml-4 pl-3 fst-italic">
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
