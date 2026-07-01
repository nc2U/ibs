<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useForum } from '@/store/pinia/forum'
import { useRoute } from 'vue-router'
import type { Comment } from '@/store/types/forum'
import CommentList from './CommentList.vue'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  postId: { type: Number, required: true },
  forumId: { type: Number, required: true },
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const route = useRoute()
const projId = computed(() => route.params.projId as string)

const frmStore = useForum()

const onSubmitComment = (payload: any) => {
  const data = typeof payload === 'string' ? { content: payload } : payload
  if (data.pk) frmStore.patchComment(data)
  else frmStore.createComment({ ...data, post: props.postId }, projId.value)
}

const onDeleteComment = (pk: number) => {
  if (confirm('이 댓글을 삭제하시겠습니까?')) {
    frmStore.deleteComment({ pk, post: props.postId }, projId.value)
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
