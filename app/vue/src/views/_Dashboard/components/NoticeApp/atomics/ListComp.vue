<script lang="ts" setup>
import { type ComputedRef, inject, type PropType } from 'vue'
import type { Post } from '@/store/types/board.ts'
import type { User } from '@/store/types/accounts.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'

defineProps({
  mainViewName: { type: String, default: '공지 사항' },
  noticeList: { type: Array as PropType<Post[]>, default: () => [] },
  postList: { type: Array as PropType<Post[]>, default: () => [] },
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
            <tr v-for="item in noticeList" :key="item.pk ?? 0">
              <td class="pl-5">
                <v-badge
                  v-if="item.is_notice"
                  color="primary"
                  content="!"
                  offset-y="-7"
                  class="mr-4"
                />
                <router-link
                  v-if="!item.is_secret || userInfo?.is_superuser || userInfo?.pk === item.user?.pk"
                  :to="{ name: `${mainViewName} - 보기`, params: { postId: item.pk } }"
                >
                  {{ cutString(item.title, 32) }}
                </router-link>
                <span v-else class="text-grey">{{ cutString(item.title, 32) }}</span>
                <v-icon v-if="item.is_secret" icon="mdi-lock" size="sm" class="ml-2 text-grey" />
                <CBadge v-if="item.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
                <CBadge v-if="item.comments?.length" color="warning" size="sm" class="ml-1">
                  +{{ item.comments.length }}
                </CBadge>
              </td>
              <td class="text-right pr-4">{{ timeFormat(item.created ?? '').substring(0, 10) }}</td>
            </tr>
            <template v-for="(item, i) in postList" :key="item.pk ?? 0">
              <tr v-if="(noticeList.length ?? 0) + i <= 7">
                <td class="pl-5">
                  <router-link
                    v-if="
                      !item.is_secret || userInfo?.is_superuser || userInfo?.pk === item.user?.pk
                    "
                    :to="{ name: `${mainViewName} - 보기`, params: { postId: item.pk } }"
                  >
                    {{ cutString(item.title, 32) }}
                  </router-link>
                  <span v-else class="text-grey">{{ cutString(item.title, 32) }}</span>
                  <v-icon v-if="item.is_secret" icon="mdi-lock" size="sm" class="ml-2 text-grey" />
                  <CBadge v-if="item.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
                  <CBadge v-if="item.comments?.length" color="warning" size="sm" class="ml-1">
                    +{{ item.comments.length }}
                  </CBadge>
                </td>
                <td class="text-right pr-4">
                  {{ timeFormat(item.created ?? '').substring(0, 10) }}
                </td>
              </tr>
            </template>
          </tbody>
        </v-table>
      </v-card>
    </CCol>
  </CRow>
</template>
