<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Comment } from '@/store/types/forum'
import CommentItem from './CommentItem.vue'

defineProps({
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const emit = defineEmits(['submit-comment', 'delete-comment'])
</script>

<template>
  <div class="comment-list">
    <CommentItem
      v-for="cmt in comments"
      :key="cmt.pk"
      :comment="cmt"
      @submit-comment="emit('submit-comment', $event)"
      @delete-comment="emit('delete-comment', $event)"
    />
  </div>
</template>
