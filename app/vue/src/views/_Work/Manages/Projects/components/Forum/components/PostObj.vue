<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { Post } from '@/store/types/board'
import { timeFormat } from '@/utils/baseMixins'

defineProps({
  post: { type: Object as PropType<Post>, required: true },
})

const route = useRoute()
</script>

<template>
  <CTableDataCell class="text-center">{{ post.pk }}</CTableDataCell>
  <CTableDataCell class="text-left">
    <CBadge v-if="post.is_notice" color="warning" class="mr-2">공지</CBadge>
    <router-link
      :to="{
        name: '(게시판) - 게시물 보기',
        params: {
          projId: route.params.projId,
          brdId: route.params.brdId,
          postId: post.pk,
        },
      }"
    >
      {{ post.title }}
    </router-link>
    <CBadge v-if="post.is_new" color="success" class="ml-2" size="sm">new</CBadge>
    <span v-if="post.comments?.length" class="ml-2 text-grey">
      ({{ post.comments.length }})
    </span>
  </CTableDataCell>
  <CTableDataCell class="text-center">{{ post.creator?.username }}</CTableDataCell>
  <CTableDataCell class="text-center">{{ timeFormat(post.created as string) }}</CTableDataCell>
  <CTableDataCell class="text-center">{{ post.hit }}</CTableDataCell>
</template>
