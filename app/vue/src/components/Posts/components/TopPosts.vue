<script setup lang="ts">
import { type ComputedRef, inject, type PropType } from 'vue'
import type { Post } from '@/store/types/board'
import type { User } from '@/store/types/accounts'
import { cutString, timeFormat } from '@/utils/baseMixins'

defineProps({
  post: { type: Object as PropType<Post>, default: null },
  viewRoute: { type: String, required: true },
  isLawsuit: { type: Boolean, default: false },
})

const userInfo = inject<ComputedRef<User>>('userInfo')
</script>

<template>
  <CTableRow v-if="post" class="text-center">
    <CTableDataCell>
      <v-badge color="primary" content=" 공지 " offset-x="5" offset-y="-7" />
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link
        v-if="!post.is_secret || userInfo?.is_superuser || userInfo?.pk === post.creator?.pk"
        :to="{ name: `${viewRoute} - 보기`, params: { postId: post.pk } }"
      >
        {{ cutString(post.title, 32) }}
      </router-link>
      <span v-else class="text-grey">{{ cutString(post.title, 32) }}</span>
      <v-icon v-if="post.is_secret" icon="mdi-lock" size="sm" class="ml-2 text-grey" />
      <CBadge v-if="post.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
      <CBadge v-if="post.comments?.length" color="warning" size="sm" class="ml-1">
        +{{ post.comments.length }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ post.creator?.username }}</CTableDataCell>
    <CTableDataCell>{{ timeFormat(post.created ?? '') }}</CTableDataCell>
    <CTableDataCell>{{ post.hit }}</CTableDataCell>
  </CTableRow>
</template>
