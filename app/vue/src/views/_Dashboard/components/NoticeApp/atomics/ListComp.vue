<script lang="ts" setup>
import { type ComputedRef, inject, type PropType } from 'vue'
import type { User } from '@/store/types/accounts.ts'
import type { News } from '@/store/types/work_inform.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'

defineProps({
  mainViewName: { type: String, default: '공지 사항' },
  newsList: { type: Array as PropType<News[]>, default: () => [] },
})

const userInfo = inject<ComputedRef<User>>('userInfo')
</script>

<template>
  <CRow>
    <CCol md="12">
      <v-card class="mx-auto mb-4">
        <v-table>
          <thead>
            <tr class="bg-secondary">
              <th class="text-left">
                <v-btn variant="text" icon="mdi-menu" />
                <span class="text-capitalize">{{ mainViewName }}</span>
              </th>
              <th class="text-right">
                <router-link :to="{ name: mainViewName }">더보기</router-link>
                <v-icon icon="mdi-chevron-right" />
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in newsList" :key="item.pk ?? 0">
              <td class="pl-5">
                <span class="text-grey">{{ cutString(item.title, 32) }}</span>
                <!--                <CBadge v-if="item.is_new" color="warning" size="sm" class="ml-2">new</CBadge>-->
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
