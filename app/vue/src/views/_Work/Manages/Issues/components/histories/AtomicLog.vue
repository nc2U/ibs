<script lang="ts" setup="">
import { type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { IssueLogEntry } from '@/store/types/work_logging.ts'
import { elapsedTime, timeFormat } from '@/utils/baseMixins'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'

defineProps({ log: { type: Object as PropType<IssueLogEntry>, required: true } })

const getHistory = (h: string) => h.split('|').filter(str => str.trim() !== '')

const route = useRoute()
</script>

<template>
  <CRow>
    <CCol>
      <CRow
        :id="`note-${log.pk}`"
        :class="{ 'bg-blue-lighten-5': route.hash == `#note-${log.log_id}` }"
      >
        <CCol v-if="log.user">
          <router-link :to="{ name: '사용자 - 보기', params: { userId: log.user.pk } }">
            {{ log.user.username }}
          </router-link>
          이(가)
          <span>
            <router-link
              :to="{
                name: '(작업내역)',
                query: { from: log.timestamp.substring(0, 10) },
              }"
            >
              {{ elapsedTime(log.timestamp) }}
            </router-link>
            <v-tooltip activator="parent" location="top">{{ timeFormat(log.timestamp) }}</v-tooltip>
          </span>
          에 변경
        </CCol>
        <CCol class="text-right">
          <router-link :to="{ hash: '#note-' + log.log_id }">#{{ log.log_id }}</router-link>
        </CCol>
      </CRow>
      <v-divider class="mt-0 mb-2" />
      <div class="history pl-4">
        <ul class="ml-2">
          <li v-for="(src, i) in getHistory(log.details)" :key="i">
            <VueMarkdownIt :source="src" />
            <span v-if="log.diff && src.includes('**설명**')">
              <router-link to="">
                (변경 내용)
                <v-tooltip activator="parent" location="start">
                  <VueMarkdownIt :source="log.diff" />
                </v-tooltip>
              </router-link>
            </span>
          </li>
        </ul>
      </div>
    </CCol>
  </CRow>
</template>
