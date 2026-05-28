<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { elapsedTime, timeFormat } from '@/utils/baseMixins'

defineProps({ timeEntry: { type: Object, default: () => null } })

const router = useRouter()
</script>

<template>
  <CRow>
    <CCol>
      <CRow>
        <CCol v-if="timeEntry.user">
          <router-link :to="{ name: '사용자 - 보기', params: { userId: timeEntry.user.pk } }">
            {{ timeEntry.user.username }}
          </router-link>
          이(가)
          <span>
            <router-link
              :to="{
                name: '(실행기록)',
                params: { projId: 'redmine' },
                query: { from: timeEntry.created.substring(0, 10) },
              }"
            >
              {{ elapsedTime(timeEntry.created) }}
            </router-link>
            <v-tooltip activator="parent" location="top">{{
              timeFormat(timeEntry.created)
            }}</v-tooltip>
          </span>
          에 추가함
        </CCol>
        <CCol class="text-right pr-3">
          <span>
            <v-icon
              icon="mdi-pencil"
              color="amber"
              class="mr-2 pointer"
              size="18"
              @click="
                router.push({
                  name: '(소요시간) - 편집',
                  params: { projId: timeEntry.issue.project.slug, timeId: timeEntry.pk },
                })
              "
            />
            <v-tooltip activator="parent" location="top">편집</v-tooltip>
          </span>

          <span>
            <v-icon icon="mdi-trash-can" color="grey" size="18" class="pointer" />
            <v-tooltip activator="parent" location="top">삭제</v-tooltip>
          </span>
        </CCol>
      </CRow>
      <v-divider class="mt-0 mb-2" />
      <div class="history pl-4">
        <ul class="mb-2">
          <li>작업시간 : {{ timeEntry.hours }} 시간</li>
        </ul>
      </div>
      <div class="mb-3 fst-italic">{{ timeEntry.comment }}</div>
    </CCol>
  </CRow>
</template>
