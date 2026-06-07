<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { timeFormat } from '@/utils/baseMixins'
import type { Forum, Comment as Cm } from '@/store/types/forum'

const props = defineProps({
  forumList: { type: Array as PropType<Forum[]>, default: () => [] },
  comment: { type: Object as PropType<Cm>, default: null },
})

const viewRoute = computed(() => {
  const forum = props.forumList.filter(b => b.pk === props.comment?.post?.forum)[0]

  return forum && forum.name ? forum.name : '공지 사항'
})
</script>

<template>
  <CTableRow class="text-50 text-center" :id="`comment_${comment.pk}`">
    <CTableDataCell>{{ comment.pk }}</CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link
        :to="{ name: `${viewRoute} - 보기`, params: { postId: comment.post.pk } }"
        target="_blank"
      >
        {{ comment.content }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ timeFormat(comment.created as string) }}</CTableDataCell>
  </CTableRow>
</template>
