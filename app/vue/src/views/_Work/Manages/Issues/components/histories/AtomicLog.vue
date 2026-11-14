<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { IssueLogEntry } from '@/store/types/work_logging'
import { elapsedTime, timeFormat } from '@/utils/baseMixins'
import { markdownRender } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import { CCol, CRow } from '@coreui/vue'

defineProps({ log: { type: Object as PropType<IssueLogEntry>, required: true } })

const getHistory = (h: string) => h.split('|').filter(str => str.trim() !== '')

const route = useRoute()
const { canViewUser } = usePerms()
</script>

<template>
  <CRow>
    <CCol class="ps-0">
      <CRow
        :id="`note-${log.log_id}`"
        :class="{ 'bg-blue-lighten-5': route.hash == `#note-${log.log_id}` }"
      >
        <CCol v-if="log.creator" class="ms-2">
          <router-link
            v-if="canViewUser(log.creator.pk)"
            :to="{ name: '사용자 - 보기', params: { userId: log.creator.pk } }"
          >
            {{ log.creator.username }}
          </router-link>
          <span v-else>{{ log.creator.username }}</span>
          이(가)
          <span>
            <router-link
              :to="{
                name: route.params.projId || log.issue?.project?.slug ? '(업무실행내역)' : '업무실행내역',
                params:
                  route.params.projId || log.issue?.project?.slug
                    ? { projId: (route.params.projId as string) || log.issue?.project?.slug }
                    : {},
                query: { from: log.timestamp.substring(0, 10) },
              }"
            >
              {{ elapsedTime(log.timestamp) }}
            </router-link>
            <v-tooltip activator="parent" location="top">{{ timeFormat(log.timestamp) }}</v-tooltip>
          </span>
          에 변경
        </CCol>
        <CCol class="text-end">
          <router-link :to="{ hash: '#note-' + log.log_id }">#{{ log.log_id }}</router-link>
        </CCol>
      </CRow>
      <v-divider class="mt-1 mb-2" />
      <div class="history">
        <ul class="ms-0 ps-0">
          <li v-for="(src, i) in getHistory(log.details)" :key="i" class="list-item">
            <div v-html="markdownRender(src)" />
            <span v-if="log.diff && src.includes('**설명**')" class="ms-5">
              <a href="#" @click.prevent>
                (변경 내용)
                <v-tooltip activator="parent" location="start">
                  <span v-html="markdownRender(log.diff)" />
                </v-tooltip>
              </a>
            </span>
          </li>
        </ul>
      </div>
    </CCol>
  </CRow>
</template>
