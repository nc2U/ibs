<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Post } from '@/store/types/forum'
import { useRoute } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'

defineProps({
  post: { type: Object as PropType<Post>, required: true },
})

const route = useRoute()

const { can, PERM } = usePerms()
const canForumRead = computed(() => can(PERM.FORUM_READ))
</script>

<template>
  <CTableDataCell class="text-center">{{ post.pk }}</CTableDataCell>
  <CTableDataCell class="text-left">
    <CBadge v-if="post.is_notice" color="primary" class="mr-2">공지</CBadge>
    <router-link
      v-if="canForumRead"
      :to="{
        name: '(게시판) - 게시물 보기',
        params: {
          projId: route.params.projId,
          forumId: route.params.forumId,
          postId: post.pk,
        },
      }"
    >
      {{ post.title }}
    </router-link>
    <span v-else>{{ post.title }}</span>
    <span v-if="post.comments?.length" class="ml-2 text-grey"> ({{ post.comments.length }}) </span>
    <CBadge v-if="post.is_new" color="success" class="ml-2" size="sm">new</CBadge>
  </CTableDataCell>
  <CTableDataCell class="text-center">{{ post.creator?.username }}</CTableDataCell>
  <CTableDataCell class="text-center">{{ timeFormat(post.created as string) }}</CTableDataCell>
  <CTableDataCell class="text-center">{{ post.hit }}</CTableDataCell>
</template>
