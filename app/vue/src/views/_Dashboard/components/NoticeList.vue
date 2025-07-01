<script lang="ts" setup>
import { type ComputedRef, inject, type PropType } from 'vue'
import type { User } from '@/store/types/accounts.ts'
import type { News } from '@/store/types/work_inform.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'

defineProps({
  newsList: { type: Array as PropType<News[]>, default: () => [] },
})
</script>

<template>
  <CRow>
    <CCol md="12">
      <v-card class="mx-auto mb-4">
        <v-table hover>
          <col style="width: 23%" />
          <col style="width: 57%" />
          <col style="width: 20%" />
          <thead>
            <tr class="bg-secondary">
              <th class="text-left" colspan="2">
                <v-btn variant="text" icon="mdi-menu" />
                <span class="text-capitalize">공지</span>
              </th>
              <th class="text-right">
                <router-link :to="{ name: '공지' }">더보기</router-link>
                <v-icon icon="mdi-chevron-right" />
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in newsList" :key="item.pk ?? 0">
              <td class="pl-5">
                <span class="mr-3 strong">
                  <router-link :to="{ name: '(개요)', params: { projId: item.project?.slug } }">
                    {{ item.project?.name }}
                  </router-link>
                </span>
              </td>
              <td>
                <span class="text-grey">
                  <router-link
                    :to="{
                      name: '(공지) - 보기',
                      params: { projId: item.project?.slug, newsId: item.pk },
                    }"
                  >
                    {{ cutString(item.title, 32) }}
                  </router-link>
                </span>
                <CBadge v-if="item.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
                <CBadge v-if="item.comments?.length" color="warning" size="sm" class="ml-1">
                  +{{ item.comments.length }}
                </CBadge>
              </td>
              <td class="text-right pr-4">{{ timeFormat(item.created ?? '').substring(0, 10) }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </CCol>
  </CRow>
</template>
