<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useBoard } from '@/store/pinia/board'
import type { Comment } from '@/store/types/board'
import CommentList from './CommentList.vue'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  postId: { type: Number, required: true },
  brdId: { type: Number, required: true },
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const brdStore = useBoard()

const onSubmitComment = (payload: any) => {
  if (payload.pk) brdStore.patchComment(payload)
  else brdStore.createComment({ ...payload, post: { pk: props.postId, board: props.brdId } })
}

const onDeleteComment = (pk: number) => {
  if (confirm('이 댓글을 삭제하시겠습니까?')) {
    brdStore.deleteComment({ pk, post: props.postId })
  }
}
</script>

<template>
  <div class="comment-section mt-5">
    <h6>댓글 ({{ comments.length }})</h6>
    <v-divider class="mb-4" />

    <CommentList
      :comments="comments"
      @submit-comment="onSubmitComment"
      @delete-comment="onDeleteComment"
    />

    <div class="mt-4">
      <h6>댓글 작성</h6>
      <CommentForm @submit-comment="onSubmitComment" />
    </div>
  </div>
</template>
