<script setup lang="ts">
import { type PropType } from 'vue'
import type { Post } from '@/store/types/forum'
import { cutString, timeFormat } from '@/utils/baseMixins'

defineProps({
  post: { type: Object as PropType<Post>, default: null },
})
</script>

<template>
  <CTableRow v-if="post" class="text-center">
    <CTableDataCell>{{ post.pk }}</CTableDataCell>
    <CTableDataCell>
      <router-link :to="{ name: post.forum_name || '공지 사항' }" target="_blank">
        {{ post.board_name }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link
        :to="{ name: `${post.board_name || '공지 사항'} - 보기`, params: { postId: post.pk } }"
        target="_blank"
      >
        {{ cutString(post.title, 50) }}
      </router-link>
      <CBadge v-if="post.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ timeFormat(post.created ?? '') }}</CTableDataCell>
  </CTableRow>
</template>
