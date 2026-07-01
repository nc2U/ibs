<script lang="ts" setup>
import { ref, type PropType, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useForum } from '@/store/pinia/forum'
import type { Comment } from '@/store/types/forum'
import CommentList from './components/CommentList.vue'
import CommentForm from './components/CommentForm.vue'

const props = defineProps({
  post: { type: Number, required: true },
  isHide: { type: Boolean, default: false },
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const formVision = ref<boolean>(true)
const actForm = ref<number | undefined>(undefined)

const route = useRoute()
const projId = computed(() => route.params.projId as string)

const forumStore = useForum()
const createComment = (payload: Comment, projId: string = '') =>
  forumStore.createComment(payload, projId)
const patchComment = (payload: Comment, projId: string = '') =>
  forumStore.patchComment(payload, projId)
const patchCommentLike = (pk: number, post: number, page?: number) =>
  forumStore.patchCommentLike(pk, post, page)

const toLike = (pk: number) => patchCommentLike(pk, props.post)

const onSubmit = (payload: Comment) => {
  if (!payload?.pk) createComment(payload, projId.value)
  else patchComment(payload, projId.value)
}

const formReset = () => {
  formVision.value = true
  actForm.value = undefined
}

const visionToggle = (payload: { num: number; sts: boolean }) => {
  formVision.value = payload.sts
  if (!payload.sts) actForm.value = payload.num
}

const pageSelect = (page: number) => forumStore.fetchCommentList({ post: props.post, page })

const onDelete = (pk: number, post: number) => {
  forumStore.deleteComment({ pk, post }, projId.value)
}
</script>

<template>
  <div v-show="!isHide" class="border rounded">
    <CommentList
      :act-form="actForm"
      :comments="comments"
      @vision-toggle="visionToggle"
      @to-like="toLike"
      @on-submit="onSubmit"
      @on-delete="onDelete"
      @form-reset="formReset"
      @page-select="pageSelect"
    />
    <div v-show="formVision" :class="{ 'border-top': comments.length }">
      <CommentForm :form-vision="formVision" :post="post" @on-submit="onSubmit" />
    </div>
  </div>
</template>
