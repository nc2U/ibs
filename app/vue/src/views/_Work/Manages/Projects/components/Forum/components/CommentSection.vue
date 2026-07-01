<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useForum } from '@/store/pinia/forum'
import { useRoute } from 'vue-router'
import type { Comment } from '@/store/types/forum'
import CommentList from './CommentList.vue'
import CommentForm from './CommentForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  postId: { type: Number, required: true },
  forumId: { type: Number, required: true },
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const deleteCommentConfirm = ref()

const route = useRoute()
const projId = computed(() => route.params.projId as string)

const frmStore = useForum()

const onSubmitComment = (payload: any) => {
  const data = typeof payload === 'string' ? { content: payload } : payload
  if (data.pk) frmStore.patchComment(data, projId.value)
  else frmStore.createComment({ ...data, post: props.postId }, projId.value)
}

const onDeleteComment = (pk: number) => {
  delPk.value = pk
  deleteCommentConfirm.value.callModal()
}
const delPk = ref<null | number>(null)
const delConfirm = () => {
  frmStore.deleteComment({ pk: delPk.value as number, post: props.postId }, projId.value)
  deleteCommentConfirm.value.close()
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

  <ConfirmModal ref="deleteCommentConfirm">
    이 댓글을 삭제하시겠습니까?
    <template #footer>
      <v-btn color="warning" size="small" @click="delConfirm">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
